"""Conversation — the primary input. Every message may produce candidate
memories, which are persisted (pending) and returned for gentle confirmation.
Kukdi never remembers silently.
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import json

from ai_engine import reasoning
from context import build_context
from database import db
from models import MessageIn, new_id, now_iso
from speech import transcribe_audio

router = APIRouter()


async def _get_or_create_conversation(conversation_id):
    if conversation_id:
        conv = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
        if conv:
            return conv
    conv = {"id": new_id(), "title": "Conversation", "created": now_iso(), "updated": now_iso()}
    await db.conversations.insert_one(conv)
    return conv


@router.post("/message")
async def send_message(body: MessageIn):
    conv = await _get_or_create_conversation(body.conversation_id)

    history = await db.messages.find(
        {"conversation_id": conv["id"]}, {"_id": 0}
    ).sort("created", 1).to_list(50)

    user_msg = {
        "id": new_id(), "conversation_id": conv["id"], "role": "user",
        "text": body.text, "created": now_iso(),
    }
    await db.messages.insert_one({k: v for k, v in user_msg.items()})

    context = await build_context()
    result = await reasoning.converse(history, body.text, context)

    candidates = []
    for c in result["candidates"]:
        cand = {
            "id": new_id(), "conversation_id": conv["id"], "status": "pending",
            "type": c["type"], "title": c["title"], "description": c["description"],
            "confidence": c["confidence"], "tags": c["tags"], "usable_for": c["usable_for"],
            "source": "conversation", "created": now_iso(),
        }
        await db.candidates.insert_one({k: v for k, v in cand.items()})
        candidates.append({k: v for k, v in cand.items() if k != "_id"})

    kukdi_msg = {
        "id": new_id(), "conversation_id": conv["id"], "role": "kukdi",
        "text": result["reply"], "created": now_iso(),
    }
    await db.messages.insert_one({k: v for k, v in kukdi_msg.items()})

    await db.conversations.update_one(
        {"id": conv["id"]}, {"$set": {"updated": now_iso()}}
    )
    if result["detected_state"]:
        await db.settings.update_one(
            {"id": "singleton"},
            {"$set": {"detected_state": result["detected_state"], "updated": now_iso()}},
            upsert=True,
        )

    return {
        "conversation_id": conv["id"],
        "reply": {k: v for k, v in kukdi_msg.items() if k != "_id"},
        "candidates": candidates,
        "detected_state": result["detected_state"],
    }


@router.post("/stream")
async def stream_message(body: MessageIn):
    """SSE: streams Kukdi's reply token by token, then a second pass extracts
    and persists candidate memories, emitted as a final event."""
    conv = await _get_or_create_conversation(body.conversation_id)
    history = await db.messages.find(
        {"conversation_id": conv["id"]}, {"_id": 0}
    ).sort("created", 1).to_list(50)

    user_msg = {
        "id": new_id(), "conversation_id": conv["id"], "role": "user",
        "text": body.text, "created": now_iso(),
    }
    await db.messages.insert_one({k: v for k, v in user_msg.items()})
    context = await build_context()

    async def gen():
        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv['id']})}\n\n"
        full = ""
        async for token in reasoning.stream_reply(history, body.text, context):
            full += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        kukdi_msg = {
            "id": new_id(), "conversation_id": conv["id"], "role": "kukdi",
            "text": full.strip() or "I'm here.", "created": now_iso(),
        }
        await db.messages.insert_one({k: v for k, v in kukdi_msg.items()})
        await db.conversations.update_one({"id": conv["id"]}, {"$set": {"updated": now_iso()}})

        candidates = []
        try:
            extracted = await reasoning.extract_candidates(body.text, full, context)
        except Exception:
            extracted = []
        for c in extracted:
            cand = {
                "id": new_id(), "conversation_id": conv["id"], "status": "pending",
                "type": c["type"], "title": c["title"], "description": c["description"],
                "confidence": c["confidence"], "tags": c["tags"], "usable_for": c["usable_for"],
                "source": "conversation", "created": now_iso(),
            }
            await db.candidates.insert_one({k: v for k, v in cand.items()})
            candidates.append({k: v for k, v in cand.items() if k != "_id"})

        yield f"data: {json.dumps({'type': 'candidates', 'candidates': candidates})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "webm"
    if ext not in ("mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg"):
        raise HTTPException(415, "Unsupported audio format")
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:  # Whisper's own 25 MB limit
        raise HTTPException(413, "Audio too large (max 25 MB)")
    text = await transcribe_audio(data, ext)
    return {"text": text}


@router.get("/messages")
async def latest_messages(conversation_id: str = None):
    conv = None
    if conversation_id:
        conv = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    if not conv:
        conv = await db.conversations.find_one({}, {"_id": 0}, sort=[("updated", -1)])
    if not conv:
        return {"conversation_id": None, "messages": []}
    messages = await db.messages.find(
        {"conversation_id": conv["id"]}, {"_id": 0}
    ).sort("created", 1).to_list(200)
    return {"conversation_id": conv["id"], "messages": messages}
