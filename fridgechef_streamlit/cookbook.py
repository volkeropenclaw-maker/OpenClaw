"""
FridgeChef - Cookbook Feature
"""
import json
import streamlit as st
from translations import t
from ui_helpers import render_empty_state, render_section_title
from database import get_db, SavedRecipe


def render_cookbook_page():
    user_id = st.session_state.get("current_user_id")
    if not user_id:
        st.warning("Bitte einloggen.")
        return

    st.subheader(t("cookbook_title"))

    db = get_db()
    try:
        entries = db.query(SavedRecipe).filter(
            SavedRecipe.user_id == user_id
        ).order_by(SavedRecipe.saved_at.desc()).all()
    finally:
        db.close()

    if not entries:
        render_empty_state("📖", t("cookbook_empty"), t("cookbook_empty_hint"))
        return

    # Parse recipes
    all_recipes = []
    for entry in entries:
        try:
            recipe = json.loads(entry.recipe_json)
            recipe["_entry_id"] = entry.id
            recipe["_collection"] = entry.collection_name or ""
            all_recipes.append(recipe)
        except Exception:
            pass

    # ── Search & Filter ────────────────────────────────────────
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        query = st.text_input(
            t("search_cookbook"),
            placeholder=t("search_cookbook"),
            label_visibility="collapsed",
            key="cookbook_search",
        )
    with col_filter:
        collections = sorted({r["_collection"] for r in all_recipes if r["_collection"]})
        col_options = [t("all_collections")] + collections
        sel_col = st.selectbox(
            t("collection"),
            options=col_options,
            key="col_filter",
            label_visibility="collapsed",
        )

    # Filter
    filtered = all_recipes
    if query:
        filtered = [r for r in filtered if query.lower() in r.get("name", "").lower()]
    if sel_col != t("all_collections"):
        filtered = [r for r in filtered if r.get("_collection") == sel_col]

    st.markdown(f"**{len(filtered)} Rezept(e)**")

    if not filtered:
        render_empty_state("🔍", "Keine Rezepte gefunden.", "Suchbegriff ändern.")
        return

    # ── Recipe Cards ───────────────────────────────────────────
    cols = st.columns(2)
    for i, recipe in enumerate(filtered):
        with cols[i % 2]:
            _render_cookbook_card(recipe, user_id, i)


def _render_cookbook_card(recipe: dict, user_id: str, idx: int):
    entry_id = recipe.get("_entry_id", "")
    name = recipe.get("name", "Rezept")
    cuisine = recipe.get("cuisine", "")
    prep_time = recipe.get("prepTime", 0)
    difficulty = recipe.get("difficulty", "Medium")
    image = recipe.get("image", "")
    tags = recipe.get("tags", [])

    with st.container(border=True):
        if image:
            st.image(image, use_container_width=True)
        st.markdown(f"**{name}**")
        st.caption(f"🌍 {cuisine}  |  ⏱ {prep_time} {t('minutes')}  |  📊 {t(difficulty)}")
        for tag in tags[:3]:
            st.badge(tag)

        col_view, col_col, col_del = st.columns([2, 2, 1])
        with col_view:
            if st.button("👁 Ansehen", key=f"cb_view_{idx}", use_container_width=True):
                st.session_state.current_recipe = recipe
                st.session_state.page = "recipe_detail"
                st.rerun()
        with col_col:
            new_col = st.text_input(
                "Sammlung",
                value=recipe.get("_collection", ""),
                key=f"col_input_{idx}",
                label_visibility="collapsed",
                placeholder=t("collection"),
            )
            if new_col != recipe.get("_collection", ""):
                _update_collection(entry_id, new_col)
        with col_del:
            if st.button("🗑", key=f"cb_del_{idx}", help=t("delete"), use_container_width=True):
                _delete_saved_recipe(entry_id, user_id)
                st.rerun()


def _delete_saved_recipe(entry_id: str, user_id: str):
    db = get_db()
    try:
        entry = db.query(SavedRecipe).filter(
            SavedRecipe.id == entry_id,
            SavedRecipe.user_id == user_id,
        ).first()
        if entry:
            db.delete(entry)
            db.commit()
            st.success(t("recipe_removed"))
    finally:
        db.close()


def _update_collection(entry_id: str, collection_name: str):
    db = get_db()
    try:
        entry = db.query(SavedRecipe).filter(SavedRecipe.id == entry_id).first()
        if entry:
            entry.collection_name = collection_name
            db.commit()
    finally:
        db.close()
