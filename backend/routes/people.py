"""People — relationship context. Minimal, human, memory-adjacent."""
from fastapi import APIRouter, HTTPException

from database import db
from models import PersonIn, PersonUpdate, new_id, now_iso

router = APIRouter()


@router.get("")
async def list_people():
    people = await db.people.find({}, {"_id": 0}).sort("name", 1).to_list(500)
    return {"people": people}


@router.post("")
async def create_person(body: PersonIn):
    doc = body.model_dump()
    doc.update({"id": new_id(), "created": now_iso(), "updated": now_iso()})
    await db.people.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/{person_id}")
async def update_person(person_id: str, body: PersonUpdate):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    changes["updated"] = now_iso()
    res = await db.people.update_one({"id": person_id}, {"$set": changes})
    if not res.matched_count:
        raise HTTPException(404, "Person not found")
    return await db.people.find_one({"id": person_id}, {"_id": 0})


@router.delete("/{person_id}")
async def delete_person(person_id: str):
    await db.people.delete_one({"id": person_id})
    return {"ok": True}
