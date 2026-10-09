import os
import json
import urllib.request
from datetime import date, datetime

import streamlit as st

st.set_page_config(
    page_title="FoodWise — Food Waste Reduction",
    page_icon="🥬",
    layout="wide",
)

# Streamlit keeps these values for the current browser session.
DEFAULT_PANTRY = [
    {"id": 1, "name": "Spinach", "quantity": "1 bunch", "expiry": "2026-10-10", "category": "Vegetables"},
    {"id": 2, "name": "Tomatoes", "quantity": "4 pieces", "expiry": "2026-10-11", "category": "Vegetables"},
    {"id": 3, "name": "Cooked rice", "quantity": "2 cups", "expiry": "2026-10-09", "category": "Cooked food"},
    {"id": 4, "name": "Yogurt", "quantity": "1 cup", "expiry": "2026-10-12", "category": "Dairy"},
]

if "pantry" not in st.session_state:
    st.session_state.pantry = [dict(item) for item in DEFAULT_PANTRY]
if "saved_log" not in st.session_state:
    st.session_state.saved_log = []
if "next_id" not in st.session_state:
    st.session_state.next_id = 5


def days_left(expiry):
    try:
        return (date.fromisoformat(expiry) - date.today()).days
    except (ValueError, TypeError):
        return 999


def urgency(item):
    d = days_left(item.get("expiry", ""))
    if d < 0:
        return "Check immediately"
    if d == 0:
        return "Use today"
    if d == 1:
        return "Use soon"
    if d <= 3:
        return "Plan soon"
    return "Fresh"


def call_llm(prompt):
    """Optional OpenAI-compatible API. The app works without an API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    endpoint = os.getenv(
        "OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are FoodWise, a practical food-waste reduction assistant. "
                    "Be concise. Never advise eating food that may be unsafe. "
                    "Remind users that smell and appearance cannot guarantee safety."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def make_demo_recipes():
    return (
        "### 1. Spinach & Tomato Rice Bowl (15 min)\n"
        "**Use:** cooked rice, spinach, tomatoes\n\n"
        "1. Only use cooked rice that was refrigerated promptly and remains within safe storage time.\n"
        "2. Sauté chopped tomatoes and spinach until cooked.\n"
        "3. Add the rice and heat thoroughly until steaming hot.\n"
        "4. Season to taste and serve.\n\n"
        "### 2. Tomato-Yogurt Raita (8 min)\n"
        "**Use:** tomatoes, yogurt\n\n"
        "1. Wash and chop the tomatoes.\n"
        "2. Stir into fresh, properly refrigerated yogurt.\n"
        "3. Add salt and spices, then serve immediately or keep chilled.\n\n"
        "### 3. Spinach Tomato Omelette (12 min)\n"
        "**Use:** spinach, tomatoes\n\n"
        "1. Wash and chop the vegetables.\n"
        "2. Cook spinach and tomatoes in a pan.\n"
        "3. Add beaten eggs if suitable for your diet.\n"
        "4. Cook until the eggs are fully set.\n\n"
        "_Suggestions are based on your demo pantry. Adjust quantities and seasonings to taste._"
    )


st.title("🥬 FoodWise")
st.caption("A practical food-waste reduction assistant")
st.info(
    "Demo data is stored in this browser session and resets when the session restarts. "
    "This version does not use a database."
)

pantry = st.session_state.pantry
saved_log = st.session_state.saved_log
today = date.today()
urgent_count = sum(1 for item in pantry if 0 <= days_left(item["expiry"]) <= 1)
saved_value = round(sum(item["cost"] for item in saved_log), 2)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Pantry items", len(pantry))
m2.metric("Use today / soon", urgent_count)
m3.metric("Saved food entries", len(saved_log))
m4.metric("Estimated savings", f"₹{saved_value:,.2f}")

tab_pantry, tab_recipes, tab_saved, tab_stats = st.tabs(
    ["🥗 Pantry & Expiry", "🍲 Recipe Ideas", "💚 Food Saved", "📊 Statistics"]
)

with tab_pantry:
    st.subheader("Your pantry")
    if pantry:
        for item in sorted(pantry, key=lambda x: (days_left(x["expiry"]), x["name"])):
            d = days_left(item["expiry"])
            label = urgency(item)
            left, mid, right = st.columns([4, 2, 1])
            with left:
                st.markdown(f"**{item['name']}** · {item['quantity']}")
                st.caption(f"{item['category']} · Expires: {item['expiry']}")
            with mid:
                st.write(f"{label} · {d} day(s)")
            with right:
                if st.button("Remove", key=f"remove_{item['id']}"):
                    st.session_state.pantry = [
                        x for x in st.session_state.pantry if x["id"] != item["id"]
                    ]
                    st.rerun()
            st.divider()
    else:
        st.write("Your pantry is empty. Add an item below.")

    st.subheader("Add food")
    with st.form("add_food_form", clear_on_submit=True):
        name = st.text_input("Food name")
        quantity = st.text_input("Quantity", value="1 item")
        category = st.selectbox(
            "Category",
            ["Vegetables", "Fruits", "Dairy", "Cooked food", "Grains", "Meat/Fish", "Other"],
        )
        expiry = st.date_input("Expiry date", value=today)
        submitted = st.form_submit_button("Add to pantry", type="primary")
        if submitted:
            if not name.strip():
                st.error("Please enter a food name.")
            else:
                st.session_state.pantry.append(
                    {
                        "id": st.session_state.next_id,
                        "name": name.strip(),
                        "quantity": quantity.strip() or "1 item",
                        "expiry": expiry.isoformat(),
                        "category": category,
                    }
                )
                st.session_state.next_id += 1
                st.success(f"Added {name.strip()} to your pantry.")
                st.rerun()

with tab_recipes:
    st.subheader("Recipe suggestions")
    st.write("Get ideas that prioritize food already in your pantry.")
    preferences = st.text_input(
        "Dietary preferences (optional)",
        placeholder="e.g. vegetarian, no nuts, high protein",
    )
    if st.button("Generate recipes", type="primary"):
        available = [
            item for item in st.session_state.pantry
            if days_left(item["expiry"]) >= 0
        ]
        ingredients = [item["name"] for item in available]
        prompt = (
            "Create 3 practical recipes using these ingredients first: "
            + ", ".join(ingredients)
            + ". Dietary preferences: "
            + preferences
            + ". For each recipe include title, ingredients, 3-5 steps, time, "
              "and which pantry items it helps use. Do not assume every ingredient "
              "must be used. Return readable plain text."
        )
        answer = call_llm(prompt)
        if answer:
            st.session_state.recipe_text = answer
            st.session_state.recipe_mode = "AI-powered"
        else:
            st.session_state.recipe_text = make_demo_recipes()
            st.session_state.recipe_mode = "Smart demo mode"
    if "recipe_text" in st.session_state:
        st.caption(f"Mode: {st.session_state.get('recipe_mode', 'Smart demo mode')}")
        st.markdown(st.session_state.recipe_text)
    st.warning(
        "Food-safety reminder: expiry labels and storage conditions matter. "
        "Smell and appearance alone cannot guarantee that food is safe. "
        "Do not use food that may have been stored unsafely."
    )

with tab_saved:
    st.subheader("Track food saved from waste")
    with st.form("saved_food_form", clear_on_submit=True):
        saved_name = st.text_input("Food saved", placeholder="e.g. leftover vegetables")
        cost = st.number_input("Estimated value saved (₹)", min_value=0.0, step=10.0)
        saved_submit = st.form_submit_button("Log saved food", type="primary")
        if saved_submit:
            if not saved_name.strip():
                st.error("Please enter a food name.")
            else:
                st.session_state.saved_log.append(
                    {
                        "name": saved_name.strip(),
                        "cost": float(cost),
                        "date": date.today().isoformat(),
                    }
                )
                st.success("Saved-food entry recorded.")
                st.rerun()
    if st.session_state.saved_log:
        st.markdown("#### Saved-food history")
        for idx, entry in enumerate(reversed(st.session_state.saved_log), start=1):
            st.write(
                f"{idx}. **{entry['name']}** — ₹{entry['cost']:.2f} "
                f"({entry['date']})"
            )
    else:
        st.write("No saved-food entries yet.")

with tab_stats:
    st.subheader("Food-waste statistics")
    c1, c2 = st.columns(2)
    c1.metric("Items in pantry", len(st.session_state.pantry))
    c2.metric(
        "Items expiring today or tomorrow",
        sum(
            1 for item in st.session_state.pantry
            if 0 <= days_left(item["expiry"]) <= 1
        ),
    )
    c3, c4 = st.columns(2)
    c3.metric("Food saved entries", len(st.session_state.saved_log))
    c4.metric(
        "Estimated value saved",
        f"₹{sum(x['cost'] for x in st.session_state.saved_log):,.2f}",
    )
    st.caption(
        "These are session-level demo statistics. They are not stored permanently "
        "and are reset when the Streamlit session restarts."
    )
