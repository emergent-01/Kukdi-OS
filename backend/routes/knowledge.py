"""Knowledge — documents, books, notes, frameworks, cases, plus the iPad Notes
Inbox (file/PDF uploads via Emergent Object Storage). Substring search now; the
shape is ready for semantic search later.
"""
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from database import db
from models import KnowledgeIn, new_id, now_iso
from storage import APP_NAME, MIME_TYPES, extract_text, get_object, put_object

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


@router.post("/upload")
async def upload_knowledge(file: UploadFile = File(...), title: str = None):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "bin"
    data = await file.read()
    content_type = file.content_type or MIME_TYPES.get(ext, "application/octet-stream")
    path = f"{APP_NAME}/uploads/{uuid.uuid4()}.{ext}"
    result = put_object(path, data, content_type)

    body_text = extract_text(data, ext)
    kind = "document" if ext == "pdf" else "note"
    doc = {
        "id": new_id(),
        "kind": kind,
        "title": title or file.filename,
        "summary": f"Uploaded from iPad · {file.filename}",
        "body": body_text,
        "tags": ["upload"],
        "file_path": result["path"],
        "file_url": f"/api/knowledge/files/{result['path']}",
        "original_filename": file.filename,
        "content_type": content_type,
        "created": now_iso(),
    }
    await db.knowledge.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.get("/files/{path:path}")
async def download_file(path: str):
    record = await db.knowledge.find_one({"file_path": path}, {"_id": 0})
    if not record:
        raise HTTPException(404, "File not found")
    data, content_type = get_object(path)
    return Response(content=data, media_type=record.get("content_type", content_type))


@router.delete("/{item_id}")
async def delete_knowledge(item_id: str):
    await db.knowledge.delete_one({"id": item_id})
    return {"ok": True}
