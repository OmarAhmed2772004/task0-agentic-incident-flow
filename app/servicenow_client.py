"""
Writes the decision back onto the same incident in ServiceNow via the
Table API, using HTTP Basic Auth.

Field mapping per FR4:
  respond  -> close_notes = message, incident is resolved (state=6, closed by=Solved)
  ask      -> comments    = message  (customer-visible)
  escalate -> work_notes  = message  (internal only)
"""

import os

import httpx

SNOW_INSTANCE_URL = os.environ.get("SNOW_INSTANCE_URL", "").rstrip("/")
SNOW_USERNAME = os.environ.get("SNOW_USERNAME", "")
SNOW_PASSWORD = os.environ.get("SNOW_PASSWORD", "")

# ServiceNow standard incident state values
STATE_RESOLVED = "6"
RESOLUTION_CODE_SOLVED = "Solution provided"


async def write_back(incident_sys_id: str, decision: str, message: str):
    if not (SNOW_INSTANCE_URL and SNOW_USERNAME and SNOW_PASSWORD):
        raise RuntimeError("ServiceNow credentials are not set in the environment.")

    url = f"{SNOW_INSTANCE_URL}/api/now/table/incident/{incident_sys_id}"

    if decision == "respond":
        body = {
            "work_notes": message,
            "close_notes": message,
            "close_code": RESOLUTION_CODE_SOLVED,
            "state": STATE_RESOLVED,
        }
    elif decision == "ask":
        body = {"comments": message}  # customer-visible
    elif decision == "escalate":
        body = {"work_notes": f"Escalated by AI agent: {message}"}  # internal only
    else:
        raise ValueError(f"Unknown decision: {decision}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.patch(
            url,
            json=body,
            auth=(SNOW_USERNAME, SNOW_PASSWORD),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()
