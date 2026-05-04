"""
FridgeChef - Authentication helpers
"""
import uuid
import bcrypt
import streamlit as st
from database import get_db, init_db, User, Profile


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def login_user(email: str, password: str) -> tuple[bool, str]:
    """Returns (success, error_message)."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            return False, "E-Mail oder Passwort falsch."
        if not check_password(password, user.password_hash):
            return False, "E-Mail oder Passwort falsch."

        st.session_state.current_user_id = user.id
        st.session_state.current_user_email = user.email
        st.session_state.current_user_name = user.display_name or user.email.split("@")[0]
        _load_user_profile(user.id, db)
        return True, ""
    except Exception as e:
        return False, f"Fehler: {str(e)}"
    finally:
        db.close()


def register_user(email: str, password: str, display_name: str = "") -> tuple[bool, str]:
    """Returns (success, error_message)."""
    db = get_db()
    try:
        existing = db.query(User).filter(User.email == email.lower().strip()).first()
        if existing:
            return False, "Diese E-Mail ist bereits registriert."
        if len(password) < 6:
            return False, "Passwort muss mindestens 6 Zeichen haben."

        user_id = str(uuid.uuid4())
        name = display_name.strip() or email.split("@")[0]
        user = User(
            id=user_id,
            email=email.lower().strip(),
            password_hash=hash_password(password),
            display_name=name,
        )
        profile = Profile(user_id=user_id)
        db.add(user)
        db.add(profile)
        db.commit()

        st.session_state.current_user_id = user_id
        st.session_state.current_user_email = email.lower().strip()
        st.session_state.current_user_name = name
        _load_user_profile(user_id, db)
        return True, ""
    except Exception as e:
        db.rollback()
        return False, f"Fehler: {str(e)}"
    finally:
        db.close()


def logout_user():
    """Clear session state for current user."""
    for key in ["current_user_id", "current_user_email", "current_user_name",
                "language", "theme", "daily_calories", "daily_protein",
                "daily_carbs", "daily_fat", "staple_ingredients", "units"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.page = "search"


def _load_user_profile(user_id: str, db=None):
    """Load profile settings into session state."""
    close = False
    if db is None:
        db = get_db()
        close = True
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if profile:
            st.session_state.language = profile.language or "de"
            st.session_state.theme = profile.theme or "light"
            st.session_state.units = profile.units or "metric"
            st.session_state.daily_calories = profile.daily_calories or 2000
            st.session_state.daily_protein = profile.daily_protein or 150
            st.session_state.daily_carbs = profile.daily_carbs or 250
            st.session_state.daily_fat = profile.daily_fat or 65
            st.session_state.staple_ingredients = (
                profile.staple_ingredients.split(",") if profile.staple_ingredients else []
            )
        else:
            # Create default profile
            new_profile = Profile(user_id=user_id)
            db.add(new_profile)
            db.commit()
            st.session_state.language = "de"
            st.session_state.theme = "light"
            st.session_state.units = "metric"
            st.session_state.daily_calories = 2000
            st.session_state.daily_protein = 150
            st.session_state.daily_carbs = 250
            st.session_state.daily_fat = 65
            st.session_state.staple_ingredients = []
    finally:
        if close:
            db.close()


def is_logged_in() -> bool:
    return bool(st.session_state.get("current_user_id"))


def get_current_user_id() -> str | None:
    return st.session_state.get("current_user_id")


def init_session_defaults():
    """Initialize session state defaults on first load."""
    defaults = {
        "page": "search",
        "language": "de",
        "theme": "light",
        "units": "metric",
        "selected_ingredients": [],
        "staple_ingredients": [],
        "staples_enabled": True,
        "current_recipe": None,
        "search_results": [],
        "daily_calories": 2000,
        "daily_protein": 150,
        "daily_carbs": 250,
        "daily_fat": 65,
        "shopping_badge": 0,
        "confirm_clear_shopping": False,
        "confirm_delete_account": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
