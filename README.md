# Kukdi — A Personal Operating System

An intelligent, single-user "personal OS" that reduces cognitive load: it quietly
understands context, remembers what matters, and surfaces the right thing at the
right moment. Built for one user ("Little Miss", an ISB Mohali MBA aiming for
Product Management). Calm, editorial UI; the intelligence is the product.

## Stack
- **Backend:** FastAPI + MongoDB (Motor). Reasoning via Claude Sonnet 4.6, voice via
  OpenAI Whisper, uploads via Emergent Object Storage — all through the Emergent LLM key.
- **Frontend:** React (CRA) + Tailwind + shadcn/ui + framer-motion. Fonts: Cormorant
  Garamond (editorial) + Manrope.

## Architecture
- `ai_engine.py` is the ONLY module that knows an LLM exists (swappable engine).
  Routes build *context* (`context.py`) and ask the engine to *reason*.
- **Memory** is the substrate; conversation produces *candidate* memories that need
  confirmation. **Home** is computed (adaptive state), never a stored dashboard.
- String-UUID ids everywhere; Mongo `_id` is always projected out.

## Modules / API (all under `/api`)
`home` (adaptive state + daily brief), `conversation` (streaming chat + Whisper
transcribe + candidate extraction), `memory` (CRUD + candidates + relationships),
`dream` (company pipeline, prep roadmap, interview countdown), `people`, `calendar`
(+ natural-language ask), `knowledge` (uploads + semantic search), `reflection`
(weekly recap), `reminders` (smart nudges + snooze/dismiss), `stories` (STAR bank +
polish + matcher).

## Run locally
### Backend
```bash
cd backend
cp .env.example .env          # fill EMERGENT_LLM_KEY, set MONGO_URL/DB_NAME
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```
Backend seeds itself with rich demo data on first startup (or POST /api/seed to reset).

### Frontend
```bash
cd frontend
cp .env.example .env          # set REACT_APP_BACKEND_URL (e.g. http://localhost:8001)
yarn install
yarn start                    # http://localhost:3000
```

## Notes
- No authentication — intentionally single-user for Version One.
- All backend routes are prefixed with `/api`; the frontend only calls
  `REACT_APP_BACKEND_URL`. Never hardcode URLs or secrets.
