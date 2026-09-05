# Task 0 — Agentic Incident Flow

A support ticket is created in ServiceNow → a Business Rule sends it to this FastAPI service → the service asks an LLM for a decision (`respond` / `ask` / `escalate`) using only the provided knowledge articles → the service writes the result back onto the same ticket.

> **Note on LLM provider:** The assignment specified Gemini. During this project, Gemini API access was not working reliably with the available API keys, so **Groq** was used as a drop-in replacement through its OpenAI-compatible API. The same prompt and JSON decision contract are preserved.

## Project Structure

```text
task0/
├── app/
│   ├── main.py                  # FastAPI application and /webhook endpoint
│   ├── gemini_client.py         # LLM client and decision generation
│   └── servicenow_client.py     # ServiceNow API integration
├── kb_articles.json             # Knowledge-base articles
├── prompt.txt                   # Prompt template sent to the LLM
├── test_incidents.json          # Required test incidents
├── business_rule.js             # ServiceNow Business Rule
├── payload_contract.json        # Webhook payload specification
├── pdi_guide.md                 # ServiceNow PDI setup guide
├── screenshots/                 # Setup and before/after screenshots
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment-variable template
├── README.md                    # Project documentation
└── reflection.md                # Project reflection
```

## 1. Installation

Create and activate a Python virtual environment:

```bash
python -m venv venv
```

### Windows

```powershell
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 2. Get a Groq API Key

This project uses Groq as the LLM provider.

1. Go to the Groq Console.
2. Sign in.
3. Create an API key.
4. Copy the generated key.

The key normally starts with:

```text
gsk_...
```

## 3. Set Up the ServiceNow PDI

1. Create or access a ServiceNow Personal Developer Instance (PDI).
2. Note your instance URL, for example:

```text
https://devXXXXXX.service-now.com
```

3. Note your ServiceNow username and password.
4. Follow `pdi_guide.md` to configure the Incident table.
5. Create the Business Rule using the script in `business_rule.js`.
6. The Business Rule should run **After Insert**.
7. Configure the webhook endpoint to point to the publicly accessible FastAPI service.

## 4. Configure Environment Variables

Create a `.env` file based on `.env.example`.

```text
GROQ_API_KEY=gsk_your_real_key_here
GROQ_MODEL=llama-3.3-70b-versatile

SNOW_INSTANCE_URL=https://devXXXXXX.service-now.com
SNOW_USERNAME=admin
SNOW_PASSWORD=your_pdi_password
```

The `.env` file contains secrets and must **never** be committed to GitHub.

Make sure `.env` is included in `.gitignore`.

## 5. Run the FastAPI Service

Start the application with:

```powershell
uvicorn app.main:app --reload --port 8000
```

The service should start on:

```text
http://127.0.0.1:8000
```

You can check the root endpoint in a browser.

The application should return a response indicating that the service is running.

## 6. Expose the Service Using ngrok

Because ServiceNow needs to reach the locally running FastAPI application, expose port `8000` using ngrok.

Open a second terminal and run:

```powershell
ngrok http 8000
```

ngrok will provide a public HTTPS URL similar to:

```text
https://xxxx.ngrok-free.app
```

The ServiceNow Business Rule should send the webhook request to:

```text
https://xxxx.ngrok-free.app/webhook
```

> **Important:** The free ngrok URL may change when the tunnel is restarted. If the URL changes, update the Business Rule accordingly.

## 7. End-to-End Flow

The complete workflow is:

```text
ServiceNow Incident
        │
        ▼
Business Rule
        │
        ▼
POST /webhook
        │
        ▼
FastAPI Application
        │
        ▼
Knowledge Articles + Incident
        │
        ▼
Groq LLM
        │
        ▼
Decision
 ┌──────┼────────┐
 ▼      ▼        ▼
respond ask    escalate
 │      │        │
 └──────┼────────┘
        ▼
ServiceNow REST API
        │
        ▼
Original Incident Updated
```

The webhook is accepted immediately and the incident is processed in a background task.

A successful run produces logs similar to:

```text
Accepted incident INC0010007, processing in background.
Incident INC0010007 -> decision=respond
Incident INC0010007 written back to ServiceNow.
```

## 8. Test the Required Incidents

The three required scenarios are provided in `test_incidents.json`.

### Test 1 — Printer Issue

Example:

```text
Short description:
Printer not printing after office move

Description:
It was working yesterday. I tried turning it off and on.
```

Expected decision:

```text
respond
```

The incident should be resolved and resolution information should be written back to ServiceNow.

### Test 2 — Email Issue

Example:

```text
Short description:
Cannot send email

Description:
It just doesn't work.
```

Expected decision:

```text
ask
```

A customer-visible comment should be added while the incident remains open.

### Test 3 — Annual Leave Request

Example:

```text
Short description:
Request: annual leave approval

Description:
I would like to take next week off.
```

Expected decision:

```text
escalate
```

A work note should be added while the incident remains open.

## 9. Run an End-to-End Test

1. Start the FastAPI server:

```powershell
uvicorn app.main:app --reload --port 8000
```

2. Start ngrok:

```powershell
ngrok http 8000
```

3. Make sure the ServiceNow Business Rule uses the current ngrok `/webhook` URL.
4. Open the Incident table in ServiceNow.
5. Create a new incident using one of the scenarios from `test_incidents.json`.
6. Fill in the required fields.
7. Submit the incident.
8. Monitor the FastAPI terminal.

A successful request should show:

```text
POST /webhook HTTP/1.1" 202 Accepted
```

Then the LLM request should succeed:

```text
HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
```

Finally, the ServiceNow update should succeed:

```text
HTTP Request: PATCH https://devXXXXXX.service-now.com/api/now/table/incident/... "HTTP/1.1 200 OK"
```

## 10. Optional Local LLM Test

If `test_local.py` is available in the project, the LLM decision logic can be tested without ServiceNow:

```powershell
python test_local.py
```

This runs the incidents through the decision-generation logic and prints the resulting decisions.

## Troubleshooting

### ServiceNow does not reach the FastAPI server

Check that:

* FastAPI is running on port `8000`.
* ngrok is running.
* The Business Rule uses the current ngrok URL.
* The endpoint ends with:

```text
/webhook
```

### The webhook returns `202 Accepted` but nothing happens

Check the FastAPI terminal for errors after the `202 Accepted` response.

The application processes the incident in the background, so the ServiceNow request can return successfully before the LLM and write-back operations finish.

### Groq authentication error

Check that:

```text
GROQ_API_KEY
```

is correctly configured in `.env`.

Do not include quotation marks unless they are required by your environment configuration.

### Groq model error

If the configured model is unavailable, update:

```text
GROQ_MODEL
```

to a model currently available to your Groq account.

### ServiceNow PATCH returns 401 or 403

Check:

* `SNOW_INSTANCE_URL`
* `SNOW_USERNAME`
* `SNOW_PASSWORD`
* ServiceNow permissions
* Required Incident fields
* Valid values for Incident state and resolution fields

### `.env` appears on GitHub

Stop and fix this immediately.

The `.env` file should be ignored by Git and should never contain real API keys or passwords in the repository.

Check:

```powershell
git status
```

and:

```powershell
git ls-files .env
```

The second command should return nothing.

## Security Notes

Never commit:

```text
.env
```

or any file containing:

* Groq API keys
* ServiceNow passwords
* Authentication tokens
* Private credentials

Use `.env.example` to document the required environment variables without exposing real secrets.

## Implementation Summary

The project demonstrates an agentic incident-processing workflow that connects:

* **ServiceNow** for incident creation and management
* **FastAPI** for the webhook service
* **Groq LLM** for incident classification and response decisions
* **Knowledge-base articles** for grounded decision making
* **ngrok** for exposing the local development server
* **ServiceNow REST API** for writing decisions back to the original incident

The system supports three actions:

```text
respond
ask
escalate
```

and applies the corresponding action to the original ServiceNow incident.
