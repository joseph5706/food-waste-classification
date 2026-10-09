from flask import Flask, render_template, request, jsonify
from datetime import date, datetime
import os, json, urllib.request, urllib.error

app = Flask(__name__)

# Demo data is intentionally local and resets when the server restarts.
pantry = [
    {"id": 1, "name": "Spinach", "quantity": "1 bunch", "expiry": "2026-10-10", "category": "Vegetables"},
    {"id": 2, "name": "Tomatoes", "quantity": "4 pieces", "expiry": "2026-10-11", "category": "Vegetables"},
    {"id": 3, "name": "Cooked rice", "quantity": "2 cups", "expiry": "2026-10-09", "category": "Cooked food"},
    {"id": 4, "name": "Yogurt", "quantity": "1 cup", "expiry": "2026-10-12", "category": "Dairy"},
]
saved_log = []
next_id = 5

def days_left(expiry):
    try:
        return (date.fromisoformat(expiry) - date.today()).days
    except (ValueError, TypeError):
        return 999

def urgency(item):
    d = days_left(item.get("expiry", ""))
    if d < 0: return "Check immediately"
    if d == 0: return "Use today"
    if d == 1: return "Use soon"
    if d <= 3: return "Plan soon"
    return "Fresh"

def call_llm(prompt):
    """Optional OpenAI-compatible API. App remains usable without an API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    endpoint = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are FoodWise, a practical food-waste reduction assistant. Be concise. Never advise eating food that may be unsafe. Remind users that smell and appearance cannot guarantee safety."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode())
            return data["choices"][0]["message"]["content"]
    except Exception:
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/pantry", methods=["GET", "POST"])
def pantry_api():
    global next_id
    if request.method == "GET":
        result = []
        for item in pantry:
            row = dict(item)
            row["days_left"] = days_left(row["expiry"])
            row["urgency"] = urgency(row)
            result.append(row)
        return jsonify(sorted(result, key=lambda x: (x["days_left"], x["name"])))
    data = request.get_json(force=True)
    name = str(data.get("name", "")).strip()
    expiry = str(data.get("expiry", "")).strip()
    quantity = str(data.get("quantity", "")).strip() or "1 item"
    category = str(data.get("category", "Other")).strip() or "Other"
    try:
        date.fromisoformat(expiry)
    except ValueError:
        return jsonify({"error": "Please enter a valid expiry date."}), 400
    if not name:
        return jsonify({"error": "Please enter a food name."}), 400
    item = {"id": next_id, "name": name, "quantity": quantity, "expiry": expiry, "category": category}
    next_id += 1
    pantry.append(item)
    return jsonify(item), 201

@app.route("/api/pantry/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    global pantry
    before = len(pantry)
    pantry = [x for x in pantry if x["id"] != item_id]
    if len(pantry) == before:
        return jsonify({"error": "Item not found."}), 404
    return jsonify({"ok": True})

@app.route("/api/recipes", methods=["POST"])
def recipes():
    data = request.get_json(force=True)
    available = [x for x in pantry if days_left(x["expiry"]) >= 0]
    ingredients = [x["name"] for x in available]
    preferences = str(data.get("preferences", ""))
    prompt = (
        "Create 3 practical recipes using these ingredients first: " + ", ".join(ingredients) +
        ". Dietary preferences: " + preferences +
        ". For each recipe include title, ingredients, 3-5 steps, time, and which pantry items it helps use. "
        "Do not assume every ingredient must be used. Return readable plain text."
    )
    answer = call_llm(prompt)
    if answer:
        return jsonify({"mode": "AI-powered", "recipes_text": answer})
    # Helpful fallback for a working demo when no API key is configured.
    recipes_text = (
        "1. Spinach & Tomato Rice Bowl (15 min)\\n"
        "Use: cooked rice, spinach, tomatoes\\n"
        "Steps: 1) Check that the cooked rice was refrigerated promptly and is still within safe storage time. "
        "2) Sauté chopped tomatoes and spinach until cooked. 3) Add rice and heat thoroughly until steaming hot. "
        "4) Season to taste and serve.\\n\\n"
        "2. Tomato-Yogurt Raita (8 min)\\n"
        "Use: tomatoes, yogurt\\n"
        "Steps: 1) Wash and chop tomatoes. 2) Stir into fresh, properly refrigerated yogurt. "
        "3) Add salt and spices. 4) Serve immediately; keep chilled until serving.\\n\\n"
        "3. Spinach Tomato Omelette (12 min)\\n"
        "Use: spinach, tomatoes\\n"
        "Steps: 1) Wash and chop vegetables. 2) Cook spinach and tomatoes in a pan. "
        "3) Add beaten eggs if suitable for your diet. 4) Cook until eggs are fully set.\\n\\n"
        "These are starter suggestions based on your demo pantry. Adjust quantities and seasonings to taste."
    )
    return jsonify({"mode": "Smart demo mode", "recipes_text": recipes_text})

@app.route("/api/saved", methods=["POST"])
def mark_saved():
    data = request.get_json(force=True)
    name = str(data.get("name", "Saved food")).strip() or "Saved food"
    cost = data.get("cost", 0)
    try: cost = max(0, float(cost))
    except (TypeError, ValueError): cost = 0
    saved_log.append({"name": name, "cost": cost, "date": date.today().isoformat()})
    return jsonify({"ok": True, "total_items": len(saved_log),
                    "total_savings": round(sum(x["cost"] for x in saved_log), 2)})

@app.route("/api/stats")
def stats():
    return jsonify({
        "pantry_count": len(pantry),
        "urgent_count": sum(1 for x in pantry if 0 <= days_left(x["expiry"]) <= 1),
        "saved_count": len(saved_log),
        "saved_value": round(sum(x["cost"] for x in saved_log), 2)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
