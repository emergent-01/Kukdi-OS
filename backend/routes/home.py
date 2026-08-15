"""Home — a single adaptive surface. State is derived from real signals (today's
events, placement proximity, exams, weekend) unless the user intentionally sets
an override. Home is computed on read; nothing about it is stored.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from ai_engine import reasoning
from context import build_context
from database import db
from models import HOME_STATES, StateOverrideIn, now_iso

router = APIRouter()

_GREETINGS = {
    "quiet": ("A quiet day", "Nothing is urgent. A good day to think, or to rest."),
    "normal": ("Let's make today count", "A steady day ahead. Here's what matters."),
    "busy": ("A full day", "There's a lot on. I'll keep it simple — one thing at a time."),
    "placement": ("Placement season", "The offer is close. Small, consistent prep wins this."),
    "interview": ("Interview ahead", "You've prepared for this. Breathe — you know your stories."),
    "exam": ("Exam mode", "Focus on what's tested. You're consistent once you start."),
    "weekend": ("The weekend", "Space to breathe. Maybe a run would feel good."),
    "overwhelmed": ("Let's slow down", "It's a lot right now. Let's do just the next thing."),
}


def _time_greeting() -> str:
    h = datetime.now(timezone.utc).hour
    # ISB is UTC+5:30; nudge for a roughly-right feel.
    h = (h + 5) % 24
    if h < 12:
        return "Good morning, Little Miss"
    if h < 17:
        return "Good afternoon, Little Miss"
    return "Good evening, Little Miss"


def _derive_state(events, now: datetime) -> str:
    today = now.date()
    todays = [e for e in events if _same_day(e.get("start"), today)]
    next_3d = now + timedelta(days=3)

    if any(e.get("type") == "exam" and _within(e.get("start"), now, timedelta(days=2)) for e in events):
        return "exam"
    if any(e.get("type") == "placement" and _within(e.get("start"), now, timedelta(days=2)) for e in events):
        return "interview"
    if any(e.get("type") == "placement" and _within(e.get("start"), now, timedelta(days=14)) for e in events):
        return "placement"
    if now.weekday() >= 5:
        return "weekend"
    if len(todays) >= 4:
        return "overwhelmed"
    if len(todays) >= 2:
        return "busy"
    if len(todays) == 0:
        return "quiet"
    return "normal"


def _same_day(iso, day):
    if not iso:
        return False
    try:
        return datetime.fromisoformat(iso).date() == day
    except Exception:
        return False


def _within(iso, now, delta):
    if not iso:
        return False
    try:
        dt = datetime.fromisoformat(iso)
        return now <= dt <= now + delta
    except Exception:
        return False


@router.get("")
async def home():
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()

    settings = await db.settings.find_one({"id": "singleton"}, {"_id": 0}) or {}
    events_all = await db.events.find({}, {"_id": 0}).sort("start", 1).to_list(1000)

    override = settings.get("home_state_override")
    state = override if override in HOME_STATES else _derive_state(events_all, now)

    upcoming = [e for e in events_all if (e.get("start") or "") >= now_str][:6]
    todays = [e for e in events_all if _same_day(e.get("start"), now.date())]

    # Focus: the next deadline/placement/exam, framed calmly.
    focus = []
    for e in upcoming:
        if e.get("type") in ("deadline", "placement", "exam"):
            focus.append({
                "title": e["title"],
                "detail": _relative(e.get("start"), now),
                "type": e.get("type"),
            })
        if len(focus) >= 3:
            break

    # Surfaced memories: a couple that feel relevant to the moment.
    prefer_tags = {
        "exam": ["study", "planning"], "interview": ["career", "wellbeing"],
        "placement": ["career", "placements"], "overwhelmed": ["wellbeing", "running"],
        "weekend": ["wellbeing", "running"], "busy": ["planning", "energy"],
    }.get(state, ["wellbeing", "planning"])
    surfaced = await db.memories.find(
        {"status": "active", "tags": {"$in": prefer_tags}}, {"_id": 0}
    ).sort("confidence", -1).to_list(3)
    if not surfaced:
        surfaced = await db.memories.find(
            {"status": "active", "type": {"$in": ["Preference", "Routine", "Insight"]}},
            {"_id": 0},
        ).to_list(2)

    pending = await db.candidates.count_documents({"status": "pending"})
    heading, subtext = _GREETINGS.get(state, _GREETINGS["normal"])

    return {
        "state": state,
        "override": override,
        "greeting": _time_greeting(),
        "heading": heading,
        "subtext": subtext,
        "today": todays,
        "upcoming": upcoming,
        "focus": focus,
        "surfaced_memories": surfaced,
        "pending_candidates": pending,
        "date": now_str,
    }


def _relative(iso, now):
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso)
        days = (dt.date() - now.date()).days
        when = dt.strftime("%-I:%M %p") if hasattr(dt, "strftime") else ""
        if days == 0:
            return f"Today · {when}"
        if days == 1:
            return f"Tomorrow · {when}"
        return f"In {days} days · {dt.strftime('%a')}"
    except Exception:
        return ""


async def _brief_context_state():
    now = datetime.now(timezone.utc)
    settings = await db.settings.find_one({"id": "singleton"}, {"_id": 0}) or {}
    events_all = await db.events.find({}, {"_id": 0}).sort("start", 1).to_list(1000)
    override = settings.get("home_state_override")
    state = override if override in HOME_STATES else _derive_state(events_all, now)
    return settings, state, now


@router.get("/brief")
async def get_brief():
    settings, state, now = await _brief_context_state()
    today_key = now.date().isoformat()
    if settings.get("brief_date") == today_key and settings.get("brief_text"):
        return {"brief": settings["brief_text"], "cached": True}

    context = await build_context()
    text = await reasoning.daily_brief(context, state, _time_greeting())
    await db.settings.update_one(
        {"id": "singleton"},
        {"$set": {"brief_text": text, "brief_date": today_key, "updated": now_iso()}},
        upsert=True,
    )
    return {"brief": text, "cached": False}


@router.post("/brief/refresh")
async def refresh_brief():
    _, state, now = await _brief_context_state()
    context = await build_context()
    text = await reasoning.daily_brief(context, state, _time_greeting())
    await db.settings.update_one(
        {"id": "singleton"},
        {"$set": {"brief_text": text, "brief_date": now.date().isoformat(), "updated": now_iso()}},
        upsert=True,
    )
    return {"brief": text, "cached": False}


@router.post("/state")
async def set_state(body: StateOverrideIn):
    state = body.state if body.state in HOME_STATES else None
    await db.settings.update_one(
        {"id": "singleton"},
        {"$set": {"home_state_override": state, "updated": now_iso()}},
        upsert=True,
    )
    return {"override": state}
