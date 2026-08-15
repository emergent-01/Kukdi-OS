"""Kukdi's reasoning engine.

This is the ONLY module that knows an LLM exists. The rest of the product talks
to `reasoning` through two verbs:

    await reasoning.converse(history, user_text, context)  -> {reply, candidates, detected_state}
    await reasoning.answer(question, context)              -> str

`context` is a plain dict assembled by the routes (profile, active memories,
today's events). The engine never touches the database. To replace Claude with
another model — or a local one — reimplement this class; nothing else changes.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List

from emergentintegrations.llm.chat import (LlmChat, StreamDone, TextDelta,
                                           UserMessage)

from models import HOME_STATES, MEMORY_TYPES, new_id

_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
_PROVIDER = "anthropic"
_MODEL = "claude-sonnet-4-6"

_PERSONA = (
    "You are Kukdi, a calm, warm, emotionally intelligent Personal Operating "
    "System built for ONE person, whose nickname is Little Miss. She is an MBA "
    "(PGP) student at ISB Mohali aiming for a Product Management role at her "
    "dream companies (Google, Microsoft, Adobe, MakeMyTrip). She is organised "
    "and emotionally driven, a morning person who sleeps late, sometimes "
    "procrastinates, loves planning, gets anxious under stress, is consistent "
    "once committed, and finds that running clears her head.\n\n"
    "Your purpose is to REDUCE her cognitive load. You are not a chatbot and not "
    "a productivity app. You quietly understand context and remember what "
    "matters. Speak like a thoughtful, grounded friend: brief, warm, human. Two "
    "or three sentences is usually enough. Never use emoji, never use bullet "
    "lists, never sound like an assistant reading a manual. If she seems tired, "
    "anxious or overwhelmed, acknowledge the feeling before anything practical."
)

_OUTPUT_CONTRACT = (
    "Return ONLY a single JSON object, no markdown, with this exact shape:\n"
    '{\n'
    '  "reply": "your warm, natural reply to her",\n'
    '  "candidates": [\n'
    '    {"type": "<one of the memory types>", "title": "short title",\n'
    '     "description": "one clear sentence in third person about Little Miss",\n'
    '     "confidence": 0.0-1.0, "tags": ["..."], "usable_for": ["..."]}\n'
    '  ],\n'
    '  "detected_state": "<one home state or null>"\n'
    "}\n\n"
    f"Memory types: {', '.join(MEMORY_TYPES)}.\n"
    f"Home states: {', '.join(HOME_STATES)}, or null.\n\n"
    "RULES for candidates: only propose a memory for information that is worth "
    "remembering for the long term — goals, stable preferences, people, "
    "routines, habits, decisions, academic/career facts, or meaningful upcoming "
    "events. Do NOT create candidates for small talk, feelings that will pass, "
    "or things you already clearly know from the context. If nothing is worth "
    "remembering, return an empty candidates list. Prefer fewer, higher-quality "
    "memories."
)


def _context_block(context: Dict) -> str:
    lines = ["--- What you currently know (context) ---"]
    prof = context.get("profile")
    if prof:
        lines.append(f"Profile: {prof}")
    mems = context.get("memories") or []
    if mems:
        lines.append("Active memories:")
        for m in mems[:40]:
            lines.append(f"  - [{m.get('type')}] {m.get('title')}: {m.get('description')}")
    events = context.get("events") or []
    if events:
        lines.append("Upcoming on the calendar:")
        for e in events[:20]:
            lines.append(f"  - {e.get('start')} · {e.get('type')} · {e.get('title')}")
    lines.append("--- end context ---")
    return "\n".join(lines)


def _parse_json(text: str) -> Dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1:
        t = t[start : end + 1]
    return json.loads(t)


class KukdiReasoning:
    provider = _PROVIDER
    model = _MODEL

    def _chat(self, system: str, session: str) -> LlmChat:
        return LlmChat(
            api_key=_KEY, session_id=session, system_message=system
        ).with_model(_PROVIDER, _MODEL)

    async def converse(
        self, history: List[Dict], user_text: str, context: Dict
    ) -> Dict:
        system = f"{_PERSONA}\n\n{_context_block(context)}\n\n{_OUTPUT_CONTRACT}"
        chat = self._chat(system, f"kukdi-{new_id()}")

        convo = ""
        for m in history[-8:]:
            who = "Little Miss" if m.get("role") == "user" else "Kukdi"
            convo += f"{who}: {m.get('text')}\n"
        prompt = (f"Recent conversation:\n{convo}\n" if convo else "") + (
            f"Little Miss just said: \"{user_text}\"\n\n"
            "Reply to her, then extract any candidate memories per the contract."
        )

        raw = await chat.send_message(UserMessage(text=prompt))
        try:
            data = _parse_json(raw)
        except Exception:
            return {"reply": raw.strip(), "candidates": [], "detected_state": None}

        cands = []
        for c in data.get("candidates", []) or []:
            if not c.get("title"):
                continue
            cands.append(
                {
                    "type": c.get("type", "Insight"),
                    "title": c["title"],
                    "description": c.get("description", ""),
                    "confidence": float(c.get("confidence", 0.7)),
                    "tags": c.get("tags", []) or [],
                    "usable_for": c.get("usable_for", []) or [],
                }
            )
        state = data.get("detected_state")
        if state not in HOME_STATES:
            state = None
        return {
            "reply": (data.get("reply") or "").strip() or "I'm here.",
            "candidates": cands,
            "detected_state": state,
        }

    async def stream_reply(self, history: List[Dict], user_text: str, context: Dict):
        """Stream Kukdi's natural reply token by token (no candidate extraction —
        that happens in a second pass so streaming stays clean)."""
        system = (
            f"{_PERSONA}\n\n{_context_block(context)}\n\n"
            "Reply to her in plain text — warm, brief, human. No JSON, no lists, "
            "no markdown."
        )
        chat = self._chat(system, f"kukdi-stream-{new_id()}")
        convo = ""
        for m in history[-8:]:
            who = "Little Miss" if m.get("role") == "user" else "Kukdi"
            convo += f"{who}: {m.get('text')}\n"
        prompt = (f"Recent conversation:\n{convo}\n" if convo else "") + (
            f'Little Miss just said: "{user_text}"\nReply to her.'
        )
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                yield ev.content
            elif isinstance(ev, StreamDone):
                break

    async def extract_candidates(self, user_text: str, reply: str, context: Dict) -> List[Dict]:
        system = (
            f"{_PERSONA}\n\n{_context_block(context)}\n\n"
            "Extract candidate long-term memories from the exchange below. "
            + _OUTPUT_CONTRACT
            + '\nSet "reply" to an empty string; only "candidates" matters here.'
        )
        chat = self._chat(system, f"kukdi-extract-{new_id()}")
        prompt = (
            f'Little Miss said: "{user_text}"\nKukdi replied: "{reply}"\n\n'
            "Return the JSON now."
        )
        try:
            raw = await chat.send_message(UserMessage(text=prompt))
            data = _parse_json(raw)
        except Exception:
            return []
        cands = []
        for c in data.get("candidates", []) or []:
            if not c.get("title"):
                continue
            cands.append({
                "type": c.get("type", "Insight"),
                "title": c["title"],
                "description": c.get("description", ""),
                "confidence": float(c.get("confidence", 0.7)),
                "tags": c.get("tags", []) or [],
                "usable_for": c.get("usable_for", []) or [],
            })
        return cands

    async def daily_brief(self, context: Dict, state: str, greeting: str) -> str:
        system = (
            f"{_PERSONA}\n\n{_context_block(context)}\n\n"
            f"Today's felt state is '{state}'. Write ONE quiet morning brief for "
            "Little Miss — two or three warm sentences that read her day and name "
            "only the one or two things that truly matter. If she seems stretched, "
            "lighten it. Plain text, no lists, no greeting header."
        )
        chat = self._chat(system, f"kukdi-brief-{new_id()}")
        raw = await chat.send_message(UserMessage(text="Write today's brief."))
        return raw.strip()

    async def answer(self, question: str, context: Dict) -> str:
        system = (
            f"{_PERSONA}\n\n{_context_block(context)}\n\n"
            "Answer her question directly and briefly using only what you know "
            "above. If the answer isn't in your context, say so gently. Plain "
            "text only — no JSON, no lists."
        )
        chat = self._chat(system, f"kukdi-ask-{new_id()}")
        raw = await chat.send_message(UserMessage(text=question))
        return raw.strip()


reasoning = KukdiReasoning()
