"""Dream Offer — the flagship placement-prep module. Companies form an editorial
pipeline; prep items form a learning roadmap and daily practice. Progress is
computed, never stored.
"""
from fastapi import APIRouter, HTTPException

from database import db
from models import (COMPANY_STAGES, CompanyIn, CompanyUpdate, PrepItemIn,
                    PrepItemUpdate, new_id, now_iso)

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
