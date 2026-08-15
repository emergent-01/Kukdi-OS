# Kukdi — A Personal Operating System (PRD)

## Original problem statement
Build Kukdi: an intelligent operating system for ONE human being that reduces cognitive
load and solves mental fragmentation. Not a chatbot, task manager, or Notion clone. The
interface should almost disappear; the intelligence is the product. Version One is
handcrafted for "Little Miss" — an MBA (PGP) student at ISB Mohali aiming for Product
Management roles at Google, Microsoft, Adobe, MakeMyTrip. Premium, editorial, quiet, warm,
minimal design (soft off-white, muted sage). Core principles: context over features, memory
over notes, conversations over forms, guidance over dashboards, calm over notifications.

## User choices (V1)
- Reasoning engine: **Claude Sonnet 4.6** via Emergent LLM key.
- Scope built deeply: Home + Conversation + Memory + **Dream Offer** (flagship). Plus People,
  Calendar (with NL queries), Knowledge.
- **No authentication** (single-user). Data richly **seeded on startup**.
- Design: full creative judgment (editorial/Kinfolk-meets-Apple aesthetic).

## Architecture (and why)
- **Reasoning is a swappable module** (`backend/ai_engine.py`, class `KukdiReasoning`). It is
  the only file that knows an LLM exists. Routes build *context* (`context.py`) and call
  `reasoning.converse()` / `reasoning.answer()`. The UI never depends on the model — swap
  Claude for anything by rewriting one file.
- **Memory is the substrate.** Home, Calendar answers, and conversation context all read from
  memories. Conversation produces **candidate** memories that require explicit confirmation —
  nothing is remembered silently.
- **Home is computed, not stored** (`routes/home.py`): adaptive state derived from real signals
  (today's events, exam/placement proximity, weekend, load) with an intentional user override.
- String UUID ids everywhere; Mongo `_id` always projected out; datetimes stored as ISO UTC.
- FastAPI routers per domain under `/api/*`; single Mongo client in `database.py`.

## Data model / entities
memories, candidates, conversations, messages, companies, prep_items, people, events,
knowledge, settings (singleton). Memory fields: type, title, description, confidence, status,
source, relationships, tags, usable_for, created/updated/last_confirmed.

## Implemented (2026-06 — V1 launch)
- Adaptive **Home** with 8 states + editorial greeting, "What matters", "Today", "On your mind"
  surfaced memories, pending-candidate nudge, conversation pill, live state switcher.
- **Conversation/Talk** — Claude-powered, warm brief replies, contextual awareness, inline
  candidate-memory confirmation.
- **Memory** — full CRUD, edit, "still true" re-confirm, archive ("forget"), type filters,
  search, candidate confirm/dismiss.
- **Dream Offer** — company pipeline (seeded Google/Microsoft/Adobe/MakeMyTrip) with cycling
  stages, prep roadmap/frameworks/stories/cases/resume/networking with status dots, computed
  progress. Add company/prep.
- **People** — editorial relationship cards (Ananya, Rohan, Prof. Nair, Mom), CRUD.
- **Calendar** — schedule grouped by day, add/delete events, natural-language "Ask Kukdi".
- **Knowledge** — notes/books/frameworks/cases with search, view, CRUD.
- Rich idempotent seed on startup. Tested: 18/18 backend + all frontend flows, 100%.

## Backlog
- P1: Semantic search over Knowledge (embeddings) — schema is ready.
- P1: Memory relationships graph (link people ↔ memories ↔ events) surfaced in UI.
- P1: Streaming token-by-token replies in Talk (currently full-response JSON for candidate extraction).
- P2: Multi-user support (deferred deliberately for V1).
- P2: Daily "brief" generation and gentle proactive surfacing.
- P2: iPad note ingestion / document upload into Knowledge (object storage).

## Next tasks
- Consider Talk streaming + a two-pass extract so replies stream while candidates resolve after.
- Add memory↔person↔event relationships and show "who told me that".
