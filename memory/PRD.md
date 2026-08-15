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

## Implemented (2026-06 — V1.3)
- **Smart Reminders** — calm, derived, dismissable nudges on Home (`GET /api/reminders`,
  `POST /api/reminders/dismiss`): nearing deadlines/exams/placements, friends' birthdays
  (within 21 days; parses "Month Day" and ISO dates), and open company next-steps. Computed,
  not stored; only dismissals persist. Honours "calm over notifications".
- **Story Bank** — structured STAR stories (`/stories`, `/api/stories` CRUD) tagged by theme and
  companies used; **"Polish with Kukdi"** (`POST /api/stories/{id}/polish`) refines each STAR
  part via Claude and returns a warm coaching note. Shape once, reuse everywhere.
- Tested: frontend 100%, backend 100% (6/6). No defects.

## Implemented (2026-06 — V1.2)
- **Semantic Search** (Knowledge) — "By meaning" mode; the reasoning engine ranks saved
  notes/PDFs by intent (finds CIRCLES for "how to structure a design interview answer") with
  a short "why it matched" for each. `POST /api/knowledge/search`.
- **Voice Capture** (Talk) — mic button records via MediaRecorder → `POST /api/conversation/transcribe`
  (OpenAI Whisper whisper-1) → transcript is sent as a normal streamed message. Size/format guarded.
- **Weekly Reflection** — `/reflection` page + `GET /api/reflection/weekly`: a warm Sunday recap
  in Kukdi's voice derived from real weekly signals, cached per ISO week, refreshable.
- **Interview Countdown** (Dream Offer) — `POST /api/dream/countdown/generate` builds an adaptive
  day-by-day PM prep plan toward the next placement round; tappable tasks recompute progress;
  "Reshape plan" regenerates around what's done. Has a resilient fallback plan on LLM failure.
- Tested: frontend 100%; backend 93% (only by-design LLM dedup flakiness on legacy tests).

## Implemented (2026-06 — V1.1)
- **Streaming replies** in Talk — Kukdi's answer appears token by token over SSE
  (`/api/conversation/stream`); candidate extraction runs as a resilient second pass
  (guarded so the UI never hangs).
- **Memory Relationships** — memories link to people/events/other memories; connections
  resolve to labels and show as chips ("who told me that"). Endpoints: link/unlink + GET detail.
- **Daily Brief** — one quiet, LLM-written morning note on Home that reads her day
  (`/api/home/brief`, cached per day, refreshable).
- **iPad Notes Inbox** — upload notes/PDFs into Knowledge via Emergent Object Storage;
  text is extracted (pypdf) so uploads are searchable. Real storage, open single-user download.
- Tested: frontend 100%; backend 96% (only a by-design LLM-non-determinism assertion).

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
