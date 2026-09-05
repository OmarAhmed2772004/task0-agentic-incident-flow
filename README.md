# Task 0 — Agentic Incident Flow

A support ticket is created in ServiceNow → a Business Rule sends it to this
FastAPI service → the service asks Gemini for a decision (respond / ask /
escalate) using only the provided knowledge articles → the service writes
the result back onto the same ticket.

## Project structure

```
task0/
├── app/
│   ├── main.py               # FastAPI app, /webhook endpoint
│   ├── gemini_client.py      # calls Gemini, builds the prompt
│   └── servicenow_client.py  # writes the decision back to ServiceNow
├── kb_articles.json          # the 5 knowledge articles (REPLACE with the real one)
├── prompt.txt                # exact prompt template sent to Gemini
├── test_incidents.json       # <- copy this in from the asset pack
├── business_rule.js          # <- copy this in from the asset pack
├── payload_contract.json     # <- copy this in from the asset pack
├── test_local.py             # quick script to test the Gemini step alone
├── requirements.txt
├── .env.example
└── README.md
```

## 1. Install

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Real asset files

Your real `kb_articles.json`, `test_incidents.json`, `business_rule.js`,
`payload_contract.json`, and `pdi_guide.md` are already included in this
project — the code has been matched to them exactly (note: `priority` is an
integer 1–5, and both `kb_articles.json` and `test_incidents.json` wrap their
data in a `{"description": ..., "articles"/"incidents": [...]}` object, which
`app/gemini_client.py` and `test_local.py` already account for).

## 3. Get a free Gemini API key

1. Go to https://aistudio.google.com/apikey
2. Sign in with a Google account, click "Create API key". No credit card needed.
3. Copy the key.

## 4. Set up your ServiceNow PDI

1. Go to https://developer.servicenow.com and request a **Personal
   Developer Instance (PDI)**. It takes a few minutes to provision.
2. Note your instance URL (looks like `https://devXXXXXX.service-now.com`),
   and your admin username/password.
3. In the PDI, go to **System Definition → Business Rules → New**.
4. Set it to run on table `Incident`, **Insert**, **After** (or as instructed
   in `pdi_guide.md` from your asset pack — follow that guide exactly since
   it has the precise field names your instructors expect).
5. Paste in the contents of `business_rule.js`. Replace the placeholder URL
   inside it with your ngrok URL + `/webhook` (you'll get this URL in the
   next step, so come back and update it once ngrok is running).

## 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
SNOW_INSTANCE_URL=https://devXXXXXX.service-now.com
SNOW_USERNAME=admin
SNOW_PASSWORD=your_pdi_password
```

`.env` is git-ignored — never commit it.

## 6. Run the service

```bash
uvicorn app.main:app --reload --port 8000
```

Check it's alive: open http://127.0.0.1:8000 → should show `{"status": "ok", ...}`.

## 7. Expose it publicly with ngrok

In a second terminal:

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` URL it gives you. Go back to your
Business Rule in ServiceNow (step 4) and set the webhook URL to:

```
https://xxxx.ngrok-free.app/webhook
```

## 8. Test end to end

1. In your PDI, go to **Incident → Create New**.
2. Fill in a short description / description matching one of the scenarios
   in `test_incidents.json` (a clear printer problem, a vague email problem,
   or a leave request).
3. Submit it.
4. Watch your `uvicorn` terminal — you should see the incident accepted (202),
   then a log line showing the Gemini decision, then a log line confirming
   the write-back.
5. Refresh the incident in ServiceNow — it should now show the resolution
   notes / comment / work note depending on the decision.

## 9. (Optional) Test the Gemini step alone, without ServiceNow

```bash
python test_local.py
```

This runs each ticket in `test_incidents.json` straight through
`get_decision()` and prints what Gemini decided, so you can debug prompt/KB
issues quickly without creating real tickets.

## Troubleshooting

- **No response in ServiceNow**: check the Business Rule actually fired
  (System Logs), and that the ngrok URL in the rule matches your currently
  running ngrok tunnel (it changes every time you restart ngrok on the free
  tier).
- **401 from ServiceNow**: double check `SNOW_USERNAME` / `SNOW_PASSWORD` in
  `.env`.
- **Gemini errors**: check `GEMINI_API_KEY` is set and that your prompt in
  `prompt.txt` still produces valid JSON — see `_extract_json` in
  `app/gemini_client.py` for how it's parsed.
# task0-agentic-incident-flow
