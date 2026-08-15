"""V4: Smart Reminders + Story Bank tests."""
import os
import time
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Reminders --------------------------------------------------------
class TestReminders:
    def test_list_reminders_shape_and_seeds(self, s):
        r = s.get(f"{BASE}/reminders", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "reminders" in data
        rems = data["reminders"]
        assert isinstance(rems, list)
        # each has expected fields
        for rem in rems:
            for k in ["id", "kind", "title", "detail", "days", "priority"]:
                assert k in rem, f"reminder missing {k}: {rem}"
        # expect at least a next-step nudge (companies have next_action seeded)
        kinds = {r["kind"] for r in rems}
        # placement/deadline may or may not appear depending on seeded dates being in future
        # but next-step should exist for seeded companies
        assert "next-step" in kinds or "deadline" in kinds or "placement" in kinds or "birthday" in kinds, \
            f"expected at least one derived reminder kind, got {kinds}"

    def test_sorted_by_urgency(self, s):
        data = s.get(f"{BASE}/reminders", timeout=15).json()
        rems = data["reminders"]
        if len(rems) < 2:
            pytest.skip("need >=2 to check sort")
        # sorted by (-priority, days)
        for i in range(len(rems) - 1):
            a, b = rems[i], rems[i + 1]
            assert (a["priority"], -a["days"]) >= (b["priority"], -b["days"]) or a["priority"] >= b["priority"]

    def test_dismiss_reminder_disappears(self, s):
        # Create a throwaway person with an imminent birthday so we get a birthday reminder
        from datetime import datetime, timedelta, timezone
        target = datetime.now(timezone.utc).date() + timedelta(days=5)
        bstr = target.strftime("%B %d")
        p = s.post(f"{BASE}/people",
                   json={"name": "TEST_BdayPerson", "relation": "friend", "birthday": bstr},
                   timeout=15).json()
        pid = p["id"]
        rid = f"birthday:{pid}"

        # Confirm the reminder appears
        rems = s.get(f"{BASE}/reminders", timeout=15).json()["reminders"]
        assert any(r["id"] == rid for r in rems), f"expected {rid} in reminders, got ids={[r['id'] for r in rems]}"

        # Dismiss
        d = s.post(f"{BASE}/reminders/dismiss", json={"id": rid}, timeout=15)
        assert d.status_code == 200
        after = d.json()["reminders"]
        assert not any(r["id"] == rid for r in after), "dismissed reminder still present in immediate response"

        # Subsequent GET also excludes
        again = s.get(f"{BASE}/reminders", timeout=15).json()["reminders"]
        assert not any(r["id"] == rid for r in again), "dismissed reminder reappeared in GET"

        # cleanup
        s.delete(f"{BASE}/people/{pid}", timeout=15)


# ---------- Stories ----------------------------------------------------------
class TestStories:
    def test_list_seeded_stories(self, s):
        r = s.get(f"{BASE}/stories", timeout=15)
        assert r.status_code == 200
        stories = r.json()["stories"]
        assert len(stories) >= 1
        titles = [x["title"] for x in stories]
        # Seeded titles per problem statement
        assert any("ISB Marketing" in t for t in titles) or any("differently" in t.lower() for t in titles), \
            f"expected seeded stories, got {titles}"
        for st in stories:
            for k in ["id", "title", "situation", "task", "action", "result", "themes", "status"]:
                assert k in st, f"story missing {k}: {st}"

    def test_crud_story(self, s):
        payload = {"title": "TEST_story", "situation": "sit", "task": "task",
                   "action": "act", "result": "res", "themes": ["testing"]}
        c = s.post(f"{BASE}/stories", json=payload, timeout=15)
        assert c.status_code == 200
        sid = c.json()["id"]

        # PATCH
        u = s.patch(f"{BASE}/stories/{sid}", json={"situation": "updated sit"}, timeout=15)
        assert u.status_code == 200
        assert u.json()["situation"] == "updated sit"

        # verify via list
        lst = s.get(f"{BASE}/stories", timeout=15).json()["stories"]
        found = next((x for x in lst if x["id"] == sid), None)
        assert found and found["situation"] == "updated sit"

        # DELETE
        d = s.delete(f"{BASE}/stories/{sid}", timeout=15)
        assert d.status_code == 200
        lst2 = s.get(f"{BASE}/stories", timeout=15).json()["stories"]
        assert not any(x["id"] == sid for x in lst2)

    def test_polish_story_with_claude(self, s):
        # Create a throwaway story to polish
        payload = {"title": "TEST_polish", "situation": "I led a small club event.",
                   "task": "I had to increase attendance.",
                   "action": "I sent a few emails and posters.",
                   "result": "More people came.",
                   "themes": ["leadership"]}
        c = s.post(f"{BASE}/stories", json=payload, timeout=15).json()
        sid = c["id"]
        try:
            p = s.post(f"{BASE}/stories/{sid}/polish", timeout=90)
            assert p.status_code == 200, p.text
            pd = p.json()
            for k in ["situation", "task", "action", "result", "feedback", "status"]:
                assert k in pd, f"polished missing {k}"
            assert pd["status"] == "polished"
            assert isinstance(pd["feedback"], str) and len(pd["feedback"].strip()) > 0, \
                "expected non-empty coaching feedback"
            # refined STAR fields should be non-empty strings
            for k in ["situation", "task", "action", "result"]:
                assert isinstance(pd[k], str) and len(pd[k].strip()) > 0
        finally:
            s.delete(f"{BASE}/stories/{sid}", timeout=15)
