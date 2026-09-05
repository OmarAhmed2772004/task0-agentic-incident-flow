"""
Quick manual check for FR6: runs each ticket in test_incidents.json against
your locally running service (python -m uvicorn app.main:app --reload) and
prints what decision Gemini made for each one.

This does NOT touch ServiceNow - it just exercises the Gemini decision step
directly so you can sanity check it fast, without needing the PDI running.

Usage:
    python test_local.py
"""

import asyncio
import json

from app.gemini_client import get_decision

with open("test_incidents.json", "r", encoding="utf-8") as f:
    tickets = json.load(f)["incidents"]


async def main():
    for t in tickets:
        result = await get_decision(
            short_description=t.get("short_description", ""),
            description=t.get("description", ""),
            priority=t.get("priority", ""),
        )
        expected = t.get("expected_decision", "?")
        got = result["decision"]
        flag = "OK" if got == expected else "MISMATCH"
        print(f"[{flag}] {t.get('short_description')!r}")
        print(f"    expected={expected}  got={got}  message={result['message']!r}\n")


if __name__ == "__main__":
    asyncio.run(main())
