"""
Task 0 - Agentic Incident Flow
FastAPI webhook service.

Flow:
  ServiceNow Business Rule --> POST /webhook --> 202 immediately
                                        |
                                        v (background task)
                                  Gemini decides: respond / ask / escalate
                                        |
                                        v
                                ServiceNow REST API write-back
"""

import logging
import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from app.gemini_client import get_decision
from app.servicenow_client import write_back

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("task0")

app = FastAPI(title="Agentic Incident Flow - Task 0")

# --- In-memory guard against double processing (FR5) ---------------------
# Good enough for this task. A restart clears it, which is fine for a demo.
_processed_incident_ids: set[str] = set()


# --- Payload contract (must match payload_contract.json exactly) ---------
class IncidentPayload(BaseModel):
    incident_sys_id: str = Field(..., min_length=1)
    number: str = Field(..., min_length=1)
    short_description: str = Field(..., min_length=1)
    description: str = ""
    priority: int = Field(default=3, ge=1, le=5)


@app.get("/")
def health():
    return {"status": "ok", "service": "task0-webhook"}


@app.post("/webhook", status_code=202)
async def webhook(request: Request, background_tasks: BackgroundTasks):
    # Parse and validate the incoming payload ourselves so we can return a
    # clear, controlled error instead of FastAPI's default 422 (NFR3).
    try:
        raw = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body is not valid JSON.")

    try:
        payload = IncidentPayload(**raw)
    except ValidationError as e:
        logger.warning("Bad payload received: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e.errors()}")

    # De-duplication (FR5): if we've already accepted this incident, no-op.
    if payload.incident_sys_id in _processed_incident_ids:
        logger.info("Duplicate incident %s ignored.", payload.number)
        return {"status": "duplicate_ignored", "number": payload.number}

    _processed_incident_ids.add(payload.incident_sys_id)

    # NFR1: respond fast, do the slow work (Gemini + write-back) after.
    background_tasks.add_task(process_incident, payload)
    logger.info("Accepted incident %s, processing in background.", payload.number)
    return {"status": "accepted", "number": payload.number}


async def process_incident(payload: IncidentPayload):
    """Runs after the HTTP response has already been sent."""
    try:
        decision = await get_decision(
            short_description=payload.short_description,
            description=payload.description,
            priority=payload.priority,
        )
        logger.info("Incident %s -> decision=%s", payload.number, decision.get("decision"))

        await write_back(
            incident_sys_id=payload.incident_sys_id,
            decision=decision["decision"],
            message=decision["message"],
        )
        logger.info("Incident %s written back to ServiceNow.", payload.number)

    except Exception as e:
        # Never crash the service (NFR3). Log it, move on.
        logger.exception("Failed to process incident %s: %s", payload.number, e)
