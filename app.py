
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import markdown
import json
import google.generativeai as genai
from db import query_all, query_one, execute

from dotenv import load_dotenv
load_dotenv()

# ===== Environment Validation =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("⚠️  Warning: GEMINI_API_KEY not set. Recipe Generator will not work.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ===== Login Required Decorator =====
def login_required(f):
    """Decorator to require login on protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def require_login():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None

# ===== Gemini API Helper =====
def parse_gemini_response(response_text: str) -> dict | list | None:
    """Parse Gemini API response, handling markdown code blocks."""
    text = response_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# Helper for unit conversions
def load_unit_conversions() -> dict:
    try:
        rows = query_all("SELECT family, unit, to_base_factor FROM unit_conversion")
        conversions = {}
        for r in rows:
            fam = r["family"]
            u = r["unit"].lower()
            factor = float(r["to_base_factor"])
            if fam not in conversions:
                conversions[fam] = {}
            conversions[fam][u] = factor
        return conversions
    except Exception:
        return {}  # Fail gracefully if table missing

def convert_unit(qty: float, from_unit: str | None, to_unit: str | None, conversions: dict) -> float | None:
    if not from_unit or not to_unit:
        return None
    u1, u2 = from_unit.lower(), to_unit.lower()
    if u1 == u2:
        return qty
    for fam, units in conversions.items():
        if u1 in units and u2 in units:
            return qty * units[u1] / units[u2]
    return None

# helper: compute match stats for a recipe vs a user's pantry
def compute_recipe_match(recipe_id: int, user_id: int) -> dict:
    ings = query_all(
        "SELECT ingredient_name, amount, unit FROM recipe_ingredients WHERE recipe_id = %s",
        (recipe_id,)
    )
    
    pantry = query_all(
        "SELECT item_name, unit, quantity FROM pantry_items WHERE user_id = %s",
        (user_id,)
    )
    
    conv_table = load_unit_conversions()
    
    pantry_map = {}
    for p in pantry:
        name_key = p["item_name"].lower()
        if name_key not in pantry_map:
            pantry_map[name_key] = []
        pantry_map[name_key].append(p)
        
    have = []
    missing = []
    
    for r in ings:
        req_name = r["ingredient_name"]
        req_unit = r["unit"]
        req_amount = float(r["amount"] or 0)
        
        matches = pantry_map.get(req_name.lower(), [])
        
        total_on_hand_in_req_unit = 0.0
        
        for m in matches:
            p_qty = float(m["quantity"])
            p_unit = m["unit"]
            
            if (p_unit or "").lower() == (req_unit or "").lower():
                total_on_hand_in_req_unit += p_qty
            else:
                converted = convert_unit(p_qty, p_unit, req_unit, conv_table)
                if converted is not None:
                    total_on_hand_in_req_unit += converted

        if total_on_hand_in_req_unit >= req_amount:
            have.append({
                "name": req_name,
                "need": req_amount,
                "unit": req_unit,
                "have": round(total_on_hand_in_req_unit, 2)
            })
        else:
            short = max(req_amount - total_on_hand_in_req_unit, 0)
            missing.append({
                "name": req_name,
                "need": req_amount,
                "unit": req_unit,
                "have": round(total_on_hand_in_req_unit, 2),
                "short": round(short, 2)
            })

    total_need = len(ings) if ings else 1
    have_count = len(have)
    match_pct = round(100.0 * have_count / total_need, 2)
    
    return {"have": have, "missing": missing, "match_pct": match_pct, "total": total_need, "have_count": have_count}

def merge_into_pantry(uid: int, name: str, qty: float, unit: str | None, expires_on: str | None = None) -> None:
    """
    Merge (name, unit) into the user's pantry:
    - If an item with the same name+unit exists, increase its quantity.
    - Expiry logic: if a new expiry is provided,
      keep the earliest non-null date between existing and new; otherwise leave as-is.
    """
    existing = query_one(
        """
        SELECT id, quantity, expires_on
        FROM pantry_items
        WHERE user_id = %s
          AND item_name = %s
          AND (unit <=> %s)
        ORDER BY expires_on IS NULL, expires_on ASC
        LIMIT 1
        """,
        (uid, name, unit),
    )

    if existing:
        if expires_on:
            execute(
                """
                UPDATE pantry_items
                SET quantity = quantity + %s,
                    expires_on = CASE
                        WHEN expires_on IS NULL THEN %s
                        WHEN %s IS NULL THEN expires_on
                        ELSE LEAST(expires_on, %s)
                    END
                WHERE id = %s AND user_id = %s
                """,
                (qty, expires_on, expires_on, expires_on, existing["id"], uid),
            )
        else:
            execute(
                "UPDATE pantry_items SET quantity = quantity + %s WHERE id = %s AND user_id = %s",
                (qty, existing["id"], uid),
            )
    else:
        execute(
            "INSERT INTO pantry_items(user_id, item_name, quantity, unit, expires_on) VALUES(%s,%s,%s,%s,%s)",
            (uid, name, qty, unit, expires_on),
        )



# route: register new account
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        if not email or not password or not name:
            flash("All fields are required.", "error")
            return render_template("register.html")
        existing = query_one("SELECT id FROM users WHERE email = %s", (email,))
        if existing:
            flash("Email already registered.", "error")
            return render_template("register.html")
        hashed = generate_password_hash(password)
        uid = execute("INSERT INTO users(name, email, password_hash) VALUES(%s,%s,%s)", (name, email, hashed))
        session["user_id"] = uid
        session["user_name"] = name
        return redirect(url_for("home"))
    return render_template("register.html")

# route: login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_one("SELECT id, name, password_hash FROM users WHERE email = %s", (email,))
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid credentials.", "error")
            return render_template("login.html")
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("home"))
    return render_template("login.html")

# route: logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# route: home with expiry-first suggestions and recommendations
@app.route("/")
def home():
    need = require_login()
    if need:
        return need
    uid = session["user_id"]
    expiring = query_all(  # expiry-first query
        """
        SELECT item_name, quantity, unit, expires_on
        FROM pantry_items
        WHERE user_id = %s
          AND expires_on IS NOT NULL
          AND expires_on BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 5 DAY)
        ORDER BY expires_on ASC
        """,
        (uid,),
    )
    recipes = query_all(  # get candidate recipes
        "SELECT id, title FROM recipes ORDER BY id DESC LIMIT 50",
        (),
    )
    recs = []
    for r in recipes:
        m = compute_recipe_match(r["id"], uid)
        recs.append({"id": r["id"], "title": r["title"], "match_pct": m["match_pct"]})
    recs.sort(key=lambda x: x["match_pct"], reverse=True)
    return render_template("home.html", expiring=expiring, recs=recs[:10])

# route: pantry view and add item
@app.route("/pantry", methods=["GET", "POST"])
def pantry():
    need = require_login()
    if need:
        return need
    uid = session["user_id"]
    if request.method == "POST":
        try:
            name = request.form.get("item_name", "").strip()
            qty_str = request.form.get("quantity", "0")
            qty = float(qty_str or 0)
            unit = request.form.get("unit", "").strip() or None
            exp = request.form.get("expires_on", "").strip() or None
            expires_on = exp if exp else None  # raw string or None (YYYY-MM-DD)
            if not name or qty <= 0:
                flash("Provide item name and positive quantity.", "error")
            else:
                merge_into_pantry(uid, name, qty, unit, expires_on)
                flash("Item added (merged).", "success")
                return redirect(url_for("pantry"))
        except ValueError:
            flash("Invalid quantity. Please enter a valid number.", "error")
        except Exception as e:
            flash(f"Error adding item: {str(e)}", "error")
            app.logger.error(f"Pantry add error: {str(e)}")
            
    items = query_all(
        "SELECT id, item_name, quantity, unit, expires_on FROM pantry_items WHERE user_id = %s ORDER BY item_name",
        (uid,),
    )
    return render_template("pantry.html", items=items)

# route: delete pantry item
@app.route("/pantry/delete/<int:item_id>", methods=["POST"])
def pantry_delete(item_id: int):
    need = require_login()
    if need:
        return need
    execute("DELETE FROM pantry_items WHERE id = %s AND user_id = %s", (item_id, session["user_id"]))
    flash("Item deleted.", "success")
    return redirect(url_for("pantry"))

# route: edit pantry item (quantity/unit/expiry)
@app.route("/pantry/edit/<int:item_id>", methods=["POST"])
def pantry_edit(item_id: int):
    need = require_login()
    if need:
        return need
    qty = float(request.form.get("quantity", "0") or 0)
    unit = request.form.get("unit", "").strip() or None
    exp = request.form.get("expires_on", "").strip() or None
    execute(
        "UPDATE pantry_items SET quantity=%s, unit=%s, expires_on=%s WHERE id=%s AND user_id=%s",
        (qty, unit, exp, item_id, session["user_id"]),
    )
    flash("Item updated.", "success")
    return redirect(url_for("pantry"))

# route: recipes search
@app.route("/recipes")  # list/search recipes
def recipes():
    need = require_login()
    if need:
        return need
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    sql = """
    SELECT DISTINCT r.id, r.title, r.description
    FROM recipes r
    LEFT JOIN recipe_tags rt ON rt.recipe_id = r.id
    LEFT JOIN tags t ON t.id = rt.tag_id
    LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id
    WHERE 1=1
    """  # base
    params = []
    if q:
        sql += " AND (r.title LIKE %s OR ri.ingredient_name LIKE %s OR t.name LIKE %s) "
        like = f"%{q}%"
        params += [like, like, like]
    if tag:
        sql += " AND t.name = %s "
        params.append(tag)
    sql += " ORDER BY r.title ASC "
    rows = query_all(sql, tuple(params))
    annotated = []
    for r in rows:
        m = compute_recipe_match(r["id"], session["user_id"])
        r["match_pct"] = m["match_pct"]
        annotated.append(r)
    annotated.sort(key=lambda x: x["match_pct"], reverse=True)
    return render_template("recipes.html", recipes=annotated, q=q, tag=tag)

# route: recipe detail with have/missing and actions
@app.route("/recipe/<int:recipe_id>", methods=["GET", "POST"])
def recipe_detail(recipe_id: int):
    need = require_login()
    if need:
        return need
    if request.method == "POST":
        if request.form.get("action") == "add_missing":
            # compute missing using helper
            m = compute_recipe_match(recipe_id, session["user_id"])
            for item in m["missing"]:
                execute(
                    "INSERT INTO shopping_list(user_id, item_name, quantity, unit, done) VALUES(%s,%s,%s,%s,0)",
                    (session["user_id"], item["name"], item["short"], item["unit"]),
                )
            flash("Missing ingredients added to your shopping list.", "success")
            return redirect(url_for("recipe_detail", recipe_id=recipe_id))

        if request.form.get("action") == "toggle_fav":
            fav = query_one("SELECT 1 FROM favourites WHERE user_id=%s AND recipe_id=%s", (session["user_id"], recipe_id))  # exists?
            if fav:
                execute("DELETE FROM favourites WHERE user_id=%s AND recipe_id=%s", (session["user_id"], recipe_id))
                flash("Removed from favourites.", "success")
            else:
                execute("INSERT INTO favourites(user_id, recipe_id) VALUES(%s,%s)", (session["user_id"], recipe_id))
                flash("Added to favourites.", "success")
            return redirect(url_for("recipe_detail", recipe_id=recipe_id))
    recipe = query_one("SELECT id, title, description, steps_md FROM recipes WHERE id=%s", (recipe_id,))
    tags = query_all(
        "SELECT t.name FROM tags t JOIN recipe_tags rt ON rt.tag_id=t.id WHERE rt.recipe_id=%s",
        (recipe_id,),
    )
    ingredients = query_all(
        "SELECT ingredient_name, amount, unit FROM recipe_ingredients WHERE recipe_id=%s",
        (recipe_id,),
    )
    m = compute_recipe_match(recipe_id, session["user_id"])
    steps_html = markdown.markdown(recipe["steps_md"] or "")
    is_fav = query_one(
        "SELECT 1 AS present FROM favourites WHERE user_id=%s AND recipe_id=%s",
        (session["user_id"], recipe_id),
    )  # favourite?
    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        tags=[t["name"] for t in tags],
        ingredients=ingredients,
        match=m,
        steps_html=steps_html,
        is_fav=bool(is_fav),
    )

# route: shopping list view + actions
@app.route("/shopping", methods=["GET", "POST"])
def shopping():
    need = require_login()
    if need:
        return need

    if request.method == "POST":
        action = request.form.get("action", "")
        uid = session["user_id"]

        try:
            if action == "add_item":
                name = (request.form.get("item_name") or "").strip()
                qty_raw = (request.form.get("quantity") or "").strip()
                unit = (request.form.get("unit") or "").strip() or None
                try:
                    qty = float(qty_raw or 0)
                except ValueError:
                    qty = 0
                if not name or qty <= 0:
                    flash("Provide an item name and a positive quantity.", "error")
                else:
                    execute(
                        "INSERT INTO shopping_list(user_id, item_name, quantity, unit, done) VALUES(%s,%s,%s,%s,0)",
                        (uid, name, qty, unit),
                    )
                    flash("Item added to shopping list.", "success")

            elif action == "toggle_done":
                sid = int(request.form.get("sid", "0") or 0)
                execute(
                    "UPDATE shopping_list SET done = 1 - done WHERE id=%s AND user_id=%s",
                    (sid, uid),
                )
                flash("Updated item.", "success")

            elif action == "delete_item":
                sid = int(request.form.get("sid", "0") or 0)
                execute(
                    "DELETE FROM shopping_list WHERE id=%s AND user_id=%s",
                    (sid, uid),
                )
                flash("Item deleted.", "success")

            elif action == "move_one":
                sid = int(request.form.get("sid", "0") or 0)
                row = query_one(
                    "SELECT item_name, quantity, unit FROM shopping_list WHERE id=%s AND user_id=%s",
                    (sid, uid),
                )
                if row:
                    merge_into_pantry(uid, row["item_name"], float(row["quantity"]), row["unit"], None)
                    execute("DELETE FROM shopping_list WHERE id=%s AND user_id=%s", (sid, uid))
                    flash("Moved item to pantry (merged).", "success")
                else:
                    flash("Could not find that item.", "error")

            elif action == "move_to_pantry":
                done_items = query_all(
                    "SELECT id, item_name, quantity, unit FROM shopping_list WHERE user_id=%s AND done=1",
                    (uid,),
                )
                if not done_items:
                    flash("No items are marked as done. Mark items as done first, or use 'Move now'.", "error")
                else:
                    for it in done_items:
                        merge_into_pantry(uid, it["item_name"], float(it["quantity"]), it["unit"], None)
                    execute("DELETE FROM shopping_list WHERE user_id=%s AND done=1", (uid,))
                    flash("Moved purchased items to pantry (merged).", "success")

        except ValueError as e:
            flash("Invalid input. Please check your data.", "error")
            app.logger.error(f"Shopping list ValueError: {str(e)}")
        except Exception as e:
            flash(f"Error processing request: {str(e)}", "error")
            app.logger.error(f"Shopping list error: {str(e)}")

        return redirect(url_for("shopping"))


    items = query_all(
        "SELECT id, item_name, quantity, unit, done FROM shopping_list WHERE user_id=%s ORDER BY done, item_name",
        (session["user_id"],),
    )
    return render_template("shopping.html", items=items)

# route: favourites
@app.route("/favourites")
def favourites():
    need = require_login()
    if need:
        return need
    favs = query_all(
        """
        SELECT r.id, r.title
        FROM favourites f
        JOIN recipes r ON r.id = f.recipe_id
        WHERE f.user_id = %s
        ORDER BY r.title
        """,
        (session["user_id"],),
    )
    return render_template("favourites.html", favs=favs)



# route: add user recipe (with markdown steps and ingredient lines)
@app.route("/add-recipe", methods=["GET", "POST"])
def add_recipe():
    need = require_login()
    if need:
        return need
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        tags_csv = request.form.get("tags", "").strip()  # tags comma/space
        steps_md = request.form.get("steps", "").strip()
        ingredients_lines = request.form.get("ingredients", "").strip().splitlines()
        if not title or not ingredients_lines:
            flash("Title and at least one ingredient are required.", "error")
            return render_template("add_recipe.html")
        rid = execute(
            "INSERT INTO recipes(title, description, steps_md, created_by) VALUES(%s,%s,%s,%s)",
            (title, description, steps_md, session["user_id"]),
        )
        for line in ingredients_lines:
            parts = [p.strip() for p in line.split("|")]
            name = parts[0] if len(parts) > 0 else ""
            amount = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
            unit = parts[2] if len(parts) > 2 and parts[2] else None
            if name:
                execute(
                    "INSERT INTO recipe_ingredients(recipe_id, ingredient_name, amount, unit) VALUES(%s,%s,%s,%s)",
                    (rid, name, amount, unit),
                )
        if tags_csv:
            for raw in [t.strip().lower() for t in tags_csv.replace(";", ",").split(",") if t.strip()]:
                trow = query_one("SELECT id FROM tags WHERE name=%s", (raw,))
                tid = trow["id"] if trow else execute("INSERT INTO tags(name) VALUES(%s)", (raw,))
                execute("INSERT IGNORE INTO recipe_tags(recipe_id, tag_id) VALUES(%s,%s)", (rid, tid))
        flash("Recipe added!", "success")
        return redirect(url_for("recipe_detail", recipe_id=rid))
    return render_template("add_recipe.html")



# route: recipe generator using Gemini AI
@app.route("/recipe-generator", methods=["GET", "POST"])
def recipe_generator():
    need = require_login()
    if need:
        return need
    
    uid = session["user_id"]
    recipes = None
    error = None
    ingredients_input = ""
    
    pantry_items = query_all(
        "SELECT item_name FROM pantry_items WHERE user_id = %s ORDER BY item_name",
        (uid,),
    )
    pantry_list = [p["item_name"] for p in pantry_items]
    
    if request.method == "POST":
        action = request.form.get("action", "generate")
        ingredients_input = request.form.get("ingredients", "").strip()
        
        if action == "generate" and ingredients_input:
            try:
                prompt = f"""Based on these available ingredients: {ingredients_input}

Generate exactly 3 different recipe suggestions. For each recipe, provide:
- name: Recipe name
- description: Brief 1-2 sentence description
- time: Estimated cooking time (e.g., "30 mins")
- difficulty: Easy, Medium, or Hard

Return ONLY a valid JSON array with exactly 3 objects. No markdown, no explanation, just the JSON array.
Example format:
[{{ "name": "Recipe Name", "description": "Brief description", "time": "30 mins", "difficulty": "Easy" }}]"""
                
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                
                # Parse JSON response using helper
                recipes = parse_gemini_response(response.text)
                if recipes is None:
                    error = "Failed to parse recipe suggestions. Please try again."
                else:
                    session["generated_recipes"] = recipes
                    session["recipe_ingredients"] = ingredients_input
                
            except Exception as e:
                error = f"Error generating recipes: {str(e)}"
        elif action == "generate":
            error = "Please enter some ingredients first."
    
    return render_template(
        "recipe_generator.html",
        recipes=recipes,
        error=error,
        ingredients=ingredients_input,
        pantry_list=pantry_list,
    )

# route: get full recipe details for selected recipe
@app.route("/recipe-generator/details", methods=["POST"])
def recipe_generator_details():
    need = require_login()
    if need:
        return need
    
    recipe_name = request.form.get("recipe_name", "").strip()
    ingredients_input = session.get("recipe_ingredients", "")
    
    if not recipe_name:
        flash("No recipe selected.", "error")
        return redirect(url_for("recipe_generator"))
    
    try:
        prompt = f"""Create a detailed recipe for "{recipe_name}" using these available ingredients: {ingredients_input}

Provide the recipe in this exact JSON format:
{{
    "name": "Recipe Name",
    "description": "Detailed description",
    "prep_time": "15 mins",
    "cook_time": "30 mins",
    "servings": "4",
    "difficulty": "Easy/Medium/Hard",
    "ingredients": [
        {{"item": "ingredient name", "amount": "quantity with unit"}}
    ],
    "steps": [
        "Step 1 instruction",
        "Step 2 instruction"
    ],
    "tips": "Optional cooking tips"
}}

Return ONLY valid JSON, no markdown, no explanation."""
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        # Parse JSON response using helper
        recipe_details = parse_gemini_response(response.text)
        if recipe_details is None:
            flash("Failed to parse recipe details. Please try again.", "error")
            return redirect(url_for("recipe_generator"))
        
        return render_template(
            "recipe_generator.html",
            recipe_details=recipe_details,
            ingredients=ingredients_input,
            pantry_list=[],
        )
        
    except Exception as e:
        flash(f"Error getting recipe details: {str(e)}", "error")
        return redirect(url_for("recipe_generator"))

# ===== Global Error Handlers =====
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with a friendly message."""
    flash("Page not found. Redirecting to home.", "error")
    return redirect(url_for("home"))

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors with a friendly message."""
    flash("An unexpected error occurred. Please try again.", "error")
    return redirect(url_for("home"))

@app.errorhandler(Exception)
def handle_exception(e):
    """Catch-all error handler for unhandled exceptions."""
    app.logger.error(f"Unhandled exception: {str(e)}")
    flash("Something went wrong. Please try again.", "error")
    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host="127.0.0.1", port=port)
