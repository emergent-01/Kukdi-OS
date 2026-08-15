"""Kukdi backend integration tests.

Covers Home, Conversation, Memory (incl. candidates), Dream Offer, People,
Calendar (incl. LLM ask), Knowledge routes.
"""
import json
import os
import time

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"


@pytest.fixture(scope="session")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Home --------------------------------------------------------------
class TestHome:
    def test_home_shape(self, s):
        r = s.get(f"{BASE}/home", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ["state", "greeting", "heading", "subtext", "today",
                  "upcoming", "focus", "surfaced_memories", "pending_candidates"]:
            assert k in d, f"missing {k}"
        assert isinstance(d["today"], list)
        assert isinstance(d["upcoming"], list)

    def test_home_state_override(self, s):
        r = s.post(f"{BASE}/home/state", json={"state": "exam"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["override"] == "exam"

        r2 = s.get(f"{BASE}/home", timeout=15)
        d = r2.json()
        assert d["state"] == "exam"
        assert "Exam" in d["heading"] or "exam" in d["heading"].lower()

        # clear
        c = s.post(f"{BASE}/home/state", json={"state": None}, timeout=15)
        assert c.status_code == 200


# ---------- Memory ------------------------------------------------------------
class TestMemory:
    def test_list_memories_seeded(self, s):
        r = s.get(f"{BASE}/memory", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "memories" in d and "types" in d
        assert len(d["memories"]) > 0, "expected seeded memories"
        assert len(d["types"]) > 0

    def test_create_update_confirm_delete_memory(self, s):
        # CREATE
        payload = {"type": "Insight", "title": "TEST_mem_flow",
                   "description": "test memory", "tags": ["testing"]}
        r = s.post(f"{BASE}/memory", json=payload, timeout=15)
        assert r.status_code == 200
        mem = r.json()
        assert mem["title"] == "TEST_mem_flow"
        mid = mem["id"]

        # GET verify persisted
        lst = s.get(f"{BASE}/memory", timeout=15).json()["memories"]
        assert any(m["id"] == mid for m in lst)

        # PATCH
        u = s.patch(f"{BASE}/memory/{mid}", json={"title": "TEST_mem_updated"}, timeout=15)
        assert u.status_code == 200
        assert u.json()["title"] == "TEST_mem_updated"

        # confirm
        c = s.post(f"{BASE}/memory/{mid}/confirm", timeout=15)
        assert c.status_code == 200
        assert c.json()["last_confirmed"]

        # DELETE (archive)
        d = s.delete(f"{BASE}/memory/{mid}", timeout=15)
        assert d.status_code == 200
        lst2 = s.get(f"{BASE}/memory", timeout=15).json()["memories"]
        assert not any(m["id"] == mid for m in lst2), "archived memory should not appear"

    def test_candidates_pending_endpoint(self, s):
        r = s.get(f"{BASE}/memory/candidates/pending", timeout=15)
        assert r.status_code == 200
        assert "candidates" in r.json()


# ---------- Conversation (LLM) -----------------------------------------------
class TestConversation:
    def test_conversation_flow_and_candidate(self, s):
        text = ("Please remember this about me: running before exams calms me "
                "down and helps me focus. It's an important routine for me.")
        r = s.post(f"{BASE}/conversation/message",
                   json={"text": text}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "conversation_id" in d and d["conversation_id"]
        assert "reply" in d and d["reply"]["role"] == "kukdi"
        assert isinstance(d["reply"]["text"], str) and len(d["reply"]["text"]) > 0
        assert "candidates" in d and isinstance(d["candidates"], list)
        # meaningful message should yield at least one candidate
        assert len(d["candidates"]) >= 1, f"expected candidates for memorable statement, got {d}"

        # messages endpoint
        m = s.get(f"{BASE}/conversation/messages",
                  params={"conversation_id": d["conversation_id"]}, timeout=15)
        assert m.status_code == 200
        msgs = m.json()["messages"]
        roles = [x["role"] for x in msgs]
        assert "user" in roles and "kukdi" in roles

        # store one candidate for confirmation test
        pytest.candidate_id = d["candidates"][0]["id"]

    def test_confirm_candidate_becomes_memory(self, s):
        cid = getattr(pytest, "candidate_id", None)
        if not cid:
            pytest.skip("no candidate captured earlier")
        r = s.post(f"{BASE}/memory/candidates/{cid}/confirm", json={}, timeout=15)
        assert r.status_code == 200
        mem = r.json()
        assert mem["status"] == "active" and mem["id"]
        # verify in list
        lst = s.get(f"{BASE}/memory", timeout=15).json()["memories"]
        assert any(m["id"] == mem["id"] for m in lst)

    def test_dismiss_candidate(self, s):
        # create a throwaway candidate via message; if none produced, skip
        r = s.post(f"{BASE}/conversation/message",
                   json={"text": "I love spicy chai in the mornings, please remember."},
                   timeout=90)
        d = r.json()
        if not d.get("candidates"):
            pytest.skip("no candidate produced to dismiss")
        cid = d["candidates"][0]["id"]
        r2 = s.post(f"{BASE}/memory/candidates/{cid}/dismiss", timeout=15)
        assert r2.status_code == 200 and r2.json()["ok"] is True


# ---------- Dream Offer ------------------------------------------------------
class TestDreamOffer:
    def test_overview_seeded(self, s):
        r = s.get(f"{BASE}/dream/overview", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ["companies", "prep_by_category", "progress", "stage_counts"]:
            assert k in d
        names = [c["name"] for c in d["companies"]]
        for expected in ["Google", "Microsoft", "Adobe", "MakeMyTrip"]:
            assert expected in names, f"expected seed company {expected}"
        assert isinstance(d["progress"], (int, float))

    def test_company_crud_and_stage_cycle(self, s):
        # create
        r = s.post(f"{BASE}/dream/companies",
                   json={"name": "TEST_Co", "tier": "dream", "role": "PM"}, timeout=15)
        assert r.status_code == 200
        cid = r.json()["id"]

        # patch stage cycle
        u = s.patch(f"{BASE}/dream/companies/{cid}", json={"stage": "applied"}, timeout=15)
        assert u.status_code == 200 and u.json()["stage"] == "applied"

        # verify persisted
        ov = s.get(f"{BASE}/dream/overview", timeout=15).json()
        found = [c for c in ov["companies"] if c["id"] == cid]
        assert found and found[0]["stage"] == "applied"

        # delete
        d = s.delete(f"{BASE}/dream/companies/{cid}", timeout=15)
        assert d.status_code == 200

    def test_prep_crud(self, s):
        r = s.post(f"{BASE}/dream/prep",
                   json={"category": "framework", "title": "TEST_prep"}, timeout=15)
        assert r.status_code == 200
        pid = r.json()["id"]
        u = s.patch(f"{BASE}/dream/prep/{pid}", json={"status": "done"}, timeout=15)
        assert u.status_code == 200 and u.json()["status"] == "done"
        d = s.delete(f"{BASE}/dream/prep/{pid}", timeout=15)
        assert d.status_code == 200


# ---------- People -----------------------------------------------------------
class TestPeople:
    def test_seeded_people(self, s):
        r = s.get(f"{BASE}/people", timeout=15)
        assert r.status_code == 200
        names = [p["name"] for p in r.json()["people"]]
        for expected in ["Ananya", "Rohan Mehta", "Prof. Nair", "Mom"]:
            assert expected in names, f"missing seed person {expected}"

    def test_person_crud(self, s):
        r = s.post(f"{BASE}/people",
                   json={"name": "TEST_Person", "relation": "friend"}, timeout=15)
        pid = r.json()["id"]
        u = s.patch(f"{BASE}/people/{pid}", json={"notes": "hello"}, timeout=15)
        assert u.status_code == 200 and u.json()["notes"] == "hello"
        assert s.delete(f"{BASE}/people/{pid}", timeout=15).status_code == 200


# ---------- Calendar ---------------------------------------------------------
class TestCalendar:
    def test_events_split(self, s):
        r = s.get(f"{BASE}/calendar", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ["events", "upcoming", "past"]:
            assert k in d

    def test_event_crud(self, s):
        payload = {"type": "task", "title": "TEST_evt", "start": "2030-01-01T09:00:00+00:00"}
        r = s.post(f"{BASE}/calendar", json=payload, timeout=15)
        eid = r.json()["id"]
        assert s.delete(f"{BASE}/calendar/{eid}", timeout=15).status_code == 200

    def test_ask_natural_language(self, s):
        r = s.post(f"{BASE}/calendar/ask",
                   json={"question": "what do I have tomorrow?"}, timeout=90)
        assert r.status_code == 200
        ans = r.json().get("answer")
        assert isinstance(ans, str) and len(ans) > 0


# ---------- Knowledge --------------------------------------------------------
class TestKnowledge:
    def test_list_and_search(self, s):
        r = s.get(f"{BASE}/knowledge", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json()["items"], list)

    def test_create_search_delete(self, s):
        r = s.post(f"{BASE}/knowledge",
                   json={"kind": "note", "title": "TEST_knowledge_pmframework",
                         "summary": "unique_marker_xyz"}, timeout=15)
        kid = r.json()["id"]
        f = s.get(f"{BASE}/knowledge", params={"q": "unique_marker_xyz"}, timeout=15)
        assert any(i["id"] == kid for i in f.json()["items"])
        assert s.delete(f"{BASE}/knowledge/{kid}", timeout=15).status_code == 200


# ---------- V2: Streaming ---------------------------------------------------
class TestStreaming:
    def test_stream_sse_events(self, s):
        text = ("Please remember I like to rehearse my answers out loud "
                "before interviews — that's a real habit.")
        r = requests.post(f"{BASE}/conversation/stream",
                          json={"text": text}, stream=True, timeout=120)
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")

        events = []
        tokens = []
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            payload = json.loads(line[len("data: "):])
            events.append(payload["type"])
            if payload["type"] == "token":
                tokens.append(payload["content"])
            elif payload["type"] == "candidates":
                pytest.stream_candidates = payload["candidates"]
            elif payload["type"] == "done":
                break

        assert events[0] == "meta"
        assert "token" in events
        assert "candidates" in events
        assert "done" in events
        full = "".join(tokens)
        assert len(full.strip()) > 20, f"stream reply too short: {full!r}"

    def test_stream_yields_candidate(self, s):
        cands = getattr(pytest, "stream_candidates", None)
        if cands is None:
            pytest.skip("stream test did not run")
        assert isinstance(cands, list)
        assert len(cands) >= 1, f"expected candidate from memorable message, got {cands}"


# ---------- V2: Daily Brief -------------------------------------------------
class TestDailyBrief:
    def test_brief_get_cache_and_refresh(self, s):
        r1 = s.get(f"{BASE}/home/brief", timeout=60)
        assert r1.status_code == 200
        d1 = r1.json()
        assert isinstance(d1.get("brief"), str) and len(d1["brief"]) > 0

        r2 = s.get(f"{BASE}/home/brief", timeout=15)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["cached"] is True
        assert d2["brief"] == d1["brief"]

        r3 = s.post(f"{BASE}/home/brief/refresh", timeout=60)
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3["cached"] is False
        assert isinstance(d3["brief"], str) and len(d3["brief"]) > 0


# ---------- V2: Memory Relationships ----------------------------------------
class TestMemoryLinks:
    def test_link_unlink_person(self, s):
        # Get a real person
        people = s.get(f"{BASE}/people", timeout=15).json()["people"]
        assert people
        person = people[0]

        # Create a memory
        m = s.post(f"{BASE}/memory",
                   json={"type": "Insight", "title": "TEST_link_mem",
                         "description": "linked memory"}, timeout=15).json()
        mid = m["id"]

        # LINK
        r = s.post(f"{BASE}/memory/{mid}/link",
                   json={"kind": "person", "ref_id": person["id"]}, timeout=15)
        assert r.status_code == 200, r.text
        conns = r.json()["connections"]
        assert any(c["ref_id"] == person["id"] and c["label"] == person["name"]
                   for c in conns), f"expected resolved label, got {conns}"

        # GET memory shows connections
        g = s.get(f"{BASE}/memory/{mid}", timeout=15)
        assert g.status_code == 200
        gd = g.json()
        assert "connections" in gd
        assert any(c["ref_id"] == person["id"] for c in gd["connections"])

        # UNLINK
        u = s.post(f"{BASE}/memory/{mid}/unlink",
                   json={"kind": "person", "ref_id": person["id"]}, timeout=15)
        assert u.status_code == 200
        assert not any(c["ref_id"] == person["id"] for c in u.json()["connections"])

        # cleanup
        s.delete(f"{BASE}/memory/{mid}", timeout=15)


# ---------- V2: Notes Inbox (Upload) ----------------------------------------
class TestNotesInbox:
    def test_upload_txt_and_download(self, s):
        content = "TEST_upload_marker_abc123 — this note came from the iPad.".encode("utf-8")
        files = {"file": ("test_upload.txt", content, "text/plain")}
        # Use fresh session without json content-type header
        r = requests.post(f"{BASE}/knowledge/upload", files=files, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["file_url"].startswith("/api/knowledge/files/")
        assert d["original_filename"] == "test_upload.txt"
        assert "TEST_upload_marker_abc123" in (d.get("body") or "")
        kid = d["id"]

        # appears in list
        lst = s.get(f"{BASE}/knowledge", timeout=15).json()["items"]
        assert any(i["id"] == kid for i in lst)

        # searchable via extracted text
        f = s.get(f"{BASE}/knowledge", params={"q": "TEST_upload_marker_abc123"}, timeout=15)
        assert any(i["id"] == kid for i in f.json()["items"])

        # download
        path = d["file_url"].replace("/api/knowledge/files/", "")
        dl = requests.get(f"{BASE}/knowledge/files/{path}", timeout=30)
        assert dl.status_code == 200
        assert dl.content == content
        assert "text/plain" in dl.headers.get("content-type", "")

        # cleanup
        s.delete(f"{BASE}/knowledge/{kid}", timeout=15)

    def test_upload_pdf_extracts_text(self, s):
        # Build a minimal PDF using reportlab if available, else pypdf
        try:
            from reportlab.pdfgen import canvas
            import io
            buf = io.BytesIO()
            c = canvas.Canvas(buf)
            c.drawString(100, 750, "TEST_pdf_marker_xyz789 hello Kukdi")
            c.save()
            pdf_bytes = buf.getvalue()
        except Exception:
            pytest.skip("reportlab not available to build test pdf")

        files = {"file": ("t.pdf", pdf_bytes, "application/pdf")}
        r = requests.post(f"{BASE}/knowledge/upload", files=files, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["kind"] == "document"
        assert "TEST_pdf_marker_xyz789" in (d.get("body") or ""), \
            f"pdf text not extracted, body={d.get('body')!r}"
        s.delete(f"{BASE}/knowledge/{d['id']}", timeout=15)


# ---------- V3: Semantic Search ---------------------------------------------
class TestSemanticSearch:
    def test_semantic_search_ranks_by_meaning(self, s):
        # A design-interview query should surface CIRCLES / product design frameworks
        # even without keyword overlap
        r = s.post(f"{BASE}/knowledge/search",
                   json={"question": "how do I structure a product design interview answer"},
                   timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "results" in d and isinstance(d["results"], list)
        assert len(d["results"]) >= 1, f"expected at least one semantic result, got {d}"
        first = d["results"][0]
        assert "id" in first and "title" in first
        assert "reason" in first and isinstance(first["reason"], str)
        # ideally the top hit should relate to product design / CIRCLES framework
        titles = " ".join((it.get("title", "") + " " + (it.get("summary", "") or ""))
                          for it in d["results"]).lower()
        # not strict but at least should not be all irrelevant
        assert any(k in titles for k in ["circles", "product", "design", "interview", "framework", "case"]), \
            f"top semantic results seem irrelevant: titles={[it.get('title') for it in d['results']]}"

    def test_semantic_search_nonsense_returns_few(self, s):
        r = s.post(f"{BASE}/knowledge/search",
                   json={"question": "asdfqwer zxcvbn plumbus flurbo xylophone"},
                   timeout=90)
        assert r.status_code == 200
        d = r.json()
        # a nonsense query should return few or zero results
        assert len(d["results"]) <= 5, f"expected few/no results for nonsense, got {len(d['results'])}"


# ---------- V3: Voice Capture (Whisper) --------------------------------------
class TestTranscribe:
    def test_transcribe_missing_file_422(self):
        r = requests.post(f"{BASE}/conversation/transcribe", timeout=15)
        assert r.status_code == 422

    def test_transcribe_real_audio(self):
        # generate a real spoken clip via gTTS
        try:
            from gtts import gTTS
            import io
            tts = gTTS("Hello Kukdi, please remember I love running before exams.")
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            audio_bytes = buf.getvalue()
        except Exception as e:
            pytest.skip(f"gTTS not available: {e}")

        files = {"file": ("test.mp3", audio_bytes, "audio/mpeg")}
        r = requests.post(f"{BASE}/conversation/transcribe", files=files, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "text" in d
        assert isinstance(d["text"], str)
        assert len(d["text"].strip()) > 0, f"expected non-empty transcription, got {d}"


# ---------- V3: Weekly Reflection -------------------------------------------
class TestWeeklyReflection:
    def test_weekly_reflection_cache_and_refresh(self, s):
        # first call (may be cached from earlier manual testing; either way returns valid shape)
        r1 = s.get(f"{BASE}/reflection/weekly", timeout=90)
        assert r1.status_code == 200
        d1 = r1.json()
        assert "reflection" in d1 and isinstance(d1["reflection"], str)
        assert len(d1["reflection"].strip()) > 0
        assert "stats" in d1 and isinstance(d1["stats"], dict)
        for k in ["attended_this_week", "coming_up", "prep_done"]:
            assert k in d1["stats"], f"stats missing {k}: {d1['stats']}"

        # second call same week -> cached=True
        r2 = s.get(f"{BASE}/reflection/weekly", timeout=30)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["cached"] is True
        assert d2["reflection"] == d1["reflection"]

        # refresh=true -> new reflection, cached=False
        r3 = s.get(f"{BASE}/reflection/weekly", params={"refresh": "true"}, timeout=90)
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3["cached"] is False
        assert isinstance(d3["reflection"], str) and len(d3["reflection"].strip()) > 0


# ---------- V3: Interview Countdown -----------------------------------------
class TestInterviewCountdown:
    def test_generate_get_toggle_task(self, s):
        # generate (targets next seeded placement/interview e.g. Google APM)
        r = s.post(f"{BASE}/dream/countdown/generate", json={}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "countdown" in d and d["countdown"]
        cd = d["countdown"]
        for k in ["company", "role", "target_date", "days_remaining",
                  "days", "progress", "tasks_done", "tasks_total"]:
            assert k in cd, f"countdown missing {k}"
        assert isinstance(cd["days"], list) and len(cd["days"]) >= 1
        first_day = cd["days"][0]
        assert "focus" in first_day and "tasks" in first_day
        assert len(first_day["tasks"]) >= 1
        task = first_day["tasks"][0]
        assert "id" in task and "text" in task and "done" in task
        assert task["done"] is False

        # GET returns same countdown
        g = s.get(f"{BASE}/dream/countdown", timeout=15)
        assert g.status_code == 200
        gd = g.json()["countdown"]
        assert gd["target_date"] == cd["target_date"]
        assert gd["tasks_total"] == cd["tasks_total"]

        # toggle first task done -> progress moves
        tid = task["id"]
        p = s.patch(f"{BASE}/dream/countdown/task/{tid}",
                    json={"done": True}, timeout=15)
        assert p.status_code == 200
        pd = p.json()["countdown"]
        assert pd["tasks_done"] >= 1
        assert pd["progress"] > 0

        # verify persisted
        g2 = s.get(f"{BASE}/dream/countdown", timeout=15).json()["countdown"]
        found = False
        for day in g2["days"]:
            for t in day["tasks"]:
                if t["id"] == tid:
                    assert t["done"] is True
                    found = True
        assert found, "toggled task not found in persisted plan"

    def test_generate_with_company_id(self, s):
        ov = s.get(f"{BASE}/dream/overview", timeout=15).json()
        adobe = next((c for c in ov["companies"] if c["name"] == "Adobe"), None)
        if not adobe:
            pytest.skip("Adobe seed missing")
        r = s.post(f"{BASE}/dream/countdown/generate",
                   json={"company_id": adobe["id"]}, timeout=120)
        assert r.status_code == 200
        cd = r.json()["countdown"]
        assert cd["company"] == "Adobe", f"expected Adobe, got {cd['company']}"
