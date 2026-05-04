"""
FridgeChef - Nutrition Tracker Feature
"""
import uuid
from datetime import date, timedelta
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from translations import t
from ui_helpers import render_empty_state
from database import get_db, TrackerEntry


def render_tracker_page():
    user_id = st.session_state.get("current_user_id")
    if not user_id:
        st.warning("Bitte einloggen.")
        return

    st.subheader(t("tracker_title"))

    # ── Date Picker ────────────────────────────────────────────
    col_prev, col_date, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀", key="prev_day", use_container_width=True):
            current = st.session_state.get("tracker_date", date.today())
            st.session_state.tracker_date = current - timedelta(days=1)
            st.rerun()
    with col_date:
        selected_date = st.date_input(
            t("today"),
            value=st.session_state.get("tracker_date", date.today()),
            key="tracker_date_input",
            label_visibility="collapsed",
        )
        st.session_state.tracker_date = selected_date
    with col_next:
        if st.button("▶", key="next_day", use_container_width=True):
            current = st.session_state.get("tracker_date", date.today())
            if current < date.today():
                st.session_state.tracker_date = current + timedelta(days=1)
            st.rerun()

    selected_date = st.session_state.get("tracker_date", date.today())

    # ── Tab View ───────────────────────────────────────────────
    tab_day, tab_week, tab_month = st.tabs([t("day_view"), t("week_view"), t("month_view")])

    with tab_day:
        _render_day_view(user_id, selected_date)
    with tab_week:
        _render_period_chart(user_id, selected_date, days=7, label=t("week_view"))
    with tab_month:
        _render_period_chart(user_id, selected_date, days=30, label=t("month_view"))


def _get_entries_for_date(user_id: str, target_date: date) -> list[dict]:
    db = get_db()
    try:
        start = target_date
        end = target_date + timedelta(days=1)
        entries = db.query(TrackerEntry).filter(
            TrackerEntry.user_id == user_id,
            TrackerEntry.eaten_at >= start,
            TrackerEntry.eaten_at < end,
        ).order_by(TrackerEntry.eaten_at).all()
        return [
            {
                "id": e.id,
                "recipe_name": e.recipe_name,
                "servings": e.servings,
                "kcal": e.kcal or 0,
                "protein": e.protein or 0,
                "fat": e.fat or 0,
                "carbs": e.carbs or 0,
                "eaten_at": e.eaten_at,
            }
            for e in entries
        ]
    finally:
        db.close()


def _render_day_view(user_id: str, target_date: date):
    entries = _get_entries_for_date(user_id, target_date)

    goals = {
        "kcal": st.session_state.get("daily_calories", 2000),
        "protein": st.session_state.get("daily_protein", 150),
        "fat": st.session_state.get("daily_fat", 65),
        "carbs": st.session_state.get("daily_carbs", 250),
    }

    totals = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for e in entries:
        for k in totals:
            totals[k] += e.get(k, 0)

    # ── Ring Chart (Calories) ──────────────────────────────────
    kcal_pct = min(totals["kcal"] / max(goals["kcal"], 1), 1.0)
    fig_ring = go.Figure(go.Pie(
        values=[totals["kcal"], max(goals["kcal"] - totals["kcal"], 0)],
        labels=[t("consumed"), t("remaining_goal")],
        hole=0.7,
        marker_colors=["#6B4226", "#E0D5CC"],
        textinfo="none",
    ))
    fig_ring.add_annotation(
        text=f"<b>{int(totals['kcal'])}</b><br>kcal",
        x=0.5, y=0.5, showarrow=False, font_size=16,
    )
    fig_ring.update_layout(
        showlegend=True,
        height=250,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_ring, use_container_width=True)

    # ── Macro Bars ────────────────────────────────────────────
    macro_data = {
        "Protein": (totals["protein"], goals["protein"], "#4CAF50"),
        "Fat": (totals["fat"], goals["fat"], "#FF9800"),
        "Carbs": (totals["carbs"], goals["carbs"], "#2196F3"),
    }
    cols = st.columns(3)
    for col, (label, (consumed, goal, color)) in zip(cols, macro_data.items()):
        pct = min(consumed / max(goal, 1), 1.0)
        with col:
            st.markdown(f"**{label}**")
            st.progress(pct, text=f"{consumed:.0f}/{goal}g")

    st.divider()

    # ── Add Custom Entry ──────────────────────────────────────
    with st.expander(f"➕ {t('add_custom_entry')}", expanded=False):
        with st.form("custom_entry_form"):
            name = st.text_input(t("custom_entry_name"), placeholder="Apfel")
            col_kcal, col_p, col_f, col_c = st.columns(4)
            with col_kcal:
                kcal = st.number_input(t("custom_entry_kcal"), min_value=0.0, step=1.0, value=0.0)
            with col_p:
                protein = st.number_input(t("custom_entry_protein"), min_value=0.0, step=0.1, value=0.0)
            with col_f:
                fat = st.number_input(t("custom_entry_fat"), min_value=0.0, step=0.1, value=0.0)
            with col_c:
                carbs = st.number_input(t("custom_entry_carbs"), min_value=0.0, step=0.1, value=0.0)
            submitted = st.form_submit_button(t("add_custom_entry"), use_container_width=True)
            if submitted:
                if name.strip():
                    _add_custom_entry(user_id, name.strip(), kcal, protein, fat, carbs, target_date)
                    st.success(t("entry_added"))
                    st.rerun()
                else:
                    st.error("Bitte einen Namen eingeben.")

    # ── Entries List ──────────────────────────────────────────
    if not entries:
        render_empty_state("🍽️", t("tracker_empty"), t("tracker_empty_hint"))
        return

    st.markdown(f"**{t('today')}: {target_date.strftime('%d.%m.%Y')}**")
    for entry in entries:
        col_info, col_edit, col_del = st.columns([5, 1, 1])
        with col_info:
            eaten_str = entry["eaten_at"].strftime("%H:%M") if entry.get("eaten_at") else ""
            st.markdown(
                f"🍽️ **{entry['recipe_name']}** ({entry['servings']}x)  "
                f"— {entry['kcal']:.0f} kcal | P:{entry['protein']:.0f}g | "
                f"F:{entry['fat']:.0f}g | C:{entry['carbs']:.0f}g  "
                f"<small style='color:#8B7355'>{eaten_str}</small>",
                unsafe_allow_html=True,
            )
        with col_edit:
            if st.button("✏️", key=f"edit_{entry['id']}", help=t("edit")):
                st.session_state[f"editing_{entry['id']}"] = True
        with col_del:
            if st.button("🗑", key=f"del_entry_{entry['id']}", help=t("delete")):
                _delete_entry(entry["id"], user_id)
                st.rerun()

        # Inline edit
        if st.session_state.get(f"editing_{entry['id']}"):
            with st.form(f"edit_form_{entry['id']}"):
                new_servings = st.number_input("Portionen", min_value=0.1, step=0.5, value=float(entry["servings"]))
                new_kcal = st.number_input("kcal", min_value=0.0, step=1.0, value=float(entry["kcal"]))
                c1, c2 = st.columns(2)
                with c1:
                    save_edit = st.form_submit_button(t("save"), use_container_width=True)
                with c2:
                    cancel_edit = st.form_submit_button(t("cancel"), use_container_width=True)
                if save_edit:
                    _update_entry(entry["id"], user_id, new_servings, new_kcal)
                    del st.session_state[f"editing_{entry['id']}"]
                    st.rerun()
                if cancel_edit:
                    del st.session_state[f"editing_{entry['id']}"]
                    st.rerun()


def _render_period_chart(user_id: str, ref_date: date, days: int, label: str):
    """Render a bar chart for a period (week/month)."""
    db = get_db()
    try:
        start = ref_date - timedelta(days=days - 1)
        entries = db.query(TrackerEntry).filter(
            TrackerEntry.user_id == user_id,
            TrackerEntry.eaten_at >= start,
            TrackerEntry.eaten_at < ref_date + timedelta(days=1),
        ).all()
    finally:
        db.close()

    if not entries:
        render_empty_state("📊", f"Keine Daten für {label}.", "Mahlzeiten als gegessen markieren.")
        return

    # Aggregate by date
    data = {}
    for e in entries:
        d = e.eaten_at.date() if e.eaten_at else ref_date
        if d not in data:
            data[d] = {"kcal": 0, "protein": 0, "fat": 0, "carbs": 0}
        data[d]["kcal"] += e.kcal or 0
        data[d]["protein"] += e.protein or 0
        data[d]["fat"] += e.fat or 0
        data[d]["carbs"] += e.carbs or 0

    df = pd.DataFrame([
        {"date": str(d), **vals}
        for d, vals in sorted(data.items())
    ])

    goal_kcal = st.session_state.get("daily_calories", 2000)

    fig = go.Figure()
    fig.add_bar(x=df["date"], y=df["kcal"], name="Kcal", marker_color="#6B4226")
    fig.add_hline(y=goal_kcal, line_dash="dash", line_color="#D4956A", annotation_text=f"Ziel: {goal_kcal}")
    fig.update_layout(
        title=label,
        xaxis_title="Datum",
        yaxis_title="kcal",
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Macro stacked bar
    fig2 = px.bar(df, x="date", y=["protein", "fat", "carbs"],
                  title="Makros", barmode="stack",
                  color_discrete_map={"protein": "#4CAF50", "fat": "#FF9800", "carbs": "#2196F3"})
    fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)


def _add_custom_entry(user_id, name, kcal, protein, fat, carbs, entry_date):
    from datetime import datetime
    db = get_db()
    try:
        entry = TrackerEntry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            recipe_id="custom",
            recipe_name=name,
            servings=1,
            kcal=kcal,
            protein=protein,
            fat=fat,
            carbs=carbs,
            eaten_at=datetime.combine(entry_date, datetime.min.time()),
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def _delete_entry(entry_id: str, user_id: str):
    db = get_db()
    try:
        entry = db.query(TrackerEntry).filter(
            TrackerEntry.id == entry_id,
            TrackerEntry.user_id == user_id,
        ).first()
        if entry:
            db.delete(entry)
            db.commit()
            st.success(t("entry_deleted"))
    finally:
        db.close()


def _update_entry(entry_id: str, user_id: str, servings: float, kcal: float):
    db = get_db()
    try:
        entry = db.query(TrackerEntry).filter(
            TrackerEntry.id == entry_id,
            TrackerEntry.user_id == user_id,
        ).first()
        if entry:
            entry.servings = servings
            entry.kcal = kcal
            db.commit()
    finally:
        db.close()
