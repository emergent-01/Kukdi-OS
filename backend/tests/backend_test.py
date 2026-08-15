"""Kukdi backend integration tests.

Covers Home, Conversation, Memory (incl. candidates), Dream Offer, People,
Calendar (incl. LLM ask), Knowledge routes.
"""
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
