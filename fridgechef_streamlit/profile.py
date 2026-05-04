"""
FridgeChef - Profile & Settings Feature
"""
import json
import csv
import io
import streamlit as st
from translations import t
from ui_helpers import render_section_title
from database import get_db, User, Profile, SavedRecipe, TrackerEntry
from auth import check_password, hash_password, logout_user


def render_profile_page():
    user_id = st.session_state.get("current_user_id")
    if not user_id:
        st.warning("Bitte einloggen.")
        return

    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not user:
            st.error("Benutzer nicht gefunden.")
            return
    finally:
        db.close()

    st.subheader(t("profile_title"))

    # ── Avatar ─────────────────────────────────────────────────
    initials = (user.display_name or user.email)[:2].upper()
    st.markdown(f"""
<div style="
  width: 80px; height: 80px; border-radius: 50%;
  background: #6B4226; color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; font-weight: bold; margin: 0 auto 16px;
">
  {initials}
</div>
""", unsafe_allow_html=True)

    # ── Tabs ───────────────────────────────────────────────────
    tab_acc, tab_pref, tab_appear, tab_export = st.tabs([
        "👤 Konto", "⚙️ Einstellungen", "🎨 Darstellung", "📦 Daten"
    ])

    with tab_acc:
        _render_account_tab(user, user_id)
    with tab_pref:
        _render_preferences_tab(profile, user_id)
    with tab_appear:
        _render_appearance_tab(profile, user_id)
    with tab_export:
        _render_export_tab(user_id)


def _render_account_tab(user, user_id: str):
    render_section_title("Kontodaten")

    with st.form("account_form"):
        new_name = st.text_input(t("name"), value=user.display_name or "")
        new_email = st.text_input(t("email"), value=user.email)
        submitted = st.form_submit_button(t("save"), use_container_width=True)
        if submitted:
            db = get_db()
            try:
                u = db.query(User).filter(User.id == user_id).first()
                if u:
                    u.display_name = new_name.strip()
                    u.email = new_email.strip().lower()
                    db.commit()
                    st.session_state.current_user_name = new_name.strip()
                    st.session_state.current_user_email = new_email.strip().lower()
                    st.success(t("profile_saved"))
            finally:
                db.close()

    st.divider()
    render_section_title(t("change_password"))
    with st.form("password_form"):
        cur_pw = st.text_input(t("current_password"), type="password")
        new_pw = st.text_input(t("new_password"), type="password")
        new_pw2 = st.text_input(t("password_confirm"), type="password")
        pw_submitted = st.form_submit_button(t("change_password"), use_container_width=True)
        if pw_submitted:
            db = get_db()
            try:
                u = db.query(User).filter(User.id == user_id).first()
                if not check_password(cur_pw, u.password_hash):
                    st.error(t("current_password") + " falsch.")
                elif new_pw != new_pw2:
                    st.error(t("passwords_mismatch"))
                elif len(new_pw) < 6:
                    st.error(t("password_too_short"))
                else:
                    u.password_hash = hash_password(new_pw)
                    db.commit()
                    st.success("Passwort geändert!")
            finally:
                db.close()

    st.divider()
    col_logout, col_del = st.columns(2)
    with col_logout:
        if st.button(t("logout"), use_container_width=True, type="primary"):
            logout_user()
            st.rerun()
    with col_del:
        if st.button(t("delete_account"), use_container_width=True):
            st.session_state.confirm_delete_account = True

    if st.session_state.get("confirm_delete_account"):
        st.error(t("confirm_delete_account"))
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⚠️ " + t("yes"), key="del_acc_yes", use_container_width=True):
                _delete_account(user_id)
                st.rerun()
        with c2:
            if st.button(t("no"), key="del_acc_no", use_container_width=True):
                st.session_state.confirm_delete_account = False
                st.rerun()


def _render_preferences_tab(profile, user_id: str):
    render_section_title(t("daily_goals"))
    with st.form("prefs_form"):
        col1, col2 = st.columns(2)
        with col1:
            cal_goal = st.number_input(
                t("daily_calories_goal"),
                min_value=500, max_value=5000, step=50,
                value=st.session_state.get("daily_calories", 2000),
            )
            prot_goal = st.number_input(
                t("daily_protein_goal"),
                min_value=10, max_value=500, step=5,
                value=st.session_state.get("daily_protein", 150),
            )
        with col2:
            fat_goal = st.number_input(
                t("daily_fat_goal"),
                min_value=10, max_value=300, step=5,
                value=st.session_state.get("daily_fat", 65),
            )
            carbs_goal = st.number_input(
                t("daily_carbs_goal"),
                min_value=10, max_value=600, step=10,
                value=st.session_state.get("daily_carbs", 250),
            )

        st.markdown(f"**{t('staple_ingredients')}**")
        from search import STAPLE_INGREDIENTS
        staple_opts = STAPLE_INGREDIENTS + (st.session_state.get("staple_ingredients") or [])
        staple_opts = list(dict.fromkeys(staple_opts))  # deduplicate
        selected_staples = st.multiselect(
            t("staple_ingredients"),
            options=staple_opts,
            default=st.session_state.get("staple_ingredients", []),
            label_visibility="collapsed",
        )

        submitted = st.form_submit_button(t("save"), use_container_width=True)
        if submitted:
            st.session_state.daily_calories = cal_goal
            st.session_state.daily_protein = prot_goal
            st.session_state.daily_fat = fat_goal
            st.session_state.daily_carbs = carbs_goal
            st.session_state.staple_ingredients = selected_staples
            _save_profile(user_id, {
                "daily_calories": cal_goal,
                "daily_protein": prot_goal,
                "daily_fat": fat_goal,
                "daily_carbs": carbs_goal,
                "staple_ingredients": ",".join(selected_staples),
            })
            st.success(t("profile_saved"))


def _render_appearance_tab(profile, user_id: str):
    render_section_title(t("appearance"))
    with st.form("appear_form"):
        lang = st.selectbox(
            t("language"),
            options=["de", "en"],
            index=0 if st.session_state.get("language", "de") == "de" else 1,
            format_func=lambda x: "🇩🇪 Deutsch" if x == "de" else "🇬🇧 English",
        )
        theme = st.selectbox(
            "Theme",
            options=["light", "dark"],
            index=0 if st.session_state.get("theme", "light") == "light" else 1,
            format_func=lambda x: f"☀️ {t('light_mode')}" if x == "light" else f"🌙 {t('dark_mode')}",
        )
        units = st.selectbox(
            t("units_system"),
            options=["metric", "imperial"],
            index=0 if st.session_state.get("units", "metric") == "metric" else 1,
            format_func=lambda x: t("units_metric") if x == "metric" else t("units_imperial"),
        )
        submitted = st.form_submit_button(t("save"), use_container_width=True)
        if submitted:
            st.session_state.language = lang
            st.session_state.theme = theme
            st.session_state.units = units
            _save_profile(user_id, {"language": lang, "theme": theme, "units": units})
            st.success(t("profile_saved"))
            st.rerun()


def _render_export_tab(user_id: str):
    render_section_title(t("data_export"))

    # Cookbook JSON
    db = get_db()
    try:
        saved = db.query(SavedRecipe).filter(SavedRecipe.user_id == user_id).all()
        recipes_data = [json.loads(r.recipe_json) for r in saved]
        tracker_entries = db.query(TrackerEntry).filter(TrackerEntry.user_id == user_id).all()
        tracker_data = [
            {
                "recipe_name": e.recipe_name,
                "servings": e.servings,
                "kcal": e.kcal,
                "protein": e.protein,
                "fat": e.fat,
                "carbs": e.carbs,
                "eaten_at": str(e.eaten_at),
            }
            for e in tracker_entries
        ]
    finally:
        db.close()

    col1, col2 = st.columns(2)
    with col1:
        cookbook_json = json.dumps(recipes_data, indent=2, ensure_ascii=False)
        st.download_button(
            t("export_cookbook"),
            data=cookbook_json,
            file_name="kochbuch.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        # Tracker CSV
        if tracker_data:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=tracker_data[0].keys())
            writer.writeheader()
            writer.writerows(tracker_data)
            csv_str = output.getvalue()
        else:
            csv_str = "Keine Einträge vorhanden"
        st.download_button(
            t("export_tracker"),
            data=csv_str,
            file_name="tracker.csv",
            mime="text/csv",
            use_container_width=True,
        )


def _save_profile(user_id: str, updates: dict):
    db = get_db()
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(user_id=user_id)
            db.add(profile)
        for k, v in updates.items():
            if hasattr(profile, k):
                setattr(profile, k, v)
        db.commit()
    finally:
        db.close()


def _delete_account(user_id: str):
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
        logout_user()
        st.success(t("account_deleted"))
    finally:
        db.close()
