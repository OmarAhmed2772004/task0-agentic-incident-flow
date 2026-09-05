"""
Calls the Groq API (OpenAI-compatible) to make ONE decision: respond / ask / escalate.
Uses only the five knowledge articles in kb_articles.json - nothing else.

NOTE: The assignment asked for the Gemini LLM. We switched to Groq because
Google was issuing broken 'AQ.'-prefixed API keys during this project window,
blocking every Gemini key we tried (confirmed as a known, widespread Google-side
issue, not a config mistake). Groq is used here as a drop-in replacement with
the exact same prompt/JSON contract - this is called out in reflection.md.
"""

import json
import os
import pathlib
import re

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
KB_PATH = BASE_DIR / "kb_articles.json"
PROMPT_TEMPLATE_PATH = BASE_DIR / "prompt.txt"

VALID_DECISIONS = {"respond", "ask", "escalate"}


def _load_kb_articles() -> list[dict]:
    """kb_articles.json looks like {"description": "...", "articles": [...]}."""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["articles"]


def _load_prompt_template() -> str:
    with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(short_description: str, description: str, priority: int) -> str:
    """Builds the exact prompt string sent to the LLM. Keep this in sync with
    prompt.txt, which is committed to the repo as the FR-required deliverable."""
    kb_articles = _load_kb_articles()
    template = _load_prompt_template()
    return template.format(
        kb_articles_json=json.dumps(kb_articles, indent=2),
        short_description=short_description,
        description=description or "(no description provided)",
        priority=priority,
    )


def _extract_json(text: str) -> dict:
    """Strip ```json fences if the model adds them, then parse."""
    cleaned = re.sub(r"^```json\s*|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


async def get_decision(short_description: str, description: str, priority: int) -> dict:
    """Returns {"decision": "respond"|"ask"|"escalate", "message": "..."}"""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set in the environment.")

    prompt = build_prompt(short_description, description, priority)

    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GROQ_URL,
            json=body,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    try:
        text = data["choices"][0]["message"]["content"]
        result = _extract_json(text)
        decision = str(result.get("decision", "")).strip().lower()
        message = str(result.get("message", "")).strip()
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Could not parse LLM response: {e}. Raw: {data}")

    if decision not in VALID_DECISIONS or not message:
        decision, message = "escalate", "Could not confidently match this to a known article."

    return {"decision": decision, "message": message}
