"""
FridgeChef - UI Helper functions
"""
import streamlit as st
from translations import t

BROWN = "#6B4226"
BROWN_LIGHT = "#8B5E3C"
OFF_WHITE = "#FAF7F2"
OFF_WHITE_DARK = "#F0EBE3"
ACCENT = "#D4956A"
ACCENT_DARK = "#B87A50"
TEXT_DARK = "#2C1810"
TEXT_MUTED = "#8B7355"
SUCCESS = "#4CAF50"
ERROR = "#E53935"
WARNING = "#FF9800"

DARK_BG = "#1A1108"
DARK_CARD = "#2C1E10"
DARK_BORDER = "#4A3020"
DARK_TEXT = "#F5EFE7"


def apply_custom_css():
    """Inject custom CSS for Off-White + Brown theme with dark mode support."""
    is_dark = st.session_state.get("theme", "light") == "dark"

    if is_dark:
        bg = DARK_BG
        card_bg = DARK_CARD
        text = DARK_TEXT
        muted = "#A0907A"
        border = DARK_BORDER
        input_bg = DARK_CARD
        sidebar_bg = "#150E07"
        header_bg = DARK_CARD
    else:
        bg = OFF_WHITE
        card_bg = "#FFFFFF"
        text = TEXT_DARK
        muted = TEXT_MUTED
        border = "#DDD3C7"
        input_bg = "#FFFFFF"
        sidebar_bg = OFF_WHITE_DARK
        header_bg = BROWN

    st.markdown(f"""
<style>
    /* ── Root & Page ─────────────────────────────── */
    .stApp {{
        background-color: {bg};
        color: {text};
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }}

    /* ── Sidebar ─────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {border};
    }}
    [data-testid="stSidebar"] * {{
        color: {text} !important;
    }}

    /* ── Header ──────────────────────────────────── */
    .fc-header {{
        background: {header_bg};
        padding: 12px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .fc-header h1 {{
        color: #FFFFFF;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }}
    .fc-tagline {{
        color: rgba(255,255,255,0.7);
        font-size: 0.85rem;
        margin-top: 2px;
    }}

    /* ── Recipe Cards ────────────────────────────── */
    .fc-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
        cursor: pointer;
    }}
    .fc-card:hover {{
        box-shadow: 0 4px 16px rgba(107, 66, 38, 0.15);
        transform: translateY(-2px);
    }}
    .fc-card-title {{
        color: {BROWN};
        font-size: 1.05rem;
        font-weight: 600;
        margin: 8px 0 4px;
    }}
    .fc-card-meta {{
        color: {muted};
        font-size: 0.82rem;
    }}
    .fc-badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        background: {ACCENT};
        color: white;
        margin: 2px;
    }}

    /* ── Match Meter ─────────────────────────────── */
    .fc-match-bar {{
        height: 6px;
        border-radius: 3px;
        background: #E0D5CC;
        margin-top: 6px;
        overflow: hidden;
    }}
    .fc-match-fill {{
        height: 100%;
        background: {BROWN};
        border-radius: 3px;
        transition: width 0.3s ease;
    }}

    /* ── Ingredient Pills ────────────────────────── */
    .fc-pill {{
        display: inline-flex;
        align-items: center;
        background: {OFF_WHITE_DARK if not is_dark else '#3A2510'};
        border: 1px solid {border};
        border-radius: 20px;
        padding: 4px 10px;
        margin: 3px;
        font-size: 0.85rem;
        color: {text};
    }}
    .fc-pill-missing {{
        background: rgba(229, 57, 53, 0.1);
        border-color: {ERROR};
        color: {ERROR};
    }}
    .fc-pill-available {{
        background: rgba(76, 175, 80, 0.1);
        border-color: {SUCCESS};
        color: {'#2E7D32' if not is_dark else '#81C784'};
    }}

    /* ── Buttons ─────────────────────────────────── */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    .stButton > button[kind="primary"] {{
        background: {BROWN};
        border-color: {BROWN};
        color: white;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: {BROWN_LIGHT};
        border-color: {BROWN_LIGHT};
    }}

    /* ── Forms & Inputs ──────────────────────────── */
    .stTextInput input, .stSelectbox select, .stNumberInput input {{
        background: {input_bg};
        border-color: {border};
        color: {text};
        border-radius: 8px;
    }}

    /* ── Empty State ─────────────────────────────── */
    .fc-empty {{
        text-align: center;
        padding: 60px 20px;
        color: {muted};
    }}
    .fc-empty-icon {{
        font-size: 3rem;
        margin-bottom: 12px;
    }}
    .fc-empty-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {text};
        margin-bottom: 6px;
    }}
    .fc-empty-hint {{
        font-size: 0.9rem;
        color: {muted};
    }}

    /* ── Nutrition Table ─────────────────────────── */
    .fc-nutrition-row {{
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid {border};
        font-size: 0.9rem;
    }}
    .fc-nutrition-label {{ color: {muted}; }}
    .fc-nutrition-value {{ font-weight: 600; color: {text}; }}

    /* ── Shopping Item ───────────────────────────── */
    .fc-shopping-item {{
        display: flex;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid {border};
    }}
    .fc-shopping-item.completed {{
        opacity: 0.5;
        text-decoration: line-through;
    }}

    /* ── Progress Ring (CSS-based) ───────────────── */
    .fc-ring-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px auto;
    }}

    /* ── Misc ────────────────────────────────────── */
    .fc-section-title {{
        font-size: 1.2rem;
        font-weight: 600;
        color: {BROWN};
        margin: 20px 0 10px;
        padding-bottom: 6px;
        border-bottom: 2px solid {ACCENT};
    }}
    .fc-divider {{
        border: none;
        border-top: 1px solid {border};
        margin: 16px 0;
    }}
    hr {{
        border-color: {border} !important;
    }}

    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render the top header bar."""
    logo = "🍴"
    title = t("app_title")
    tagline = t("app_tagline")
    st.markdown(f"""
<div class="fc-header">
  <div>
    <h1>{logo} {title}</h1>
    <div class="fc-tagline">{tagline}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_recipe_card(recipe: dict, match_pct: float = 1.0, key_prefix: str = "") -> bool:
    """
    Render a recipe card. Returns True if the card was clicked (view button pressed).
    """
    recipe_id = recipe.get("id", "")
    name = recipe.get("name", "Rezept")
    cuisine = recipe.get("cuisine", "")
    difficulty = recipe.get("difficulty", "Medium")
    prep_time = recipe.get("prepTime", 0)
    tags = recipe.get("tags", [])
    image_url = recipe.get("image", "")

    diff_label = t(difficulty) if difficulty in ("Easy", "Medium", "Hard") else difficulty
    pct_int = int(match_pct * 100)
    badge_html = "".join(f'<span class="fc-badge">{tag}</span>' for tag in tags[:3])

    col_img, col_info = st.columns([1, 3])
    with col_img:
        if image_url:
            st.image(image_url, width=100)
        else:
            st.markdown("🍽️", unsafe_allow_html=False)

    with col_info:
        st.markdown(f"""
<div class="fc-card-title">{name}</div>
<div class="fc-card-meta">
  🌍 {cuisine} &nbsp;|&nbsp; ⏱ {prep_time} {t('minutes')} &nbsp;|&nbsp; 📊 {diff_label}
</div>
<div style="margin-top:4px">{badge_html}</div>
<div class="fc-match-bar"><div class="fc-match-fill" style="width:{pct_int}%"></div></div>
<div class="fc-card-meta" style="margin-top:2px">{pct_int}% {t('available')}</div>
""", unsafe_allow_html=True)

    key = f"view_{key_prefix}_{recipe_id}"
    return st.button(f"👁 Rezept ansehen", key=key, use_container_width=True)


def render_empty_state(icon: str, title: str, hint: str = ""):
    """Render a centered empty state."""
    st.markdown(f"""
<div class="fc-empty">
  <div class="fc-empty-icon">{icon}</div>
  <div class="fc-empty-title">{title}</div>
  {"<div class='fc-empty-hint'>" + hint + "</div>" if hint else ""}
</div>
""", unsafe_allow_html=True)


def render_nutrition_table(nutrition: dict):
    """Render a styled nutrition facts table."""
    rows = [
        (t("kcal"),    f"{nutrition.get('kcal', 0)} kcal"),
        (t("protein"), f"{nutrition.get('protein', 0)} g"),
        (t("fat"),     f"{nutrition.get('fat', 0)} g"),
        (t("carbs"),   f"{nutrition.get('carbs', 0)} g"),
        (t("fiber"),   f"{nutrition.get('fiber', 0)} g"),
        (t("salt"),    f"{nutrition.get('salt', 0)} g"),
    ]
    html = "".join(
        f'<div class="fc-nutrition-row"><span class="fc-nutrition-label">{label}</span>'
        f'<span class="fc-nutrition-value">{value}</span></div>'
        for label, value in rows
    )
    st.markdown(f'<div style="margin:12px 0">{html}</div>', unsafe_allow_html=True)


def render_section_title(title: str):
    st.markdown(f'<div class="fc-section-title">{title}</div>', unsafe_allow_html=True)


def responsive_columns(n: int = 3):
    """Return columns adjusted for responsive layout."""
    # On mobile, Streamlit naturally stacks — we just return 1–3 cols
    return st.columns(min(n, 3))


def render_ingredient_pill(name: str, available: bool = True):
    cls = "fc-pill-available" if available else "fc-pill-missing"
    icon = "✅" if available else "❌"
    st.markdown(
        f'<span class="fc-pill {cls}">{icon} {name}</span>',
        unsafe_allow_html=True,
    )


def theme_toggle_button():
    """Small toggle for dark/light mode."""
    current = st.session_state.get("theme", "light")
    label = "☀️ Hell" if current == "dark" else "🌙 Dunkel"
    if st.button(label, key="theme_toggle"):
        st.session_state.theme = "light" if current == "dark" else "dark"
        st.rerun()


def language_switcher():
    """Language select widget."""
    lang = st.session_state.get("language", "de")
    new_lang = st.selectbox(
        "",
        options=["de", "en"],
        index=0 if lang == "de" else 1,
        format_func=lambda x: "🇩🇪 Deutsch" if x == "de" else "🇬🇧 English",
        key="lang_select",
        label_visibility="collapsed",
    )
    if new_lang != lang:
        st.session_state.language = new_lang
        st.rerun()
