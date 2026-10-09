# FoodWise AI — Sustainability Hackathon Prototype

FoodWise AI helps users reduce household food waste by tracking pantry items, prioritizing ingredients nearing their date, generating recipes from available ingredients, and recording self-reported food savings.

## Features
- Responsive dashboard and pantry inventory
- Expiry-date prioritization (based on user-entered dates)
- Add and remove ingredients
- Recipe ideas based on pantry contents
- Optional OpenAI-compatible chat-completions integration
- Smart demo recipe fallback when no API key is configured
- Self-reported food-rescue log and estimated money saved
- No database required for the first demo; data resets when server restarts

## Run locally
Requires Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Enable AI recipe generation
Copy `.env.example` values into your environment. Set `OPENAI_API_KEY` securely in your terminal or hosting provider; do not commit the key to GitHub. You can change `OPENAI_BASE_URL` and `OPENAI_MODEL` for a compatible provider.

Windows PowerShell example:
```powershell
$env:OPENAI_API_KEY="your-key"
python app.py
```

Without an API key, the app uses built-in demo recipes so the prototype remains demonstrable offline.

## Important prototype limitations
- Pantry and saved-food logs live in server memory and reset when the server restarts.
- The demo date values may need updating for your presentation.
- The recipe fallback is illustrative, not a nutrition or food-safety authority.
- Date reminders do not determine whether food is safe. Follow package/storage instructions and local food-safety guidance. Never use the app to judge spoiled food.
- Savings are user-entered estimates. Do not present them as independently verified impact or precise carbon savings.

## Suggested team split (2–4 members)
1. Frontend/UI: polish responsive screens and user flow.
2. Backend/data: validation, database persistence, pantry CRUD.
3. AI/research: recipe prompt, safety guardrails, testing.
4. Pitch/demo: user interviews, impact methodology, slides and live demo.

## Hackathon roadmap
1. Prototype: pantry + urgency + recipe ideas + savings log.
2. Reliability: SQLite persistence, test cases, date/time-zone handling.
3. AI: structured recipe output, dietary/allergen constraints, tests for unsafe prompts.
4. Differentiator: explain why each ingredient is prioritized; prevent duplicate shopping.
5. Evaluation: test with sample households and report measured usability, recipe usefulness, and food-rescue logs.
