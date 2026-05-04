"""
FridgeChef - UI Translations (DE / EN)
"""
import streamlit as st

TRANSLATIONS = {
    # ── App general ─────────────────────────────────────────────
    "app_title":            {"de": "FridgeChef", "en": "FridgeChef"},
    "app_tagline":          {"de": "Koche mit dem, was du hast", "en": "Cook with what you have"},
    "loading":              {"de": "Lädt…", "en": "Loading…"},
    "save":                 {"de": "Speichern", "en": "Save"},
    "cancel":               {"de": "Abbrechen", "en": "Cancel"},
    "delete":               {"de": "Löschen", "en": "Delete"},
    "edit":                 {"de": "Bearbeiten", "en": "Edit"},
    "close":                {"de": "Schließen", "en": "Close"},
    "confirm":              {"de": "Bestätigen", "en": "Confirm"},
    "yes":                  {"de": "Ja", "en": "Yes"},
    "no":                   {"de": "Nein", "en": "No"},
    "error":                {"de": "Fehler", "en": "Error"},
    "success":              {"de": "Erfolg", "en": "Success"},
    "retry":                {"de": "Erneut versuchen", "en": "Retry"},
    "no_internet":          {"de": "Keine Internetverbindung", "en": "No internet connection"},
    "export":               {"de": "Exportieren", "en": "Export"},
    "settings":             {"de": "Einstellungen", "en": "Settings"},
    "language":             {"de": "Sprache", "en": "Language"},
    "dark_mode":            {"de": "Dunkelmodus", "en": "Dark Mode"},
    "light_mode":           {"de": "Hellmodus", "en": "Light Mode"},

    # ── Auth ────────────────────────────────────────────────────
    "login":                {"de": "Anmelden", "en": "Log in"},
    "logout":               {"de": "Abmelden", "en": "Log out"},
    "register":             {"de": "Registrieren", "en": "Sign up"},
    "email":                {"de": "E-Mail", "en": "Email"},
    "password":             {"de": "Passwort", "en": "Password"},
    "password_confirm":     {"de": "Passwort bestätigen", "en": "Confirm password"},
    "display_name":         {"de": "Anzeigename", "en": "Display name"},
    "no_account":           {"de": "Noch kein Konto?", "en": "No account yet?"},
    "have_account":         {"de": "Bereits ein Konto?", "en": "Already have an account?"},
    "login_success":        {"de": "Erfolgreich angemeldet!", "en": "Logged in successfully!"},
    "logout_success":       {"de": "Erfolgreich abgemeldet.", "en": "Logged out successfully."},
    "register_success":     {"de": "Willkommen bei FridgeChef!", "en": "Welcome to FridgeChef!"},
    "invalid_email":        {"de": "Ungültige E-Mail-Adresse.", "en": "Invalid email address."},
    "password_too_short":   {"de": "Passwort zu kurz (min. 6 Zeichen).", "en": "Password too short (min. 6 chars)."},
    "passwords_mismatch":   {"de": "Passwörter stimmen nicht überein.", "en": "Passwords do not match."},
    "change_password":      {"de": "Passwort ändern", "en": "Change password"},
    "current_password":     {"de": "Aktuelles Passwort", "en": "Current password"},
    "new_password":         {"de": "Neues Passwort", "en": "New password"},

    # ── Navigation ──────────────────────────────────────────────
    "nav_search":           {"de": "🔍 Suche", "en": "🔍 Search"},
    "nav_cookbook":         {"de": "📖 Kochbuch", "en": "📖 Cookbook"},
    "nav_shopping":         {"de": "🛒 Einkauf", "en": "🛒 Shopping"},
    "nav_tracker":          {"de": "📊 Tracker", "en": "📊 Tracker"},
    "nav_profile":          {"de": "👤 Profil", "en": "👤 Profile"},

    # ── Search ──────────────────────────────────────────────────
    "search_title":         {"de": "Zutaten suchen", "en": "Search Ingredients"},
    "search_placeholder":   {"de": "Zutat eingeben…", "en": "Enter ingredient…"},
    "add_ingredient":       {"de": "Hinzufügen", "en": "Add"},
    "remove":               {"de": "Entfernen", "en": "Remove"},
    "clear_all":            {"de": "Alle löschen", "en": "Clear all"},
    "your_ingredients":     {"de": "Deine Zutaten", "en": "Your Ingredients"},
    "common_ingredients":   {"de": "Häufige Zutaten", "en": "Common Ingredients"},
    "staple_ingredients":   {"de": "Grundzutaten", "en": "Pantry Staples"},
    "staples_enabled":      {"de": "Grundzutaten einschließen", "en": "Include pantry staples"},
    "find_recipes":         {"de": "Rezepte finden", "en": "Find Recipes"},
    "ai_recipes":           {"de": "KI-Rezepte generieren", "en": "Generate AI Recipes"},
    "upload_photo":         {"de": "Foto hochladen", "en": "Upload Photo"},
    "photo_hint":           {"de": "Foto deines Kühlschranks hochladen", "en": "Upload a photo of your fridge"},
    "analyzing_photo":      {"de": "Foto wird analysiert…", "en": "Analyzing photo…"},
    "no_ingredients":       {"de": "Bitte zuerst Zutaten hinzufügen.", "en": "Please add ingredients first."},
    "filters":              {"de": "Filter", "en": "Filters"},
    "vegetarian":           {"de": "Vegetarisch", "en": "Vegetarian"},
    "vegan":                {"de": "Vegan", "en": "Vegan"},
    "gluten_free":          {"de": "Glutenfrei", "en": "Gluten-free"},
    "lactose_free":         {"de": "Laktosefrei", "en": "Lactose-free"},
    "max_prep_time":        {"de": "Max. Zubereitungszeit (Min)", "en": "Max prep time (min)"},
    "difficulty":           {"de": "Schwierigkeit", "en": "Difficulty"},
    "cuisine":              {"de": "Küche", "en": "Cuisine"},
    "sort_by":              {"de": "Sortieren nach", "en": "Sort by"},
    "sort_match":           {"de": "Beste Übereinstimmung", "en": "Best match"},
    "sort_time":            {"de": "Zeit", "en": "Time"},
    "sort_difficulty":      {"de": "Schwierigkeit", "en": "Difficulty"},
    "results_found":        {"de": "{n} Rezept(e) gefunden", "en": "{n} recipe(s) found"},
    "no_results":           {"de": "Keine passenden Rezepte gefunden.", "en": "No matching recipes found."},
    "generating_ai":        {"de": "KI generiert Rezepte…", "en": "AI is generating recipes…"},
    "ai_unavailable":       {"de": "KI nicht verfügbar. OPENAI_API_KEY setzen.", "en": "AI unavailable. Set OPENAI_API_KEY."},

    # ── Recipe Detail ────────────────────────────────────────────
    "prep_time":            {"de": "Zubereitungszeit", "en": "Prep Time"},
    "servings":             {"de": "Portionen", "en": "Servings"},
    "servings_slider":      {"de": "Portionen anpassen", "en": "Adjust servings"},
    "ingredients":          {"de": "Zutaten", "en": "Ingredients"},
    "missing":              {"de": "fehlend", "en": "missing"},
    "available":            {"de": "vorhanden", "en": "available"},
    "instructions":         {"de": "Zubereitung", "en": "Instructions"},
    "nutrition":            {"de": "Nährwerte", "en": "Nutrition"},
    "kcal":                 {"de": "Kalorien", "en": "Calories"},
    "protein":              {"de": "Protein", "en": "Protein"},
    "fat":                  {"de": "Fett", "en": "Fat"},
    "carbs":                {"de": "Kohlenhydrate", "en": "Carbs"},
    "fiber":                {"de": "Ballaststoffe", "en": "Fiber"},
    "salt":                 {"de": "Salz", "en": "Salt"},
    "add_missing_to_shopping": {"de": "Fehlende zur Einkaufsliste", "en": "Add missing to shopping"},
    "all_ingredients_available": {"de": "Alle Zutaten vorhanden!", "en": "All ingredients available!"},
    "save_to_cookbook":     {"de": "Im Kochbuch speichern", "en": "Save to Cookbook"},
    "saved_to_cookbook":    {"de": "Im Kochbuch gespeichert!", "en": "Saved to Cookbook!"},
    "already_saved":        {"de": "Bereits im Kochbuch", "en": "Already in Cookbook"},
    "log_meal":             {"de": "Als gegessen markieren", "en": "Log as eaten"},
    "meal_logged":          {"de": "Mahlzeit protokolliert!", "en": "Meal logged!"},
    "back_to_results":      {"de": "← Zurück zu Ergebnissen", "en": "← Back to results"},

    # ── Cookbook ────────────────────────────────────────────────
    "cookbook_title":       {"de": "Mein Kochbuch", "en": "My Cookbook"},
    "cookbook_empty":       {"de": "Dein Kochbuch ist leer.", "en": "Your cookbook is empty."},
    "cookbook_empty_hint":  {"de": "Speichere Rezepte aus der Suche.", "en": "Save recipes from search results."},
    "search_cookbook":      {"de": "Kochbuch durchsuchen…", "en": "Search cookbook…"},
    "collection":           {"de": "Sammlung", "en": "Collection"},
    "all_collections":      {"de": "Alle Sammlungen", "en": "All collections"},
    "add_to_collection":    {"de": "Zur Sammlung hinzufügen", "en": "Add to collection"},
    "recipe_removed":       {"de": "Rezept entfernt.", "en": "Recipe removed."},

    # ── Shopping ────────────────────────────────────────────────
    "shopping_title":       {"de": "Einkaufsliste", "en": "Shopping List"},
    "shopping_empty":       {"de": "Deine Einkaufsliste ist leer.", "en": "Your shopping list is empty."},
    "shopping_empty_hint":  {"de": "Füge fehlende Zutaten aus Rezepten hinzu.", "en": "Add missing ingredients from recipes."},
    "clear_shopping":       {"de": "Alles löschen", "en": "Clear all"},
    "confirm_clear":        {"de": "Wirklich alle Items löschen?", "en": "Really delete all items?"},
    "item_completed":       {"de": "Erledigt", "en": "Completed"},
    "export_list":          {"de": "Liste exportieren", "en": "Export list"},
    "items_remaining":      {"de": "{n} offen", "en": "{n} open"},
    "merged_from":          {"de": "Aus: {recipes}", "en": "From: {recipes}"},

    # ── Tracker ─────────────────────────────────────────────────
    "tracker_title":        {"de": "Ernährungs-Tracker", "en": "Nutrition Tracker"},
    "tracker_empty":        {"de": "Noch keine Einträge heute.", "en": "No entries today."},
    "tracker_empty_hint":   {"de": "Markiere Rezepte als gegessen.", "en": "Log meals from recipe details."},
    "day_view":             {"de": "Tag", "en": "Day"},
    "week_view":            {"de": "Woche", "en": "Week"},
    "month_view":           {"de": "Monat", "en": "Month"},
    "today":                {"de": "Heute", "en": "Today"},
    "add_custom_entry":     {"de": "Eintrag hinzufügen", "en": "Add entry"},
    "custom_entry_name":    {"de": "Name (z.B. Apfel)", "en": "Name (e.g. Apple)"},
    "custom_entry_kcal":    {"de": "Kalorien (kcal)", "en": "Calories (kcal)"},
    "custom_entry_protein": {"de": "Protein (g)", "en": "Protein (g)"},
    "custom_entry_fat":     {"de": "Fett (g)", "en": "Fat (g)"},
    "custom_entry_carbs":   {"de": "Kohlenhydrate (g)", "en": "Carbs (g)"},
    "daily_goal":           {"de": "Tagesziel", "en": "Daily goal"},
    "consumed":             {"de": "Konsumiert", "en": "Consumed"},
    "remaining_goal":       {"de": "Verbleibend", "en": "Remaining"},
    "entry_added":          {"de": "Eintrag hinzugefügt!", "en": "Entry added!"},
    "entry_deleted":        {"de": "Eintrag gelöscht.", "en": "Entry deleted."},

    # ── Profile ──────────────────────────────────────────────────
    "profile_title":        {"de": "Mein Profil", "en": "My Profile"},
    "name":                 {"de": "Name", "en": "Name"},
    "preferences":          {"de": "Einstellungen", "en": "Preferences"},
    "diet_filters":         {"de": "Standard-Diät-Filter", "en": "Default diet filters"},
    "daily_goals":          {"de": "Tagesziele", "en": "Daily goals"},
    "daily_calories_goal":  {"de": "Kalorien-Tagesziel", "en": "Daily calorie goal"},
    "daily_protein_goal":   {"de": "Protein-Tagesziel (g)", "en": "Daily protein goal (g)"},
    "daily_fat_goal":       {"de": "Fett-Tagesziel (g)", "en": "Daily fat goal (g)"},
    "daily_carbs_goal":     {"de": "Kohlenhydrate-Tagesziel (g)", "en": "Daily carbs goal (g)"},
    "units_metric":         {"de": "Metrisch", "en": "Metric"},
    "units_imperial":       {"de": "Imperial", "en": "Imperial"},
    "units_system":         {"de": "Maßsystem", "en": "Unit system"},
    "appearance":           {"de": "Erscheinungsbild", "en": "Appearance"},
    "data_export":          {"de": "Daten exportieren", "en": "Export data"},
    "export_cookbook":      {"de": "Kochbuch exportieren (JSON)", "en": "Export cookbook (JSON)"},
    "export_tracker":       {"de": "Tracker exportieren (CSV)", "en": "Export tracker (CSV)"},
    "delete_account":       {"de": "Konto löschen", "en": "Delete account"},
    "confirm_delete_account": {"de": "Konto wirklich löschen? Diese Aktion ist unwiderruflich.", "en": "Really delete account? This cannot be undone."},
    "account_deleted":      {"de": "Konto gelöscht.", "en": "Account deleted."},
    "profile_saved":        {"de": "Profil gespeichert!", "en": "Profile saved!"},

    # ── Difficulty labels ─────────────────────────────────────────
    "Easy":                 {"de": "Einfach", "en": "Easy"},
    "Medium":               {"de": "Mittel", "en": "Medium"},
    "Hard":                 {"de": "Schwer", "en": "Hard"},

    # ── Minutes ──────────────────────────────────────────────────
    "minutes":              {"de": "Min.", "en": "min"},
    "per_serving":          {"de": "pro Portion", "en": "per serving"},
}


def t(key: str, **kwargs) -> str:
    """Translate a key using the current session language."""
    lang = st.session_state.get("language", "de")
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("de", key))
    for k, v in kwargs.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text
