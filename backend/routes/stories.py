"""Story Bank — shape a STAR story once, polish it with Kukdi, reuse it across
every company. Structured so a single strong story can be tagged by theme and
mapped to the companies it's been used for.
"""
from fastapi import APIRouter, HTTPException

from ai_engine import reasoning
from database import db
from models import StoryIn, StoryUpdate, new_id, now_iso

router = APIRouter()


@router.get("")
async def list_stories():
    stories = await db.stories.find({}, {"_id": 0}).sort("updated", -1).to_list(500)
    return {"stories": stories}


@router.post("")
async def create_story(body: StoryIn):
    doc = body.model_dump()
    doc.update({"id": new_id(), "feedback": "", "created": now_iso(), "updated": now_iso()})
    await db.stories.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/{story_id}")
async def update_story(story_id: str, body: StoryUpdate):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(400, "No changes")
    changes["updated"] = now_iso()
    res = await db.stories.update_one({"id": story_id}, {"$set": changes})
    if not res.matched_count:
        raise HTTPException(404, "Story not found")
    return await db.stories.find_one({"id": story_id}, {"_id": 0})


@router.post("/{story_id}/polish")
async def polish_story(story_id: str):
    story = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not story:
        raise HTTPException(404, "Story not found")
    polished = await reasoning.polish_story(story)
    await db.stories.update_one(
        {"id": story_id},
        {"$set": {
            "situation": polished["situation"], "task": polished["task"],
            "action": polished["action"], "result": polished["result"],
            "feedback": polished["feedback"], "status": "polished",
            "updated": now_iso(),
        }},
    )
    return await db.stories.find_one({"id": story_id}, {"_id": 0})


@router.delete("/{story_id}")
async def delete_story(story_id: str):
    await db.stories.delete_one({"id": story_id})
    return {"ok": True}
