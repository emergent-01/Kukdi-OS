"""Dream Offer — the flagship placement-prep module. Companies form an editorial
pipeline; prep items form a learning roadmap and daily practice. Progress is
computed, never stored.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from ai_engine import reasoning
from context import build_context
from database import db
from models import (COMPANY_STAGES, CompanyIn, CompanyUpdate, CountdownGenerateIn,
                    PrepItemIn, PrepItemUpdate, TaskToggleIn, new_id, now_iso)

router = APIRouter()


@router.get("/overview")
async def overview():
    companies = await db.companies.find({}, {"_id": 0}).sort("created", 1).to_list(200)
    prep = await db.prep_items.find({}, {"_id": 0}).sort("created", 1).to_list(500)

    total = len(prep)
    done = len([p for p in prep if p.get("status") == "done"])
    doing = len([p for p in prep if p.get("status") == "doing"])
    progress = round((done + 0.5 * doing) / total * 100) if total else 0

    stage_counts = {s: 0 for s in COMPANY_STAGES}
    for c in companies:
        stage_counts[c.get("stage", "researching")] = stage_counts.get(c.get("stage", "researching"), 0) + 1

    by_category = {}
    for p in prep:
        by_category.setdefault(p.get("category", "roadmap"), []).append(p)

    return {
        "companies": companies,
        "prep_by_category": by_category,
        "progress": progress,
        "stage_counts": stage_counts,
        "counts": {"companies": len(companies), "prep_done": done, "prep_total": total},
    }


@router.post("/companies")
async def create_company(body: CompanyIn):
    doc = body.model_dump()
    doc.update({"id": new_id(), "created": now_iso(), "updated": now_iso()})
    await db.companies.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/companies/{company_id}")
async def update_company(company_id: str, body: CompanyUpdate):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    changes["updated"] = now_iso()
    res = await db.companies.update_one({"id": company_id}, {"$set": changes})
    if not res.matched_count:
        raise HTTPException(404, "Company not found")
    return await db.companies.find_one({"id": company_id}, {"_id": 0})


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str):
    await db.companies.delete_one({"id": company_id})
    return {"ok": True}


@router.post("/prep")
async def create_prep(body: PrepItemIn):
    doc = body.model_dump()
    doc.update({"id": new_id(), "created": now_iso(), "updated": now_iso()})
    await db.prep_items.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/prep/{prep_id}")
async def update_prep(prep_id: str, body: PrepItemUpdate):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    changes["updated"] = now_iso()
    res = await db.prep_items.update_one({"id": prep_id}, {"$set": changes})
    if not res.matched_count:
        raise HTTPException(404, "Prep item not found")
    return await db.prep_items.find_one({"id": prep_id}, {"_id": 0})


@router.delete("/prep/{prep_id}")
async def delete_prep(prep_id: str):
    await db.prep_items.delete_one({"id": prep_id})
    return {"ok": True}


# ----- Interview Countdown ---------------------------------------------------

def _days_remaining(target_iso: str) -> int:
    try:
        target = datetime.fromisoformat(target_iso)
        return max(0, (target.date() - datetime.now(timezone.utc).date()).days)
    except Exception:
        return 0


async def _serialize_countdown(plan):
    if not plan:
        return None
    total = sum(len(d.get("tasks", [])) for d in plan.get("days", []))
    done = sum(1 for d in plan.get("days", []) for t in d.get("tasks", []) if t.get("done"))
    return {
        "company": plan.get("company"),
        "role": plan.get("role"),
        "target_date": plan.get("target_date"),
        "days_remaining": _days_remaining(plan.get("target_date", "")),
        "days": plan.get("days", []),
        "progress": round(done / total * 100) if total else 0,
        "tasks_done": done,
        "tasks_total": total,
    }


@router.get("/countdown")
async def get_countdown():
    plan = await db.countdowns.find_one({"id": "active"}, {"_id": 0})
    return {"countdown": await _serialize_countdown(plan)}


@router.post("/countdown/generate")
async def generate_countdown(body: CountdownGenerateIn):
    company_name, role, target_date = "Google", "Product Manager", None

    if body.company_id:
        c = await db.companies.find_one({"id": body.company_id}, {"_id": 0})
        if not c:
            raise HTTPException(404, "Company not found")
        company_name, role = c["name"], c.get("role", role)

    if body.target_date:
        target_date = body.target_date
    else:
        now = datetime.now(timezone.utc).isoformat()
        placement = await db.events.find_one(
            {"type": {"$in": ["placement", "interview"]}, "start": {"$gte": now}},
            {"_id": 0}, sort=[("start", 1)],
        )
        if placement:
            target_date = placement["start"]
            if not body.company_id:
                for cn in ("Google", "Microsoft", "Adobe", "MakeMyTrip"):
                    if cn.lower() in placement["title"].lower():
                        company_name = cn
    if not target_date:
        target_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    remaining = max(1, _days_remaining(target_date))

    existing = await db.countdowns.find_one({"id": "active"}, {"_id": 0})
    done_focus = []
    if existing:
        for d in existing.get("days", []):
            if all(t.get("done") for t in d.get("tasks", [])) and d.get("tasks"):
                done_focus.append(d.get("focus", ""))

    context = await build_context()
    raw_days = await reasoning.interview_plan(company_name, role, remaining, done_focus, context)
    if not raw_days:
        # Resilient fallback so the UI never sees a broken plan on LLM failure.
        raw_days = [
            {"focus": "Product sense & structure", "tasks": ["Practice one product design case out loud using CIRCLES", "Review your two strongest stories"]},
            {"focus": "Metrics & prioritisation", "tasks": ["Work through one metrics/estimation prompt", "Draft a RICE prioritisation for a feature"]},
            {"focus": "Confidence & reset", "tasks": ["Do one timed mock", "Go for a run, then sleep early"]},
        ][:remaining]

    start = datetime.now(timezone.utc)
    days = []
    for i, d in enumerate(raw_days):
        day_date = (start + timedelta(days=i)).date().isoformat()
        days.append({
            "id": new_id(),
            "date": day_date,
            "focus": d.get("focus", f"Day {i + 1}"),
            "tasks": [{"id": new_id(), "text": t, "done": False} for t in (d.get("tasks", []) or [])],
        })

    plan = {
        "id": "active", "company": company_name, "role": role,
        "target_date": target_date, "days": days, "created": now_iso(),
    }
    await db.countdowns.replace_one({"id": "active"}, plan, upsert=True)
    return {"countdown": await _serialize_countdown(plan)}


@router.patch("/countdown/task/{task_id}")
async def toggle_countdown_task(task_id: str, body: TaskToggleIn):
    plan = await db.countdowns.find_one({"id": "active"}, {"_id": 0})
    if not plan:
        raise HTTPException(404, "No active countdown")
    for d in plan.get("days", []):
        for t in d.get("tasks", []):
            if t["id"] == task_id:
                t["done"] = body.done
    await db.countdowns.replace_one({"id": "active"}, plan)
    return {"countdown": await _serialize_countdown(plan)}
