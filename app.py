from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from dotenv import load_dotenv
import os
import sqlite3
import uuid
import json
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from recipes import RECIPES, COMMON_INGREDIENTS, STAPLE_INGREDIENTS

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fridgechef-local-secret-2026")

DB_PATH = os.path.join(os.path.dirname(__file__), "fridgechef.db")
DEFAULT_RECIPE_IMAGE = (
    "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600&h=400&fit=crop"
)
AI_GENERATED_RECIPES = {}

client = None
if OpenAI and os.environ.get("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS favorites (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                recipe_id TEXT NOT NULL,
                recipe TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, recipe_id)
            );
            CREATE TABLE IF NOT EXISTS shopping_items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                amount REAL,
                unit TEXT,
                recipe_id TEXT,
                recipe_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS meal_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                recipe_id TEXT NOT NULL,
                recipe_name TEXT NOT NULL,
                servings INTEGER,
                kcal REAL,
                protein REAL,
                fat REAL,
                carbs REAL,
                eaten_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


init_db()


class User:
    def __init__(self, row):
        self.id = row["id"]
        self.email = row["email"]
        self.display_name = row["display_name"]


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(row) if row else None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Bitte zuerst einloggen.", "warning")
            return redirect(url_for("auth"))
        return f(*args, **kwargs)
    return decorated


def match_recipes(selected, staples, staples_enabled, filters):
    all_ingredients = [i.lower() for i in selected]
    if staples_enabled:
        all_ingredients += [s.lower() for s in staples]

    results = []
    for recipe in RECIPES:
        recipe_ing_names = [ing["name"].lower() for ing in recipe["ingredients"]]

        matched = 0
        for ing_name in recipe_ing_names:
            for user_ing in all_ingredients:
                if user_ing in ing_name or ing_name in user_ing:
                    matched += 1
                    break

        if matched == 0:
            continue

        tags = recipe.get("tags", [])
        if filters.get("vegetarian") and "vegetarian" not in tags:
            continue
        if filters.get("vegan") and "vegan" not in tags:
            continue
        if filters.get("glutenFree") and "glutenFree" not in tags:
            continue
        if filters.get("lactoseFree") and "lactoseFree" not in tags:
            continue
        max_time = filters.get("maxPrepTime")
        if max_time and recipe["prepTime"] > int(max_time):
            continue
        difficulty = filters.get("difficulty")
        if difficulty and recipe["difficulty"] != difficulty:
            continue
        cuisine = filters.get("cuisine")
        if cuisine and recipe["cuisine"] != cuisine:
            continue

        total = len(recipe_ing_names)
        results.append({
            "recipe": recipe,
            "matched": matched,
            "total": total,
            "score": matched / total,
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)


def get_recipe_by_id(recipe_id):
    recipe = next((r for r in RECIPES if r["id"] == recipe_id), None)
    if recipe:
        return recipe
    return AI_GENERATED_RECIPES.get(recipe_id)


def normalize_ai_recipe(raw_recipe):
    ingredients = []
    for ing in raw_recipe.get("ingredients", []):
        if not isinstance(ing, dict):
            continue
        amount = ing.get("amount", 1)
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 1
        ingredients.append({
            "name": str(ing.get("name", "Unknown ingredient")).strip() or "Unknown ingredient",
            "amount": amount,
            "unit": str(ing.get("unit", "pcs")).strip() or "pcs",
        })

    steps = raw_recipe.get("steps") or raw_recipe.get("instructions") or []
    if not isinstance(steps, list):
        steps = [str(steps)]
    steps = [str(step).strip() for step in steps if str(step).strip()]

    tags = raw_recipe.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    tags = [str(tag).strip() for tag in tags if str(tag).strip()]

    prep_time = raw_recipe.get("prepTime", 20)
    servings = raw_recipe.get("servings", 2)
    try:
        prep_time = int(prep_time)
    except (TypeError, ValueError):
        prep_time = 20
    try:
        servings = int(servings)
    except (TypeError, ValueError):
        servings = 2

    steps_list = steps or ["No steps available."]
    return {
        "id": f"ai_{uuid.uuid4().hex[:8]}",
        "name": str(raw_recipe.get("name", "AI Recipe")).strip() or "AI Recipe",
        "image": str(raw_recipe.get("image", DEFAULT_RECIPE_IMAGE)).strip() or DEFAULT_RECIPE_IMAGE,
        "cuisine": str(raw_recipe.get("cuisine", "International")).strip() or "International",
        "difficulty": str(raw_recipe.get("difficulty", "Medium")).strip() or "Medium",
        "prepTime": max(prep_time, 1),
        "servings": max(servings, 1),
        "tags": tags,
        "ingredients": ingredients,
        "steps": steps_list,
        "instructions": steps_list,
    }


def generate_ai_recipes(ingredients, staples_enabled, count=2):
    if not client:
        return []

    ingredients_text = ", ".join(ingredients)
    pantry_note = (
        "Standard seasonings (salt, pepper, oil) may be used."
        if staples_enabled
        else "Use only the listed ingredients; do not assume extra pantry staples."
    )
    prompt = f"""
You are a Michelin-star chef. Create {count} creative recipes that mainly use these ingredients: {ingredients_text}.
{pantry_note}

Answer ONLY with a valid JSON array. No markdown formatting, no code fences. Raw JSON only.
Each object must have:
- name (English recipe title)
- prepTime (integer, minutes)
- difficulty: one of "Easy", "Medium", "Hard"
- cuisine (string)
- tags: array of short strings (e.g. "Vegetarian", "Quick lunch")
- servings (integer)
- ingredients: array of objects with name (string), amount (number), unit (string)
- instructions: array of step strings in English
Optional: image (URL string). If omitted, a default image will be used.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        response_text = (response.choices[0].message.content or "").strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        parsed = json.loads(response_text.strip())
        if not isinstance(parsed, list):
            return []

        normalized_recipes = []
        for raw_recipe in parsed:
            if not isinstance(raw_recipe, dict):
                continue
            recipe = normalize_ai_recipe(raw_recipe)
            AI_GENERATED_RECIPES[recipe["id"]] = recipe
            normalized_recipes.append(recipe)

        return normalized_recipes
    except Exception as e:
        print(f"Fehler bei der KI-Generierung: {e}")
        return []


NUTRITION_DB = {
    "chicken":      {"kcal": 165, "protein": 31,  "fat": 3.6, "carbs": 0},
    "beef":         {"kcal": 250, "protein": 26,  "fat": 15,  "carbs": 0},
    "pork":         {"kcal": 242, "protein": 27,  "fat": 14,  "carbs": 0},
    "salmon":       {"kcal": 208, "protein": 20,  "fat": 13,  "carbs": 0},
    "shrimp":       {"kcal": 85,  "protein": 18,  "fat": 1,   "carbs": 0},
    "tofu":         {"kcal": 76,  "protein": 8,   "fat": 4.5, "carbs": 2},
    "rice":         {"kcal": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
    "pasta":        {"kcal": 157, "protein": 5.8, "fat": 0.9, "carbs": 31},
    "flour":        {"kcal": 364, "protein": 10,  "fat": 1,   "carbs": 76},
    "egg":          {"kcal": 155, "protein": 13,  "fat": 11,  "carbs": 1.1},
    "milk":         {"kcal": 61,  "protein": 3.2, "fat": 3.3, "carbs": 4.8},
    "butter":       {"kcal": 717, "protein": 0.9, "fat": 81,  "carbs": 0.1},
    "cheese":       {"kcal": 400, "protein": 25,  "fat": 33,  "carbs": 1.3},
    "tomato":       {"kcal": 18,  "protein": 0.9, "fat": 0.2, "carbs": 3.9},
    "onion":        {"kcal": 40,  "protein": 1.1, "fat": 0.1, "carbs": 9.3},
    "garlic":       {"kcal": 149, "protein": 6.4, "fat": 0.5, "carbs": 33},
    "olive oil":    {"kcal": 884, "protein": 0,   "fat": 100, "carbs": 0},
    "spinach":      {"kcal": 23,  "protein": 2.9, "fat": 0.4, "carbs": 3.6},
    "mushroom":     {"kcal": 22,  "protein": 3.1, "fat": 0.3, "carbs": 3.3},
    "potato":       {"kcal": 77,  "protein": 2,   "fat": 0.1, "carbs": 17},
    "carrot":       {"kcal": 41,  "protein": 0.9, "fat": 0.2, "carbs": 10},
    "avocado":      {"kcal": 160, "protein": 2,   "fat": 15,  "carbs": 9},
    "lentil":       {"kcal": 116, "protein": 9,   "fat": 0.4, "carbs": 20},
    "chickpea":     {"kcal": 164, "protein": 8.9, "fat": 2.6, "carbs": 27},
    "black bean":   {"kcal": 132, "protein": 8.9, "fat": 0.5, "carbs": 24},
    "coconut milk": {"kcal": 197, "protein": 2,   "fat": 21,  "carbs": 3},
    "soy sauce":    {"kcal": 53,  "protein": 5.6, "fat": 0.1, "carbs": 5},
    "noodle":       {"kcal": 138, "protein": 4.5, "fat": 0.6, "carbs": 28},
    "bread":        {"kcal": 265, "protein": 9,   "fat": 3.2, "carbs": 49},
    "peanut":       {"kcal": 567, "protein": 26,  "fat": 49,  "carbs": 16},
}


def estimate_nutrition(ingredients, servings, default_servings):
    total = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    unit_to_grams = {"g": 1, "ml": 1, "kg": 1000, "tbsp": 15, "tsp": 5,
                     "pcs": 100, "cloves": 5, "leaves": 2, "slices": 30}
    for ing in ingredients:
        grams = ing["amount"] * unit_to_grams.get(ing["unit"], 10)
        name = ing["name"].lower()
        nutrition = next((v for k, v in NUTRITION_DB.items() if k in name), None)
        if nutrition:
            factor = grams / 100
            for key in total:
                total[key] += nutrition[key] * factor

    scale = servings / default_servings if default_servings else 1
    return {k: round(v * scale) for k, v in total.items()}


def is_ingredient_available(ing_name, all_ingredients):
    name_lower = ing_name.lower()
    return any(u in name_lower or name_lower in u for u in all_ingredients)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    user = get_current_user()
    selected = session.get("selected_ingredients", [])
    active_staples = session.get("staples", list(STAPLE_INGREDIENTS))
    staples_enabled = session.get("staples_enabled", True)
    return render_template("index.html",
        user=user,
        selected=selected,
        common_ingredients=COMMON_INGREDIENTS,
        staple_ingredients=STAPLE_INGREDIENTS,
        active_staples=active_staples,
        staples_enabled=staples_enabled,
    )


@app.route("/add_ingredient", methods=["POST"])
def add_ingredient():
    ingredient = request.form.get("ingredient", "").strip()
    if ingredient:
        selected = session.get("selected_ingredients", [])
        if ingredient not in selected:
            selected.append(ingredient)
            session["selected_ingredients"] = selected
    return redirect(url_for("index"))


@app.route("/remove_ingredient/<path:ingredient>")
def remove_ingredient(ingredient):
    selected = session.get("selected_ingredients", [])
    session["selected_ingredients"] = [i for i in selected if i != ingredient]
    return redirect(url_for("index"))


@app.route("/clear_ingredients")
def clear_ingredients():
    session["selected_ingredients"] = []
    return redirect(url_for("index"))


@app.route("/toggle_staple/<path:staple>")
def toggle_staple(staple):
    staples = session.get("staples", list(STAPLE_INGREDIENTS))
    if staple in staples:
        staples.remove(staple)
    else:
        staples.append(staple)
    session["staples"] = staples
    return redirect(url_for("index"))


@app.route("/toggle_staples_enabled", methods=["POST"])
def toggle_staples_enabled():
    session["staples_enabled"] = not session.get("staples_enabled", True)
    return redirect(url_for("index"))


@app.route("/results")
def results():
    user = get_current_user()
    selected = session.get("selected_ingredients", [])
    if not selected:
        flash("Bitte zuerst Zutaten auswählen.", "info")
        return redirect(url_for("index"))

    active_staples = session.get("staples", list(STAPLE_INGREDIENTS))
    staples_enabled = session.get("staples_enabled", True)

    filters = {
        "vegetarian":  "vegetarian"  in request.args,
        "vegan":       "vegan"       in request.args,
        "glutenFree":  "glutenFree"  in request.args,
        "lactoseFree": "lactoseFree" in request.args,
        "maxPrepTime": request.args.get("maxPrepTime") or None,
        "difficulty":  request.args.get("difficulty")  or None,
        "cuisine":     request.args.get("cuisine")     or None,
    }
    sort_by = request.args.get("sort", "match")

    matched = match_recipes(selected, active_staples, staples_enabled, filters)

    if sort_by == "time":
        matched.sort(key=lambda x: x["recipe"]["prepTime"])
    elif sort_by == "difficulty":
        order = {"Easy": 0, "Medium": 1, "Hard": 2}
        matched.sort(key=lambda x: order.get(x["recipe"]["difficulty"], 1))

    cuisines = sorted(set(r["cuisine"] for r in RECIPES))
    return render_template("results.html",
        user=user,
        results=matched,
        selected=selected,
        sort_by=sort_by,
        filters=filters,
        cuisines=cuisines,
        is_ai=False,
    )


@app.route("/ai_results")
@login_required
def ai_results():
    user = get_current_user()
    selected = session.get("selected_ingredients", [])
    if not selected:
        flash("Bitte zuerst Zutaten hinzufügen.", "info")
        return redirect(url_for("index"))

    if not client:
        flash("KI ist nicht verfügbar. Bitte OPENAI_API_KEY setzen und `pip install openai`.", "danger")
        return redirect(url_for("index"))

    staples_enabled = session.get("staples_enabled", True)
    ai_recipes = generate_ai_recipes(selected, staples_enabled, count=2)
    if not ai_recipes:
        flash("Fehler bei der Rezept-Generierung. Versuche es erneut.", "danger")
        return redirect(url_for("index"))

    results_data = []
    for recipe in ai_recipes:
        total = len(recipe.get("ingredients", []))
        results_data.append({
            "recipe": recipe,
            "matched": total,
            "total": total,
            "score": 1.0 if total else 0,
        })

    filters = {
        "vegetarian": False,
        "vegan": False,
        "glutenFree": False,
        "lactoseFree": False,
        "maxPrepTime": None,
        "difficulty": None,
        "cuisine": None,
    }
    cuisines = sorted({r.get("cuisine", "International") for r in ai_recipes})
    return render_template(
        "results.html",
        user=user,
        results=results_data,
        selected=selected,
        sort_by="match",
        filters=filters,
        cuisines=cuisines,
        is_ai=True,
    )


@app.route("/recipe/<recipe_id>")
def recipe_detail(recipe_id):
    user = get_current_user()
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return render_template("404.html", user=user), 404

    selected = session.get("selected_ingredients", [])
    active_staples = session.get("staples", list(STAPLE_INGREDIENTS))
    staples_enabled = session.get("staples_enabled", True)

    all_ingredients = [i.lower() for i in selected]
    if staples_enabled:
        all_ingredients += [s.lower() for s in active_staples]

    ingredients_status = [
        {"ing": ing, "available": is_ingredient_available(ing["name"], all_ingredients)}
        for ing in recipe["ingredients"]
    ]
    missing_count = sum(1 for i in ingredients_status if not i["available"])
    matched_count = len(recipe["ingredients"]) - missing_count

    is_favorite = False
    if user:
        with get_db() as conn:
            row = conn.execute(
                "SELECT id FROM favorites WHERE user_id = ? AND recipe_id = ?",
                (user.id, recipe_id)
            ).fetchone()
            is_favorite = row is not None

    default_srv = recipe.get("servings") or 1
    nutrition = estimate_nutrition(
        recipe["ingredients"], 1, default_srv
    )

    return render_template("recipe_detail.html",
        user=user,
        recipe=recipe,
        ingredients_status=ingredients_status,
        missing_count=missing_count,
        matched_count=matched_count,
        is_favorite=is_favorite,
        nutrition=nutrition,
    )


@app.route("/toggle_favorite/<recipe_id>", methods=["POST"])
@login_required
def toggle_favorite(recipe_id):
    user = get_current_user()
    recipe = get_recipe_by_id(recipe_id)

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (user.id, recipe_id)
        ).fetchone()
        if existing:
            conn.execute(
                "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
                (user.id, recipe_id)
            )
            flash("Rezept aus dem Kochbuch entfernt.", "info")
        elif recipe:
            conn.execute(
                "INSERT INTO favorites (id, user_id, recipe_id, recipe) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), user.id, recipe_id, json.dumps(recipe))
            )
            flash("Rezept zum Kochbuch hinzugefügt!", "success")

    return redirect(url_for("recipe_detail", recipe_id=recipe_id))


@app.route("/cookbook")
@login_required
def cookbook():
    user = get_current_user()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT recipe, recipe_id FROM favorites WHERE user_id = ? ORDER BY created_at",
            (user.id,)
        ).fetchall()
    favorites = [{"recipe": json.loads(row["recipe"]), "recipe_id": row["recipe_id"]} for row in rows]
    return render_template("cookbook.html", user=user, favorites=favorites)


@app.route("/remove_favorite/<recipe_id>", methods=["POST"])
@login_required
def remove_favorite(recipe_id):
    user = get_current_user()
    with get_db() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (user.id, recipe_id)
        )
    flash("Rezept entfernt.", "info")
    return redirect(url_for("cookbook"))


@app.route("/shopping_list")
@login_required
def shopping_list():
    user = get_current_user()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM shopping_items WHERE user_id = ? ORDER BY created_at",
            (user.id,)
        ).fetchall()
    items = [dict(row) for row in rows]

    grouped = {}
    for item in items:
        key = item["recipe_name"]
        grouped.setdefault(key, []).append(item)

    return render_template("shopping_list.html",
        user=user,
        grouped=grouped,
        total=len(items),
    )


@app.route("/add_to_shopping/<recipe_id>", methods=["POST"])
@login_required
def add_to_shopping(recipe_id):
    user = get_current_user()
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return redirect(url_for("index"))

    selected = session.get("selected_ingredients", [])
    active_staples = session.get("staples", list(STAPLE_INGREDIENTS))
    staples_enabled = session.get("staples_enabled", True)
    all_ingredients = [i.lower() for i in selected]
    if staples_enabled:
        all_ingredients += [s.lower() for s in active_staples]

    missing = [ing for ing in recipe["ingredients"]
               if not is_ingredient_available(ing["name"], all_ingredients)]

    if missing:
        with get_db() as conn:
            conn.executemany(
                "INSERT INTO shopping_items (id, user_id, name, amount, unit, recipe_id, recipe_name) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(str(uuid.uuid4()), user.id, ing["name"], ing["amount"],
                  ing["unit"], recipe_id, recipe["name"]) for ing in missing]
            )
        flash(f"{len(missing)} fehlende Zutat(en) zur Einkaufsliste hinzugefügt.", "success")
    else:
        flash("Du hast bereits alle Zutaten!", "info")

    return redirect(url_for("recipe_detail", recipe_id=recipe_id))


@app.route("/remove_shopping_item/<item_id>", methods=["POST"])
@login_required
def remove_shopping_item(item_id):
    user = get_current_user()
    with get_db() as conn:
        conn.execute(
            "DELETE FROM shopping_items WHERE id = ? AND user_id = ?",
            (item_id, user.id)
        )
    return redirect(url_for("shopping_list"))


@app.route("/clear_shopping_list", methods=["POST"])
@login_required
def clear_shopping_list():
    user = get_current_user()
    with get_db() as conn:
        conn.execute("DELETE FROM shopping_items WHERE user_id = ?", (user.id,))
    flash("Einkaufsliste geleert.", "info")
    return redirect(url_for("shopping_list"))


@app.route("/tracker")
@login_required
def tracker():
    user = get_current_user()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM meal_logs WHERE user_id = ? ORDER BY eaten_at DESC",
            (user.id,)
        ).fetchall()
    logs = [dict(row) for row in rows]

    totals = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for log in logs:
        for key in totals:
            totals[key] += float(log.get(key, 0) or 0)

    count = len(logs)
    avg = {k: round(v / count, 1) if count > 0 else 0 for k, v in totals.items()}
    totals = {k: round(v, 1) for k, v in totals.items()}

    return render_template("tracker.html",
        user=user,
        logs=logs,
        totals=totals,
        avg=avg,
        count=count,
    )


@app.route("/log_meal/<recipe_id>", methods=["POST"])
@login_required
def log_meal(recipe_id):
    user = get_current_user()
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return redirect(url_for("index"))

    servings = int(request.form.get("servings", recipe["servings"]))
    nutrition = estimate_nutrition(recipe["ingredients"], servings, recipe["servings"])

    with get_db() as conn:
        conn.execute(
            "INSERT INTO meal_logs (id, user_id, recipe_id, recipe_name, servings, kcal, protein, fat, carbs) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user.id, recipe_id, recipe["name"], servings,
             nutrition["kcal"], nutrition["protein"], nutrition["fat"], nutrition["carbs"])
        )

    flash(f"'{recipe['name']}' als gegessen markiert! ({nutrition['kcal']} kcal)", "success")
    return redirect(url_for("tracker"))


@app.route("/delete_meal/<log_id>", methods=["POST"])
@login_required
def delete_meal(log_id):
    user = get_current_user()
    with get_db() as conn:
        conn.execute(
            "DELETE FROM meal_logs WHERE id = ? AND user_id = ?",
            (log_id, user.id)
        )
    return redirect(url_for("tracker"))


@app.route("/auth", methods=["GET", "POST"])
def auth():
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Bitte E-Mail und Passwort eingeben.", "danger")
            return render_template("auth.html", user=None)

        try:
            if action == "login":
                with get_db() as conn:
                    row = conn.execute(
                        "SELECT * FROM users WHERE email = ?", (email,)
                    ).fetchone()
                if row and check_password_hash(row["password_hash"], password):
                    session["user_id"] = row["id"]
                    session.permanent = True
                    flash("Erfolgreich eingeloggt!", "success")
                    return redirect(url_for("index"))
                else:
                    flash("E-Mail oder Passwort falsch.", "danger")

            elif action == "register":
                display_name = request.form.get("display_name", "").strip()
                if len(password) < 6:
                    flash("Passwort muss mindestens 6 Zeichen lang sein.", "danger")
                    return render_template("auth.html", user=None)

                with get_db() as conn:
                    existing = conn.execute(
                        "SELECT id FROM users WHERE email = ?", (email,)
                    ).fetchone()
                    if existing:
                        flash("Diese E-Mail ist bereits registriert.", "warning")
                        return render_template("auth.html", user=None)

                    user_id = str(uuid.uuid4())
                    conn.execute(
                        "INSERT INTO users (id, email, display_name, password_hash) VALUES (?, ?, ?, ?)",
                        (user_id, email, display_name or email.split("@")[0],
                         generate_password_hash(password))
                    )

                session["user_id"] = user_id
                session.permanent = True
                flash("Willkommen bei FridgeChef! Konto erfolgreich erstellt.", "success")
                return redirect(url_for("index"))

        except Exception as e:
            flash(f"Fehler: {str(e)}", "danger")

    return render_template("auth.html", user=None)


@app.route("/logout")
def logout():
    session.clear()
    flash("Erfolgreich ausgeloggt.", "info")
    return redirect(url_for("auth"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", user=get_current_user()), 404


if __name__ == "__main__":
    app.run(debug=True, port=5001)
