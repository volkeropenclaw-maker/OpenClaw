"""
FridgeChef - Search Feature (Text + Photo, Spoonacular + OpenAI fallback)
"""
import os
import json
import base64
import hashlib
import uuid
import requests
import streamlit as st
from translations import t
from ui_helpers import render_recipe_card, render_empty_state, render_section_title, render_ingredient_pill, render_nutrition_table
from database import get_db, AIRecipeCache, ShoppingListItem, SavedRecipe

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False

SPOONACULAR_KEY = os.getenv("SPOONACULAR_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600&h=400&fit=crop"

COMMON_INGREDIENTS = [
    "Chicken", "Beef", "Pasta", "Rice", "Tomatoes", "Onion", "Garlic",
    "Eggs", "Cheese", "Butter", "Milk", "Potatoes", "Carrots", "Spinach",
    "Mushrooms", "Salmon", "Shrimp", "Tofu", "Lentils", "Chickpeas",
]
STAPLE_INGREDIENTS = [
    "Salt", "Pepper", "Olive Oil", "Flour", "Sugar", "Soy Sauce",
    "Vinegar", "Paprika", "Cumin", "Oregano",
]

NUTRITION_DB = {
    "chicken":      {"kcal": 165, "protein": 31,  "fat": 3.6, "carbs": 0, "fiber": 0, "salt": 0.1},
    "beef":         {"kcal": 250, "protein": 26,  "fat": 15,  "carbs": 0, "fiber": 0, "salt": 0.1},
    "pork":         {"kcal": 242, "protein": 27,  "fat": 14,  "carbs": 0, "fiber": 0, "salt": 0.1},
    "salmon":       {"kcal": 208, "protein": 20,  "fat": 13,  "carbs": 0, "fiber": 0, "salt": 0.2},
    "shrimp":       {"kcal": 85,  "protein": 18,  "fat": 1,   "carbs": 0, "fiber": 0, "salt": 0.5},
    "tofu":         {"kcal": 76,  "protein": 8,   "fat": 4.5, "carbs": 2, "fiber": 0.3, "salt": 0.1},
    "rice":         {"kcal": 130, "protein": 2.7, "fat": 0.3, "carbs": 28, "fiber": 0.4, "salt": 0},
    "pasta":        {"kcal": 157, "protein": 5.8, "fat": 0.9, "carbs": 31, "fiber": 1.8, "salt": 0},
    "flour":        {"kcal": 364, "protein": 10,  "fat": 1,   "carbs": 76, "fiber": 2.7, "salt": 0},
    "egg":          {"kcal": 155, "protein": 13,  "fat": 11,  "carbs": 1.1, "fiber": 0, "salt": 0.4},
    "milk":         {"kcal": 61,  "protein": 3.2, "fat": 3.3, "carbs": 4.8, "fiber": 0, "salt": 0.1},
    "butter":       {"kcal": 717, "protein": 0.9, "fat": 81,  "carbs": 0.1, "fiber": 0, "salt": 0.6},
    "cheese":       {"kcal": 400, "protein": 25,  "fat": 33,  "carbs": 1.3, "fiber": 0, "salt": 1.7},
    "tomato":       {"kcal": 18,  "protein": 0.9, "fat": 0.2, "carbs": 3.9, "fiber": 1.2, "salt": 0},
    "onion":        {"kcal": 40,  "protein": 1.1, "fat": 0.1, "carbs": 9.3, "fiber": 1.7, "salt": 0},
    "garlic":       {"kcal": 149, "protein": 6.4, "fat": 0.5, "carbs": 33, "fiber": 2.1, "salt": 0.02},
    "olive oil":    {"kcal": 884, "protein": 0,   "fat": 100, "carbs": 0, "fiber": 0, "salt": 0},
    "spinach":      {"kcal": 23,  "protein": 2.9, "fat": 0.4, "carbs": 3.6, "fiber": 2.2, "salt": 0.1},
    "mushroom":     {"kcal": 22,  "protein": 3.1, "fat": 0.3, "carbs": 3.3, "fiber": 1, "salt": 0},
    "potato":       {"kcal": 77,  "protein": 2,   "fat": 0.1, "carbs": 17, "fiber": 2.2, "salt": 0},
    "carrot":       {"kcal": 41,  "protein": 0.9, "fat": 0.2, "carbs": 10, "fiber": 2.8, "salt": 0.1},
    "avocado":      {"kcal": 160, "protein": 2,   "fat": 15,  "carbs": 9, "fiber": 7, "salt": 0},
    "lentil":       {"kcal": 116, "protein": 9,   "fat": 0.4, "carbs": 20, "fiber": 7.9, "salt": 0},
    "chickpea":     {"kcal": 164, "protein": 8.9, "fat": 2.6, "carbs": 27, "fiber": 7.6, "salt": 0.1},
    "coconut milk": {"kcal": 197, "protein": 2,   "fat": 21,  "carbs": 3, "fiber": 0, "salt": 0.1},
    "soy sauce":    {"kcal": 53,  "protein": 5.6, "fat": 0.1, "carbs": 5, "fiber": 0, "salt": 5.7},
    "pasta":        {"kcal": 138, "protein": 4.5, "fat": 0.6, "carbs": 28, "fiber": 1.8, "salt": 0},
    "bread":        {"kcal": 265, "protein": 9,   "fat": 3.2, "carbs": 49, "fiber": 2.7, "salt": 0.6},
}


def estimate_nutrition(ingredients: list, servings: int, default_servings: int) -> dict:
    total = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "fiber": 0.0, "salt": 0.0}
    unit_to_grams = {
        "g": 1, "ml": 1, "kg": 1000, "l": 1000,
        "tbsp": 15, "tsp": 5, "pcs": 100, "cloves": 5,
        "leaves": 2, "slices": 30, "cups": 240,
    }
    for ing in ingredients:
        grams = ing.get("amount", 0) * unit_to_grams.get(ing.get("unit", "pcs"), 10)
        name = ing.get("name", "").lower()
        nutrition = next((v for k, v in NUTRITION_DB.items() if k in name), None)
        if nutrition:
            factor = grams / 100
            for key in total:
                total[key] += nutrition.get(key, 0) * factor
    scale = servings / max(default_servings, 1)
    return {k: round(v * scale, 1) for k, v in total.items()}


def _get_openai_client():
    if not _openai_available or not OPENAI_KEY:
        return None
    return OpenAI(api_key=OPENAI_KEY)


def analyze_photo_with_openai(image_bytes: bytes) -> list[str]:
    """Use GPT-4 Vision to identify ingredients from a fridge photo."""
    client = _get_openai_client()
    if not client:
        return []
    b64 = base64.b64encode(image_bytes).decode()
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": (
                        "Look at this fridge/kitchen photo and list all visible food ingredients. "
                        "Return ONLY a JSON array of ingredient names in English, e.g. [\"chicken\", \"milk\", \"eggs\"]. "
                        "No explanation, just the JSON array."
                    )},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }],
            max_tokens=200,
        )
        text = resp.choices[0].message.content.strip()
        # Strip code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        return [str(x).strip() for x in parsed if x]
    except Exception as e:
        st.error(f"Vision-Analyse fehlgeschlagen: {e}")
        return []


def search_spoonacular(ingredients: list[str], number: int = 6) -> list[dict]:
    """Search Spoonacular for recipes by ingredients."""
    if not SPOONACULAR_KEY:
        return []
    try:
        ing_str = ",".join(ingredients)
        resp = requests.get(
            "https://api.spoonacular.com/recipes/findByIngredients",
            params={
                "ingredients": ing_str,
                "number": number,
                "ranking": 1,
                "ignorePantry": True,
                "apiKey": SPOONACULAR_KEY,
            },
            timeout=8,
        )
        if resp.status_code == 402:
            return []  # quota exceeded
        resp.raise_for_status()
        recipes_basic = resp.json()

        # Fetch full details with nutrition
        ids = [str(r["id"]) for r in recipes_basic]
        if not ids:
            return []
        bulk = requests.get(
            "https://api.spoonacular.com/recipes/informationBulk",
            params={"ids": ",".join(ids), "includeNutrition": True, "apiKey": SPOONACULAR_KEY},
            timeout=10,
        )
        bulk.raise_for_status()
        details = {str(r["id"]): r for r in bulk.json()}

        results = []
        for basic in recipes_basic:
            detail = details.get(str(basic["id"]), {})
            used_ings = [i["name"] for i in basic.get("usedIngredients", [])]
            total_ings = used_ings + [i["name"] for i in basic.get("missedIngredients", [])]

            nutrition = detail.get("nutrition", {})
            nutrients = {n["name"]: n["amount"] for n in nutrition.get("nutrients", [])}

            # Build ingredient list
            ing_list = []
            for ing in detail.get("extendedIngredients", []):
                ing_list.append({
                    "name": ing.get("name", ""),
                    "amount": ing.get("amount", 1),
                    "unit": ing.get("unit", "pcs"),
                })

            steps = []
            for a in detail.get("analyzedInstructions", []):
                for s in a.get("steps", []):
                    steps.append(s.get("step", ""))

            results.append({
                "id": f"sp_{basic['id']}",
                "name": detail.get("title", basic.get("title", "")),
                "image": detail.get("image", DEFAULT_IMAGE),
                "cuisine": (detail.get("cuisines") or ["International"])[0],
                "difficulty": _guess_difficulty(detail.get("readyInMinutes", 30)),
                "prepTime": detail.get("readyInMinutes", 30),
                "servings": detail.get("servings", 2),
                "tags": _build_tags(detail),
                "ingredients": ing_list,
                "steps": steps,
                "nutrition_per_serving": {
                    "kcal": round(nutrients.get("Calories", 0)),
                    "protein": round(nutrients.get("Protein", 0), 1),
                    "fat": round(nutrients.get("Fat", 0), 1),
                    "carbs": round(nutrients.get("Carbohydrates", 0), 1),
                    "fiber": round(nutrients.get("Fiber", 0), 1),
                    "salt": round(nutrients.get("Sodium", 0) / 1000, 2),
                },
                "_used_ings": used_ings,
                "_total_ings": total_ings,
                "_match_score": len(used_ings) / max(len(total_ings), 1),
            })
        return results
    except requests.exceptions.ConnectionError:
        st.warning(f"⚠️ {t('no_internet')}")
        return []
    except Exception as e:
        st.warning(f"Spoonacular-Fehler: {e}")
        return []


def _guess_difficulty(minutes: int) -> str:
    if minutes <= 20:
        return "Easy"
    elif minutes <= 45:
        return "Medium"
    return "Hard"


def _build_tags(detail: dict) -> list:
    tags = []
    if detail.get("vegetarian"):
        tags.append("Vegetarian")
    if detail.get("vegan"):
        tags.append("Vegan")
    if detail.get("glutenFree"):
        tags.append("Gluten-free")
    if detail.get("dairyFree"):
        tags.append("Dairy-free")
    return tags


def generate_openai_recipes(ingredients: list[str], staples_enabled: bool, count: int = 3) -> list[dict]:
    """Generate recipes via OpenAI with caching."""
    client = _get_openai_client()
    if not client:
        return []

    # Check cache
    cache_key = hashlib.sha256(",".join(sorted(ingredients)).encode()).hexdigest()
    db = get_db()
    try:
        cached = db.query(AIRecipeCache).filter(
            AIRecipeCache.ingredients_hash == cache_key
        ).first()
        if cached:
            return json.loads(cached.recipe_json)
    finally:
        db.close()

    pantry_note = (
        "Standard seasonings (salt, pepper, oil) may be used."
        if staples_enabled
        else "Use only listed ingredients."
    )
    prompt = f"""Create {count} recipes using mainly: {', '.join(ingredients)}.
{pantry_note}
Return ONLY a valid JSON array. Each object must have:
- name (string), prepTime (int minutes), difficulty ("Easy"|"Medium"|"Hard")
- cuisine (string), tags (array of strings), servings (int)
- ingredients: array of {{name, amount (number), unit (string)}}
- instructions: array of step strings
- image (URL, optional)
No markdown, no code fences. Pure JSON."""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return only valid JSON arrays."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            return []

        recipes = []
        for raw in parsed:
            if not isinstance(raw, dict):
                continue
            rid = f"ai_{uuid.uuid4().hex[:8]}"
            recipes.append({
                "id": rid,
                "name": raw.get("name", "AI Recipe"),
                "image": raw.get("image", DEFAULT_IMAGE),
                "cuisine": raw.get("cuisine", "International"),
                "difficulty": raw.get("difficulty", "Medium"),
                "prepTime": max(int(raw.get("prepTime", 20)), 1),
                "servings": max(int(raw.get("servings", 2)), 1),
                "tags": raw.get("tags", []),
                "ingredients": [
                    {"name": str(i.get("name", "")), "amount": float(i.get("amount", 1)), "unit": str(i.get("unit", "pcs"))}
                    for i in raw.get("ingredients", []) if isinstance(i, dict)
                ],
                "steps": [str(s) for s in raw.get("instructions", []) if s],
            })

        # Cache result
        db = get_db()
        try:
            entry = AIRecipeCache(
                id=str(uuid.uuid4()),
                ingredients_hash=cache_key,
                recipe_json=json.dumps(recipes),
            )
            db.add(entry)
            db.commit()
        finally:
            db.close()

        return recipes
    except Exception as e:
        st.error(f"KI-Generierung fehlgeschlagen: {e}")
        return []


def is_available(ing_name: str, user_ings: list[str]) -> bool:
    name = ing_name.lower()
    return any(u in name or name in u for u in [x.lower() for x in user_ings])


def render_search_page():
    """Main search page rendering."""
    st.subheader(t("search_title"))

    # ── Ingredient Input ─────────────────────────────────────────
    col1, col2 = st.columns([4, 1])
    with col1:
        new_ing = st.text_input(
            t("search_placeholder"),
            key="new_ingredient_input",
            label_visibility="collapsed",
            placeholder=t("search_placeholder"),
        )
    with col2:
        add_pressed = st.button(t("add_ingredient"), use_container_width=True)

    if add_pressed and new_ing.strip():
        ings = st.session_state.get("selected_ingredients", [])
        if new_ing.strip() not in ings:
            ings.append(new_ing.strip())
            st.session_state.selected_ingredients = ings
        st.rerun()

    # ── Common Ingredient Quick-Add ──────────────────────────────
    with st.expander(t("common_ingredients"), expanded=False):
        cols = st.columns(4)
        for i, ing in enumerate(COMMON_INGREDIENTS):
            selected = ing in st.session_state.get("selected_ingredients", [])
            with cols[i % 4]:
                if st.button(
                    f"{'✅' if selected else '+'} {ing}",
                    key=f"quick_{ing}",
                    use_container_width=True,
                ):
                    ings = st.session_state.get("selected_ingredients", [])
                    if selected:
                        ings.remove(ing)
                    else:
                        ings.append(ing)
                    st.session_state.selected_ingredients = ings
                    st.rerun()

    # ── Photo Upload ─────────────────────────────────────────────
    with st.expander(t("upload_photo"), expanded=False):
        uploaded = st.file_uploader(
            t("photo_hint"),
            type=["jpg", "jpeg", "png", "webp"],
            key="fridge_photo",
        )
        if uploaded:
            st.image(uploaded, width=200)
            if st.button(t("analyzing_photo"), key="analyze_photo"):
                with st.spinner(t("analyzing_photo")):
                    detected = analyze_photo_with_openai(uploaded.read())
                if detected:
                    ings = st.session_state.get("selected_ingredients", [])
                    added = 0
                    for ing in detected:
                        if ing not in ings:
                            ings.append(ing)
                            added += 1
                    st.session_state.selected_ingredients = ings
                    st.success(f"{added} Zutaten erkannt und hinzugefügt!")
                    st.rerun()
                else:
                    st.warning("Keine Zutaten erkannt. Bitte Text-Suche verwenden.")

    # ── Selected Ingredients ─────────────────────────────────────
    selected = st.session_state.get("selected_ingredients", [])
    if selected:
        st.markdown(f"**{t('your_ingredients')}** ({len(selected)})")
        pill_html = ""
        for ing in selected:
            pill_html += f'<span class="fc-pill">{ing} </span>'
        st.markdown(pill_html, unsafe_allow_html=True)

        cols = st.columns(len(selected) + 1)
        for i, ing in enumerate(selected):
            with cols[i]:
                if st.button("✕", key=f"rem_{ing}", help=f"{t('remove')} {ing}"):
                    selected.remove(ing)
                    st.session_state.selected_ingredients = selected
                    st.rerun()
        with cols[-1]:
            if st.button(t("clear_all"), key="clear_ings"):
                st.session_state.selected_ingredients = []
                st.rerun()

    # ── Staples ──────────────────────────────────────────────────
    staples_on = st.checkbox(
        t("staples_enabled"),
        value=st.session_state.get("staples_enabled", True),
        key="staples_toggle",
    )
    st.session_state.staples_enabled = staples_on

    st.divider()

    # ── Search / Generate buttons ────────────────────────────────
    if not selected:
        st.info(t("no_ingredients"))
        return

    col_search, col_ai = st.columns(2)
    with col_search:
        search_btn = st.button(t("find_recipes"), use_container_width=True, type="primary", key="btn_search")
    with col_ai:
        ai_btn = st.button(t("ai_recipes"), use_container_width=True, key="btn_ai")

    if search_btn:
        _do_spoonacular_search(selected)
    elif ai_btn:
        _do_ai_search(selected, staples_on)

    # ── Results ──────────────────────────────────────────────────
    results = st.session_state.get("search_results", [])
    if results:
        st.markdown(f"**{t('results_found', n=len(results))}**")
        for i, recipe in enumerate(results):
            score = recipe.get("_match_score", 1.0)
            with st.container():
                clicked = render_recipe_card(recipe, match_pct=score, key_prefix=f"r{i}")
                if clicked:
                    st.session_state.current_recipe = recipe
                    st.session_state.page = "recipe_detail"
                    st.rerun()
            st.divider()
    elif st.session_state.get("search_done"):
        render_empty_state("🔍", t("no_results"), "Versuche andere Zutaten oder KI-Rezepte.")


def _do_spoonacular_search(ingredients: list):
    with st.spinner(t("loading")):
        results = search_spoonacular(ingredients, number=6)
    if not results:
        # Fallback: local matching (if recipes.py exists)
        try:
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from recipes import RECIPES
            sys.path.pop(0)
            results = _local_search(ingredients, RECIPES)
        except ImportError:
            pass
    st.session_state.search_results = results
    st.session_state.search_done = True
    st.rerun()


def _do_ai_search(ingredients: list, staples_on: bool):
    if not OPENAI_KEY:
        st.error(t("ai_unavailable"))
        return
    with st.spinner(t("generating_ai")):
        results = generate_openai_recipes(ingredients, staples_on, count=3)
    if results:
        for r in results:
            r["_match_score"] = 1.0
    st.session_state.search_results = results
    st.session_state.search_done = True
    st.rerun()


def _local_search(selected: list, recipes: list) -> list:
    """Simple local recipe matching as fallback."""
    user_ings = [x.lower() for x in selected]
    results = []
    for recipe in recipes:
        recipe_ings = [i["name"].lower() for i in recipe.get("ingredients", [])]
        matched = sum(1 for ri in recipe_ings if any(u in ri or ri in u for u in user_ings))
        if matched > 0:
            total = max(len(recipe_ings), 1)
            results.append({**recipe, "_match_score": matched / total})
    return sorted(results, key=lambda x: x["_match_score"], reverse=True)


def render_recipe_detail(recipe: dict, user_ings: list = None):
    """Full recipe detail view with servings slider."""
    if user_ings is None:
        user_ings = st.session_state.get("selected_ingredients", [])
        if st.session_state.get("staples_enabled"):
            user_ings = user_ings + STAPLE_INGREDIENTS

    if st.button(t("back_to_results"), key="back_btn"):
        st.session_state.page = "search"
        st.session_state.current_recipe = None
        st.rerun()

    name = recipe.get("name", "Rezept")
    image = recipe.get("image", DEFAULT_IMAGE)
    cuisine = recipe.get("cuisine", "")
    difficulty = recipe.get("difficulty", "Medium")
    prep_time = recipe.get("prepTime", 0)
    default_servings = recipe.get("servings", 2)
    steps = recipe.get("steps") or recipe.get("instructions", [])
    ingredients = recipe.get("ingredients", [])
    tags = recipe.get("tags", [])

    # Image + title
    col_img, col_info = st.columns([2, 3])
    with col_img:
        if image:
            st.image(image, use_container_width=True)
    with col_info:
        st.title(name)
        st.caption(f"🌍 {cuisine}  |  ⏱ {prep_time} {t('minutes')}  |  📊 {t(difficulty)}")
        for tag in tags:
            st.badge(tag)

    st.divider()

    # Servings slider
    servings = st.slider(
        t("servings_slider"),
        min_value=1,
        max_value=12,
        value=default_servings,
        key=f"servings_{recipe.get('id', 'r')}",
    )
    scale = servings / max(default_servings, 1)

    # Ingredients
    render_section_title(t("ingredients"))
    missing_ings = []
    cols = st.columns(2)
    for i, ing in enumerate(ingredients):
        available = is_available(ing["name"], user_ings)
        if not available:
            missing_ings.append(ing)
        scaled_amount = round(ing.get("amount", 0) * scale, 1)
        label = f"{scaled_amount} {ing.get('unit', '')} {ing['name']}"
        with cols[i % 2]:
            if available:
                st.markdown(f"✅ {label}")
            else:
                st.markdown(f"<span style='color:#E53935'>❌ {label}</span>", unsafe_allow_html=True)

    # Shopping + Cookbook buttons
    user_id = st.session_state.get("current_user_id")
    if user_id:
        col_shop, col_book, col_log = st.columns(3)
        with col_shop:
            if missing_ings:
                if st.button(t("add_missing_to_shopping"), key="add_to_shop", use_container_width=True):
                    _add_to_shopping(user_id, recipe, missing_ings)
                    st.success(f"{len(missing_ings)} Zutaten hinzugefügt!")
            else:
                st.info(t("all_ingredients_available"))
        with col_book:
            if st.button(t("save_to_cookbook"), key="save_cookbook", use_container_width=True):
                _save_to_cookbook(user_id, recipe)
        with col_log:
            if st.button(t("log_meal"), key="log_meal_btn", use_container_width=True):
                _log_meal(user_id, recipe, servings, default_servings, ingredients)

    st.divider()

    # Instructions
    render_section_title(t("instructions"))
    if steps:
        for i, step in enumerate(steps, 1):
            st.markdown(f"**{i}.** {step}")
    else:
        st.info("Keine Schritt-für-Schritt Anleitung verfügbar.")

    st.divider()

    # Nutrition
    render_section_title(t("nutrition"))
    if "nutrition_per_serving" in recipe:
        n = recipe["nutrition_per_serving"]
        n_scaled = {k: round(v * scale, 1) for k, v in n.items()}
        st.caption(f"_{t('per_serving')} ({servings} {t('servings')}):_")
        render_nutrition_table(n_scaled)
    else:
        nutrition = estimate_nutrition(ingredients, servings, default_servings)
        st.caption(f"_{t('per_serving')} (geschätzt):_")
        render_nutrition_table(nutrition)


def _add_to_shopping(user_id: str, recipe: dict, missing: list):
    db = get_db()
    try:
        for ing in missing:
            item = ShoppingListItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                ingredient_name=ing["name"],
                amount=ing.get("amount", 0),
                unit=ing.get("unit", ""),
                recipe_id=recipe.get("id", ""),
                recipe_name=recipe.get("name", ""),
            )
            db.add(item)
        db.commit()
        # Update badge
        count = db.query(ShoppingListItem).filter(
            ShoppingListItem.user_id == user_id,
            ShoppingListItem.is_completed == False,
        ).count()
        st.session_state.shopping_badge = count
    finally:
        db.close()


def _save_to_cookbook(user_id: str, recipe: dict):
    db = get_db()
    try:
        existing = db.query(SavedRecipe).filter(
            SavedRecipe.user_id == user_id,
            SavedRecipe.recipe_json.contains(recipe.get("id", "NOID")),
        ).first()
        if existing:
            st.info(t("already_saved"))
        else:
            entry = SavedRecipe(
                id=str(uuid.uuid4()),
                user_id=user_id,
                recipe_json=json.dumps(recipe),
            )
            db.add(entry)
            db.commit()
            st.success(t("saved_to_cookbook"))
    finally:
        db.close()


def _log_meal(user_id: str, recipe: dict, servings: int, default_servings: int, ingredients: list):
    from database import TrackerEntry
    db = get_db()
    try:
        nutrition = estimate_nutrition(ingredients, servings, default_servings)
        entry = TrackerEntry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            recipe_id=recipe.get("id", ""),
            recipe_name=recipe.get("name", ""),
            servings=servings,
            kcal=nutrition["kcal"],
            protein=nutrition["protein"],
            fat=nutrition["fat"],
            carbs=nutrition["carbs"],
        )
        db.add(entry)
        db.commit()
        st.success(t("meal_logged"))
    finally:
        db.close()
