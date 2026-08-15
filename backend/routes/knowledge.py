"""Knowledge — documents, books, notes, frameworks, cases. Substring search now;
the shape is ready for semantic search later.
"""
from fastapi import APIRouter, HTTPException

from database import db
from models import KnowledgeIn, new_id, now_iso

router = APIRouter()


@router.get("")
async def list_knowledge(q: str = None):
    query = {}
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"summary": {"$regex": q, "$options": "i"}},
            {"body": {"$regex": q, "$options": "i"}},
        ]
    items = await db.knowledge.find(query, {"_id": 0}).sort("created", -1).to_list(500)
    return {"items": items}


@router.post("")
async def create_knowledge(body: KnowledgeIn):
    doc = body.model_dump()
    doc.update({"id": new_id(), "created": now_iso()})
    await db.knowledge.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.delete("/{item_id}")
async def delete_knowledge(item_id: str):
    await db.knowledge.delete_one({"id": item_id})
    return {"ok": True}
