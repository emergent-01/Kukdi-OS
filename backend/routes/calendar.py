"""Calendar — timetable, deadlines, exams, placements, tasks. Natural-language
questions ("what do I have tomorrow?") are answered by the reasoning engine over
the calendar context.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ai_engine import reasoning
from context import build_context
from database import db
from models import AskIn, EventIn, EventUpdate, new_id, now_iso

router = APIRouter()


@router.get("")
async def list_events():
    events = await db.events.find({}, {"_id": 0}).sort("start", 1).to_list(1000)
    now = datetime.now(timezone.utc).isoformat()
    upcoming = [e for e in events if (e.get("start") or "") >= now]
    past = [e for e in events if (e.get("start") or "") < now]
    return {"events": events, "upcoming": upcoming, "past": past}


@router.post("")
async def create_event(body: EventIn):
    doc = body.model_dump()
    doc.update({"id": new_id(), "created": now_iso()})
    await db.events.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/{event_id}")
async def update_event(event_id: str, body: EventUpdate):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    res = await db.events.update_one({"id": event_id}, {"$set": changes})
    if not res.matched_count:
        raise HTTPException(404, "Event not found")
    return await db.events.find_one({"id": event_id}, {"_id": 0})


@router.delete("/{event_id}")
async def delete_event(event_id: str):
    await db.events.delete_one({"id": event_id})
    return {"ok": True}


@router.post("/ask")
async def ask_calendar(body: AskIn):
    context = await build_context()
    context["now"] = now_iso()
    answer = await reasoning.answer(body.question, context)
    return {"answer": answer}
