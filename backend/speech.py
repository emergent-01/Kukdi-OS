"""Speech-to-text for Voice Capture — OpenAI Whisper (whisper-1) via the Emergent
LLM key. Kept separate from the text reasoning engine (different provider/verb).
"""
import os
import tempfile

from emergentintegrations.llm.openai import OpenAISpeechToText

_stt = OpenAISpeechToText(api_key=os.environ.get("EMERGENT_LLM_KEY", ""))


async def transcribe_audio(data: bytes, ext: str = "webm") -> str:
    ext = (ext or "webm").lower()
    if ext not in ("mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"):
        ext = "webm"
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        tmp.seek(0)
        with open(tmp.name, "rb") as audio_file:
            resp = await _stt.transcribe(file=audio_file, model="whisper-1", response_format="json")
    return (getattr(resp, "text", "") or "").strip()
