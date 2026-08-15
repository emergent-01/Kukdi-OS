"""Kukdi domain model.

Design notes
------------
- We use string UUIDs as the primary `id` on every document and never expose
  Mongo's `_id` (queries always project it out). This sidesteps ObjectId JSON
  serialization entirely and keeps ids stable across imports/exports.
- Datetimes are stored as ISO-8601 strings (UTC). The whole product reasons in
  ISO strings so the boundary between DB, API and LLM context is one format.
- Request bodies are Pydantic models (validation at the edge). Stored documents
  are plain dicts assembled by the routes — we don't over-model internal shapes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----- Controlled vocabularies (kept as data, not enums, so they're easy to
# extend and to feed to the reasoning engine as guidance) --------------------

MEMORY_TYPES = [
    "Profile", "Preference", "Goal", "Person", "Routine", "Habit",
    "Academic", "Career", "Decision", "Insight", "Context", "Event",
]

HOME_STATES = [
    "quiet", "normal", "busy", "placement", "interview", "exam",
    "weekend", "overwhelmed",
]

COMPANY_STAGES = ["researching", "networking", "applied", "interviewing", "offer", "closed"]
COMPANY_TIERS = ["dream", "target", "safe"]
PREP_CATEGORIES = ["framework", "story", "case", "resume", "networking", "roadmap", "daily"]
EVENT_TYPES = ["class", "deadline", "exam", "event", "task", "placement"]


# ----- Request models --------------------------------------------------------

class MessageIn(BaseModel):
    text: str
    conversation_id: Optional[str] = None


class MemoryIn(BaseModel):
    type: str = "Insight"
    title: str
    description: str = ""
    confidence: float = 0.8
    status: str = "active"
    source: str = "manual"
    tags: List[str] = Field(default_factory=list)
    usable_for: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    usable_for: Optional[List[str]] = None


class CandidateDecision(BaseModel):
    # Optional edits applied at confirmation time.
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None


class LinkIn(BaseModel):
    kind: str  # person | event | memory
    ref_id: str
    label: str = ""


class CompanyIn(BaseModel):
    name: str
    tier: str = "target"
    role: str = "Product Manager"
    stage: str = "researching"
    location: str = ""
    notes: str = ""
    next_action: str = ""


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    role: Optional[str] = None
    stage: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    next_action: Optional[str] = None


class PrepItemIn(BaseModel):
    category: str = "roadmap"
    title: str
    content: str = ""
    status: str = "todo"  # todo | doing | done
    company_id: Optional[str] = None


class PrepItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None


class PersonIn(BaseModel):
    name: str
    relation: str = ""
    company: str = ""
    birthday: str = ""
    notes: str = ""
    important: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    company: Optional[str] = None
    birthday: Optional[str] = None
    notes: Optional[str] = None
    important: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class EventIn(BaseModel):
    type: str = "event"
    title: str
    start: str
    end: Optional[str] = None
    location: str = ""
    course: str = ""
    notes: str = ""
    done: bool = False


class EventUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    done: Optional[bool] = None


class KnowledgeIn(BaseModel):
    kind: str = "note"  # note | book | framework | case | document
    title: str
    summary: str = ""
    body: str = ""
    tags: List[str] = Field(default_factory=list)


class AskIn(BaseModel):
    question: str


class CountdownGenerateIn(BaseModel):
    company_id: Optional[str] = None
    target_date: Optional[str] = None


class TaskToggleIn(BaseModel):
    done: bool


class StateOverrideIn(BaseModel):
    state: Optional[str] = None  # null clears the override
