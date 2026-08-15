"""Memory — the foundation. Fully editable, always transparent. Candidate
memories (from conversation) are confirmed or dismissed here.
"""
from fastapi import APIRouter, HTTPException

from database import db
from models import (CandidateDecision, LinkIn, MemoryIn, MemoryUpdate, new_id,
                   now_iso)

router = APIRouter()


@router.get("")
async def list_memories(type: str = None, q: str = None):
    query = {"status": {"$ne": "archived"}}
    if type:
        query["type"] = type
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    items = await db.memories.find(query, {"_id": 0}).sort("updated", -1).to_list(500)
    types = await db.memories.distinct("type", {"status": {"$ne": "archived"}})
    return {"memories": items, "types": types}


@router.post("")
async def create_memory(body: MemoryIn):
    doc = body.model_dump()
    doc.update({
        "id": new_id(), "relationships": doc.get("relationships", []),
        "created": now_iso(), "updated": now_iso(), "last_confirmed": now_iso(),
    })
    await db.memories.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/{memory_id}")
async def update_memory(memory_id: str, body: MemoryUpdate):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(400, "No changes")
    changes["updated"] = now_iso()
    res = await db.memories.update_one({"id": memory_id}, {"$set": changes})
    if not res.matched_count:
        raise HTTPException(404, "Memory not found")
    return await db.memories.find_one({"id": memory_id}, {"_id": 0})


@router.post("/{memory_id}/confirm")
async def confirm_memory(memory_id: str):
    res = await db.memories.update_one(
        {"id": memory_id}, {"$set": {"last_confirmed": now_iso(), "updated": now_iso()}}
    )
    if not res.matched_count:
        raise HTTPException(404, "Memory not found")
    return await db.memories.find_one({"id": memory_id}, {"_id": 0})


@router.delete("/{memory_id}")
async def archive_memory(memory_id: str):
    await db.memories.update_one(
        {"id": memory_id}, {"$set": {"status": "archived", "updated": now_iso()}}
    )
    return {"ok": True}


async def _resolve_links(relationships):
    resolved = []
    for r in relationships or []:
        kind, ref = r.get("kind"), r.get("ref_id")
        label = r.get("label")
        if not label:
            if kind == "person":
                doc = await db.people.find_one({"id": ref}, {"_id": 0})
                label = doc["name"] if doc else "Unknown"
            elif kind == "event":
                doc = await db.events.find_one({"id": ref}, {"_id": 0})
                label = doc["title"] if doc else "Unknown"
            elif kind == "memory":
                doc = await db.memories.find_one({"id": ref}, {"_id": 0})
                label = doc["title"] if doc else "Unknown"
        resolved.append({"kind": kind, "ref_id": ref, "label": label})
    return resolved


@router.get("/{memory_id}")
async def get_memory(memory_id: str):
    m = await db.memories.find_one({"id": memory_id}, {"_id": 0})
    if not m:
        raise HTTPException(404, "Memory not found")
    m["connections"] = await _resolve_links(m.get("relationships", []))
    return m


@router.post("/{memory_id}/link")
async def link_memory(memory_id: str, body: LinkIn):
    m = await db.memories.find_one({"id": memory_id}, {"_id": 0})
    if not m:
        raise HTTPException(404, "Memory not found")
    rels = [r for r in (m.get("relationships") or []) if r.get("ref_id") != body.ref_id]
    rels.append({"kind": body.kind, "ref_id": body.ref_id, "label": body.label})
    await db.memories.update_one(
        {"id": memory_id}, {"$set": {"relationships": rels, "updated": now_iso()}}
    )
    return {"connections": await _resolve_links(rels)}


@router.post("/{memory_id}/unlink")
async def unlink_memory(memory_id: str, body: LinkIn):
    m = await db.memories.find_one({"id": memory_id}, {"_id": 0})
    if not m:
        raise HTTPException(404, "Memory not found")
    rels = [r for r in (m.get("relationships") or []) if r.get("ref_id") != body.ref_id]
    await db.memories.update_one(
        {"id": memory_id}, {"$set": {"relationships": rels, "updated": now_iso()}}
    )
    return {"connections": await _resolve_links(rels)}


# ----- Candidate memories ----------------------------------------------------

@router.get("/candidates/pending")
async def pending_candidates():
    items = await db.candidates.find(
        {"status": "pending"}, {"_id": 0}
    ).sort("created", -1).to_list(100)
    return {"candidates": items}


@router.post("/candidates/{candidate_id}/confirm")
async def confirm_candidate(candidate_id: str, body: CandidateDecision):
    cand = await db.candidates.find_one({"id": candidate_id}, {"_id": 0})
    if not cand:
        raise HTTPException(404, "Candidate not found")
    memory = {
        "id": new_id(),
        "type": body.type or cand["type"],
        "title": body.title or cand["title"],
        "description": body.description or cand["description"],
        "confidence": cand.get("confidence", 0.7),
        "status": "active", "source": "conversation", "relationships": [],
        "tags": cand.get("tags", []), "usable_for": cand.get("usable_for", []),
        "created": now_iso(), "updated": now_iso(), "last_confirmed": now_iso(),
    }
    await db.memories.insert_one({k: v for k, v in memory.items()})
    await db.candidates.update_one(
        {"id": candidate_id}, {"$set": {"status": "confirmed"}}
    )
    return {k: v for k, v in memory.items() if k != "_id"}


@router.post("/candidates/{candidate_id}/dismiss")
async def dismiss_candidate(candidate_id: str):
    await db.candidates.update_one(
        {"id": candidate_id}, {"$set": {"status": "dismissed"}}
    )
    return {"ok": True}
