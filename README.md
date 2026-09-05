# Task 0 — Agentic Incident Flow

A support ticket is created in ServiceNow → a Business Rule sends it to this
FastAPI service → the service asks an LLM for a decision (respond / ask /
escalate) using only the provided knowledge articles → the service writes
the result back onto the same ticket.

> **Note on LLM provider:** the assignment specified Gemini. During this
> project, Google was issuing broken `AQ.`-prefixed API keys that were
> rejected by the Gemini REST API — a confirmed, widespread Google-side
> issue at the time, not a configuration mistake (see `reflection.md` for
> details). We switched to **Groq** (OpenAI-compatible, free tier) as a
> drop-in replacement using the exact same prompt/JSON contract.

## Project structure

- `app/main.py` — FastAPI app, `/webhook` endpoint
- `app/gemini_client.py` — calls the LLM (Groq), builds the prompt
- `app/servicenow_client.py` — writes the decision back to ServiceNow
- `kb_articles.json` — the 5 knowledge articles (from the asset pack)
- `prompt.txt` — exact prompt template sent to the LLM
- `test_incidents.json` — the 3 required test tickets (from the asset pack)
- `business_rule.js` — ServiceNow Business Rule script (from the asset pack)
- `payload_contract.json` — webhook payload spec (from the asset pack)
- `pdi_guide.md` — ServiceNow PDI setup guide (from the asset pack)
- `screenshots/` — Business Rule + before/after screenshots
- `requirements.txt`
- `.env.example`
- `README.md`

## 1. Install

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

## 2. Get a free Groq API key

1. Go to https://console.groq.com/keys
2. Sign in with any Google account.
3. Click "Create API Key". Copy it — it starts with `gsk_...`.

## 3. Set up your ServiceNow PDI

1. Go to https://developer.servicenow.com and request a free **Personal
   Developer Instance (PDI)**.
2. Note your instance URL (`https://devXXXXXX.service-now.com`), and your
   admin username/password.
3. Follow `pdi_guide.md` (included in this repo) to create the Business
   Rule on the `Incident` table, using the script in `business_rule.js`.
   The Business Rule must run **after Insert**.

## 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

GROQ_API_KEY=gsk_your_real_key_here
GROQ_MODEL=llama-3.3-70b-versatile
SNOW_INSTANCE_URL=https://devXXXXXX.service-now.com
SNOW_USERNAME=admin
SNOW_PASSWORD=your_pdi_password


`.env` is git-ignored — never commit it.

> Note: check `https://api.groq.com/openai/v1/models` with your key if you
> get a `model_not_found` error — Groq's available model list changes, and
> `GROQ_MODEL` needs to match one your key currently has access to.

## 5. Run the service

```bash
uvicorn app.main:app --reload --port 8000
```

Check it's alive: open http://127.0.0.1:8000 → should show `{"status": "ok", ...}`.

## 6. Expose it publicly with ngrok

In a second terminal:

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` (or `.ngrok-free.dev`) URL. Go to
your Business Rule in ServiceNow and set the endpoint URL in the script to:

https://xxxx.ngrok-free.app/webhook


## 7. Test end to end

1. In your PDI, go to **Incident → Create New**.
2. Use one of the three scenarios from `test_incidents.json`:
   - "Printer not printing after office move" / "It was working yesterday.
     I tried turning it off and on." → expected: **respond**
   - "Cannot send email" / "It just doesn't work." → expected: **ask**
   - "Request: annual leave approval" / "I would like to take next week
     off." → expected: **escalate**
3. Fill in a Caller (required field), then Submit.
4. Watch the `uvicorn` terminal for:

Accepted incident INC00XXXXX, processing in background.
Incident INC00XXXXX -> decision=respond
Incident INC00XXXXX written back to ServiceNow.

5. Refresh the incident in ServiceNow to see the result:
   - **respond** → ticket is Resolved, with resolution notes filled in
   - **ask** → a customer-visible comment is added, ticket stays open
   - **escalate** → a work note is added, ticket stays open

## 8. (Optional) Test the LLM step alone, without ServiceNow

```bash
python test_local.py
```

Runs each ticket in `test_incidents.json` straight through `get_decision()`
and prints the result, without needing ServiceNow running.

## Troubleshooting

- **No response in ServiceNow**: check the Business Rule's "Insert"
  checkbox is checked (When to run tab), and that the ngrok URL in the
  script matches your currently running tunnel (it changes every restart
  on the free tier).
- **401/403 from ServiceNow on write-back**: double check
  `SNOW_USERNAME`/`SNOW_PASSWORD` in `.env`. A `403` with "Data Policy
  Exception" usually means a required field (like Resolution code) has an
  invalid value for your instance — check valid choices via
  `GET /api/now/table/sys_choice?sysparm_query=name=incident^element=close_code`.
- **Groq errors**: check `GROQ_API_KEY` is set, and that `GROQ_MODEL` is a
  model your key currently has access to (see step 4).
- **Environment variables not loading**: `main.py` calls `load_dotenv()` at
  startup — if you renamed/moved files, make sure that call still runs
  before any `os.environ.get(...)` calls.