"""
FridgeChef - Main Streamlit Application
"""
import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from database import init_db
from auth import init_session_defaults, is_logged_in, login_user, register_user
from translations import t
from ui_helpers import apply_custom_css, render_header, theme_toggle_button, language_switcher

# ── Page config (must be first Streamlit call) ─────────────────────
st.set_page_config(
    page_title="FridgeChef",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init ────────────────────────────────────────────────────────────
init_db()
init_session_defaults()
apply_custom_css()


def render_login_page():
    """Login / Signup page."""
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        st.markdown("""
<div style="text-align:center; margin-bottom: 32px;">
  <h1 style="color:#6B4226; font-size:2.5rem;">🍴 FridgeChef</h1>
  <p style="color:#8B7355;">Koche mit dem, was du hast</p>
</div>
""", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs([t("login"), t("register")])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input(t("email"), placeholder="deine@email.de")
                password = st.text_input(t("password"), type="password", placeholder="••••••••")
                submitted = st.form_submit_button(t("login"), use_container_width=True, type="primary")
                if submitted:
                    if not email or not password:
                        st.error("Bitte E-Mail und Passwort eingeben.")
                    else:
                        with st.spinner(t("loading")):
                            ok, msg = login_user(email, password)
                        if ok:
                            st.success(t("login_success"))
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_register:
            with st.form("register_form"):
                display_name = st.text_input(t("display_name"), placeholder="Max Mustermann")
                reg_email = st.text_input(t("email"), placeholder="deine@email.de", key="reg_email")
                reg_pw = st.text_input(t("password"), type="password", key="reg_pw")
                reg_pw2 = st.text_input(t("password_confirm"), type="password", key="reg_pw2")
                reg_submitted = st.form_submit_button(t("register"), use_container_width=True, type="primary")
                if reg_submitted:
                    if not reg_email or not reg_pw:
                        st.error("Bitte alle Felder ausfüllen.")
                    elif reg_pw != reg_pw2:
                        st.error(t("passwords_mismatch"))
                    elif len(reg_pw) < 6:
                        st.error(t("password_too_short"))
                    elif "@" not in reg_email:
                        st.error(t("invalid_email"))
                    else:
                        with st.spinner(t("loading")):
                            ok, msg = register_user(reg_email, reg_pw, display_name)
                        if ok:
                            st.success(t("register_success"))
                            st.rerun()
                        else:
                            st.error(msg)


def render_sidebar():
    """Sidebar navigation."""
    with st.sidebar:
        # User info
        user_name = st.session_state.get("current_user_name", "")
        if user_name:
            initials = user_name[:2].upper()
            st.markdown(f"""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
  <div style="width:40px; height:40px; border-radius:50%; background:#6B4226;
    color:white; display:flex; align-items:center; justify-content:center;
    font-weight:bold; font-size:1.1rem;">{initials}</div>
  <div style="font-weight:600; color:#6B4226;">{user_name}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        shopping_badge = st.session_state.get("shopping_badge", 0)
        nav_items = [
            ("search",   t("nav_search")),
            ("cookbook", t("nav_cookbook")),
            ("shopping", f"{t('nav_shopping')}{' (' + str(shopping_badge) + ')' if shopping_badge else ''}"),
            ("tracker",  t("nav_tracker")),
            ("profile",  t("nav_profile")),
        ]
        current_page = st.session_state.get("page", "search")
        for page_key, label in nav_items:
            is_active = current_page == page_key
            style = "background: #6B4226; color: white; border-radius: 8px; padding: 4px 8px;" if is_active else ""
            if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.session_state.current_recipe = None
                st.rerun()

        st.markdown("---")

        # Language & Theme
        language_switcher()
        theme_toggle_button()


def render_main_content():
    """Render main content based on current page."""
    page = st.session_state.get("page", "search")

    # Recipe detail overrides any page
    if st.session_state.get("current_recipe") and page != "cookbook":
        from search import render_recipe_detail
        recipe = st.session_state.current_recipe
        user_ings = st.session_state.get("selected_ingredients", [])
        if st.session_state.get("staples_enabled"):
            from search import STAPLE_INGREDIENTS
            user_ings = user_ings + STAPLE_INGREDIENTS
        render_recipe_detail(recipe, user_ings)
        return

    if page == "search":
        from search import render_search_page
        render_search_page()
    elif page == "cookbook":
        from cookbook import render_cookbook_page
        render_cookbook_page()
    elif page == "shopping":
        from shopping import render_shopping_page
        render_shopping_page()
    elif page == "tracker":
        from tracker import render_tracker_page
        render_tracker_page()
    elif page == "profile":
        from profile import render_profile_page
        render_profile_page()
    else:
        st.error(f"Unbekannte Seite: {page}")


# ── Main app flow ───────────────────────────────────────────────────
if not is_logged_in():
    render_login_page()
else:
    render_header()
    render_sidebar()
    render_main_content()
