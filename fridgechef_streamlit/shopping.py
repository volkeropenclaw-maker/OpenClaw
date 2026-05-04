"""
FridgeChef - Shopping List Feature
"""
import uuid
import streamlit as st
from translations import t
from ui_helpers import render_empty_state
from database import get_db, ShoppingListItem


def render_shopping_page():
    user_id = st.session_state.get("current_user_id")
    if not user_id:
        st.warning("Bitte einloggen.")
        return

    st.subheader(t("shopping_title"))

    db = get_db()
    try:
        items = db.query(ShoppingListItem).filter(
            ShoppingListItem.user_id == user_id
        ).order_by(ShoppingListItem.recipe_name).all()
        items_data = [
            {
                "id": item.id,
                "name": item.ingredient_name,
                "amount": item.amount,
                "unit": item.unit,
                "recipe_id": item.recipe_id,
                "recipe_name": item.recipe_name or "Sonstiges",
                "is_completed": item.is_completed,
            }
            for item in items
        ]
    finally:
        db.close()

    if not items_data:
        render_empty_state("🛒", t("shopping_empty"), t("shopping_empty_hint"))
        return

    # ── Stats & Actions ────────────────────────────────────────
    open_items = [i for i in items_data if not i["is_completed"]]
    done_items = [i for i in items_data if i["is_completed"]]

    col_stat, col_export, col_clear = st.columns([2, 1, 1])
    with col_stat:
        st.metric(t("items_remaining", n=len(open_items)), f"{len(done_items)}/{len(items_data)} erledigt")
    with col_export:
        export_text = _build_export_text(items_data)
        st.download_button(
            t("export_list"),
            data=export_text,
            file_name="einkaufsliste.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_clear:
        if st.button(t("clear_shopping"), use_container_width=True, key="clear_shop_btn"):
            st.session_state.confirm_clear_shopping = True

    if st.session_state.get("confirm_clear_shopping"):
        st.warning(t("confirm_clear"))
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button(t("yes"), key="confirm_clear_yes", use_container_width=True):
                _clear_all(user_id)
                st.session_state.confirm_clear_shopping = False
                st.session_state.shopping_badge = 0
                st.rerun()
        with col_no:
            if st.button(t("no"), key="confirm_clear_no", use_container_width=True):
                st.session_state.confirm_clear_shopping = False
                st.rerun()

    st.divider()

    # ── Smart Merge: group by ingredient name across recipes ───
    merged = _smart_merge(items_data)

    # ── Group by Recipe ────────────────────────────────────────
    grouped = {}
    for item in items_data:
        key = item["recipe_name"]
        grouped.setdefault(key, []).append(item)

    for recipe_name, recipe_items in grouped.items():
        with st.expander(f"📋 **{recipe_name}** ({len(recipe_items)} Items)", expanded=True):
            for item in recipe_items:
                _render_shopping_item(item, user_id, merged)

    # ── Update badge ───────────────────────────────────────────
    st.session_state.shopping_badge = len(open_items)


def _smart_merge(items: list) -> dict:
    """
    Build a dict: ingredient_name → {total_amount, unit, recipes}
    for items with the same name across different recipes.
    """
    merged = {}
    for item in items:
        key = item["name"].lower().strip()
        if key not in merged:
            merged[key] = {"amount": 0.0, "unit": item["unit"], "recipes": []}
        merged[key]["amount"] += item.get("amount", 0) or 0
        rname = item.get("recipe_name", "")
        if rname and rname not in merged[key]["recipes"]:
            merged[key]["recipes"].append(rname)
    return merged


def _render_shopping_item(item: dict, user_id: str, merged: dict):
    item_id = item["id"]
    name = item["name"]
    amount = item.get("amount", 0)
    unit = item.get("unit", "")
    completed = item.get("is_completed", False)

    key_norm = name.lower().strip()
    merge_info = merged.get(key_norm, {})
    multi_recipe = len(merge_info.get("recipes", [])) > 1

    col_check, col_label, col_del = st.columns([1, 8, 1])
    with col_check:
        new_state = st.checkbox(
            "",
            value=completed,
            key=f"chk_{item_id}",
            label_visibility="collapsed",
        )
        if new_state != completed:
            _toggle_item(item_id, new_state, user_id)
            st.rerun()

    with col_label:
        style = "text-decoration: line-through; opacity: 0.5;" if completed else ""
        amount_str = f"{amount} {unit}" if amount else unit
        tooltip = ""
        if multi_recipe:
            recipes_str = ", ".join(merge_info["recipes"])
            tooltip = f" 🔀 {t('merged_from', recipes=recipes_str)}"
            amount_str = f"{round(merge_info['amount'], 1)} {merge_info['unit']}"
        st.markdown(
            f'<span style="{style}">{amount_str} **{name}**{tooltip}</span>',
            unsafe_allow_html=True,
        )

    with col_del:
        if st.button("🗑", key=f"del_{item_id}", help=t("delete"), use_container_width=True):
            _delete_item(item_id, user_id)
            st.rerun()


def _toggle_item(item_id: str, new_state: bool, user_id: str):
    db = get_db()
    try:
        item = db.query(ShoppingListItem).filter(
            ShoppingListItem.id == item_id,
            ShoppingListItem.user_id == user_id,
        ).first()
        if item:
            item.is_completed = new_state
            db.commit()
    finally:
        db.close()


def _delete_item(item_id: str, user_id: str):
    db = get_db()
    try:
        item = db.query(ShoppingListItem).filter(
            ShoppingListItem.id == item_id,
            ShoppingListItem.user_id == user_id,
        ).first()
        if item:
            db.delete(item)
            db.commit()
    finally:
        db.close()


def _clear_all(user_id: str):
    db = get_db()
    try:
        db.query(ShoppingListItem).filter(
            ShoppingListItem.user_id == user_id
        ).delete()
        db.commit()
        st.success(t("clear_shopping") + " ✓")
    finally:
        db.close()


def _build_export_text(items: list) -> str:
    lines = ["FridgeChef - Einkaufsliste", "=" * 30, ""]
    grouped = {}
    for item in items:
        key = item["recipe_name"]
        grouped.setdefault(key, []).append(item)

    for recipe, recipe_items in grouped.items():
        lines.append(f"[{recipe}]")
        for item in recipe_items:
            status = "✓" if item["is_completed"] else "○"
            amount = f"{item['amount']} {item['unit']}" if item.get("amount") else ""
            lines.append(f"  {status} {amount} {item['name']}".strip())
        lines.append("")
    return "\n".join(lines)
