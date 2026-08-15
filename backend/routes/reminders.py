"""Smart Reminders — calm, derived nudges. Kukdi surfaces the right thing at the
right moment (a nearing deadline, a friend's birthday, an open next-step) rather
than a notification firehose. Reminders are COMPUTED, not stored; only dismissals
persist. Aligns with the 'calm over notifications' principle.
"""
from datetime import datetime, timezone

from fastapi import APIRouter

from database import db
from models import ReminderDismissIn, now_iso

router = APIRouter()

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _days_until_birthday(bstr: str):
    if not bstr:
        return None
    today = datetime.now(timezone.utc).date()
    month = day = None

    # ISO form (YYYY-MM-DD or MM-DD)
    iso = bstr.strip()
    if "-" in iso and "/" not in iso:
        bits = iso.split("-")
        try:
            if len(bits) == 3:
                month, day = int(bits[1]), int(bits[2])
            elif len(bits) == 2:
                month, day = int(bits[0]), int(bits[1])
        except ValueError:
            month = day = None

    if not month or not day:
        parts = bstr.replace(",", " ").split()
        for p in parts:
            pl = p.strip().lower()
            if pl in _MONTHS:
                month = _MONTHS[pl]
            elif pl.isdigit():
                day = int(pl)

    if not month or not day:
        return None
    try:
        this_year = today.replace(month=month, day=day)
    except ValueError:
        return None
    if this_year < today:
        try:
            this_year = this_year.replace(year=today.year + 1)
        except ValueError:
            return None
    return (this_year - today).days


def _relative(days: int) -> str:
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    return f"In {days} days"


async def _compute():
    now = datetime.now(timezone.utc)
    now_iso_str = now.isoformat()
    reminders = []

    events = await db.events.find({}, {"_id": 0}).sort("start", 1).to_list(1000)
    for e in events:
        start = e.get("start") or ""
        if start < now_iso_str:
            continue
        try:
            dt = datetime.fromisoformat(start)
        except Exception:
            continue
        days = (dt.date() - now.date()).days
        if e.get("type") in ("deadline", "exam", "placement", "interview") and days <= 5:
            priority = 100 - days * 10
            reminders.append({
                "id": f"event:{e['id']}",
                "kind": e["type"],
                "title": e["title"],
                "detail": _relative(days),
                "days": days,
                "priority": priority,
            })

    people = await db.people.find({}, {"_id": 0}).to_list(500)
    for p in people:
        d = _days_until_birthday(p.get("birthday", ""))
        if d is not None and d <= 21:
            reminders.append({
                "id": f"birthday:{p['id']}",
                "kind": "birthday",
                "title": f"{p['name']}'s birthday",
                "detail": _relative(d),
                "days": d,
                "priority": 90 - d,
            })

    companies = await db.companies.find({}, {"_id": 0}).to_list(200)
    for c in companies:
        if c.get("next_action") and c.get("stage") in ("applied", "interviewing", "networking"):
            reminders.append({
                "id": f"action:{c['id']}",
                "kind": "next-step",
                "title": f"{c['name']} · {c['next_action']}",
                "detail": "Open next step",
                "days": 99,
                "priority": 40,
            })

    settings = await db.settings.find_one({"id": "singleton"}, {"_id": 0}) or {}
    dismissed = set(settings.get("dismissed_reminders", []))
    snoozed = settings.get("snoozed_reminders", {}) or {}
    today = datetime.now(timezone.utc).date().isoformat()
    reminders = [
        r for r in reminders
        if r["id"] not in dismissed and snoozed.get(r["id"], "") <= today
    ]
    reminders.sort(key=lambda r: (-r["priority"], r["days"]))
    return reminders


@router.get("")
async def list_reminders():
    return {"reminders": await _compute()}


@router.post("/dismiss")
async def dismiss(body: ReminderDismissIn):
    await db.settings.update_one(
        {"id": "singleton"},
        {"$addToSet": {"dismissed_reminders": body.id}, "$set": {"updated": now_iso()}},
        upsert=True,
    )
    return {"reminders": await _compute()}


@router.post("/snooze")
async def snooze(body: ReminderDismissIn):
    from datetime import timedelta
    tomorrow = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
    await db.settings.update_one(
        {"id": "singleton"},
        {"$set": {f"snoozed_reminders.{body.id}": tomorrow, "updated": now_iso()}},
        upsert=True,
    )
    return {"reminders": await _compute()}
