"""Assembles the context Kukdi reasons over. This is the seam between the DB and
the reasoning engine — routes call `build_context()` and hand the result to
`reasoning`. Keeping it here means the engine stays pure and the queries live in
one place.
"""
from __future__ import annotations

from datetime import datetime, timezone

from database import db


async def build_context() -> dict:
    memories = await db.memories.find(
        {"status": "active"}, {"_id": 0}
    ).sort("confidence", -1).to_list(60)

    now = datetime.now(timezone.utc).isoformat()
    events = await db.events.find(
        {"start": {"$gte": now}}, {"_id": 0}
    ).sort("start", 1).to_list(20)

    profile = next(
        (m["description"] for m in memories if m.get("type") == "Profile"),
        "Little Miss, MBA (PGP) student at ISB Mohali, aspiring Product Manager.",
    )
    return {"profile": profile, "memories": memories, "events": events}
