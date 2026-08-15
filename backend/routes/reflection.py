"""Weekly Reflection — a gentle Sunday recap in Kukdi's voice. Derives real signals
from the week and lets the reasoning engine narrate them. Cached per ISO week.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from ai_engine import reasoning
from context import build_context
from database import db
from models import now_iso

router = APIRouter()


async def _week_stats():
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    confirmed = await db.memories.count_documents({"last_confirmed": {"$gte": week_ago}})
    prep = await db.prep_items.find({}, {"_id": 0}).to_list(500)
    done = [p for p in prep if p.get("status") == "done"]
    doing = [p for p in prep if p.get("status") == "doing"]

    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    past_week = [e for e in events if week_ago <= (e.get("start") or "") <= now.isoformat()]
    next_week = [
        e for e in events
        if now.isoformat() <= (e.get("start") or "") <= (now + timedelta(days=7)).isoformat()
    ]
    companies = await db.companies.find({}, {"_id": 0}).to_list(200)
    active = [c["name"] for c in companies if c.get("stage") in ("interviewing", "offer")]

    return {
        "memories_confirmed": confirmed,
        "prep_done": len(done),
        "prep_in_progress": [p["title"] for p in doing][:4],
        "attended_this_week": [e["title"] for e in past_week][:6],
        "coming_up": [e["title"] for e in next_week][:6],
        "companies_in_motion": active,
    }


@router.get("/weekly")
async def weekly(refresh: bool = False):
    now = datetime.now(timezone.utc)
    week_key = f"{now.isocalendar().year}-W{now.isocalendar().week}"
    settings = await db.settings.find_one({"id": "singleton"}, {"_id": 0}) or {}

    if not refresh and settings.get("reflection_week") == week_key and settings.get("reflection_text"):
        return {"reflection": settings["reflection_text"], "stats": settings.get("reflection_stats", {}), "cached": True}

    stats = await _week_stats()
    context = await build_context()
    text = await reasoning.weekly_reflection(context, stats)
    await db.settings.update_one(
        {"id": "singleton"},
        {"$set": {"reflection_text": text, "reflection_week": week_key,
                  "reflection_stats": stats, "updated": now_iso()}},
        upsert=True,
    )
    return {"reflection": text, "stats": stats, "cached": False}
