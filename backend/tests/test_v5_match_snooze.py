"""V5: Story Matcher + Snooze Reminders."""
import os
from datetime import datetime, timedelta, timezone

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Story Matcher ---------------------------------------------------
class TestStoryMatcher:
    def test_match_leadership_question_returns_isb(self, s):
        q = "Google PM — tell me about a time you led a team without formal authority"
        r = s.post(f"{BASE}/stories/match", json={"question": q}, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "results" in data
        results = data["results"]
        assert isinstance(results, list)
        assert len(results) >= 1, "expected at least one match"

        # each has full story fields + fit + reason
        for item in results:
            for k in ["id", "title", "situation", "task", "action", "result", "fit", "reason"]:
                assert k in item, f"match missing {k}: {list(item.keys())}"
            assert item["fit"] in ("strong", "good", "stretch"), f"bad fit label {item['fit']}"

        # ISB Marketing Club should rank as strong fit at top
        top = results[0]
        assert "ISB Marketing" in top["title"], f"expected ISB Marketing on top, got {top['title']}"
        assert top["fit"] == "strong", f"expected strong fit, got {top['fit']}"
        assert isinstance(top["reason"], str) and len(top["reason"].strip()) > 5

    def test_match_nonsense_returns_few(self, s):
        r = s.post(f"{BASE}/stories/match",
                   json={"question": "asdfjkl qwerty zzz banana platypus xyzzy"}, timeout=60)
        assert r.status_code == 200
        results = r.json()["results"]
        # Allow up to a couple stretch fits, but should be small
        assert len(results) <= 3, f"nonsense query returned {len(results)} results"


# ---------- Snooze Reminders ------------------------------------------------
class TestSnoozeReminder:
    def test_snooze_hides_reminder_today(self, s):
        # create a throwaway person with imminent birthday
        target = datetime.now(timezone.utc).date() + timedelta(days=4)
        bstr = target.strftime("%B %d")
        p = s.post(f"{BASE}/people",
                   json={"name": "TEST_SnoozePerson", "relation": "friend", "birthday": bstr},
                   timeout=15).json()
        pid = p["id"]
        rid = f"birthday:{pid}"
        try:
            # appears now
            rems = s.get(f"{BASE}/reminders", timeout=15).json()["reminders"]
            assert any(r["id"] == rid for r in rems), f"expected {rid} in reminders"

            # snooze it
            resp = s.post(f"{BASE}/reminders/snooze", json={"id": rid}, timeout=15)
            assert resp.status_code == 200
            immediate = resp.json()["reminders"]
            assert not any(r["id"] == rid for r in immediate), "snoozed reminder still in immediate response"

            # subsequent GET also excludes
            after = s.get(f"{BASE}/reminders", timeout=15).json()["reminders"]
            assert not any(r["id"] == rid for r in after), "snoozed reminder reappeared in GET"
        finally:
            s.delete(f"{BASE}/people/{pid}", timeout=15)

    def test_snooze_distinct_from_dismiss(self, s):
        # Two different persons — snooze one, dismiss another; verify both hidden but keys different
        target = datetime.now(timezone.utc).date() + timedelta(days=3)
        bstr = target.strftime("%B %d")
        pa = s.post(f"{BASE}/people",
                    json={"name": "TEST_SnoozeA", "relation": "friend", "birthday": bstr}, timeout=15).json()
        pb = s.post(f"{BASE}/people",
                    json={"name": "TEST_DismissB", "relation": "friend", "birthday": bstr}, timeout=15).json()
        ra, rb = f"birthday:{pa['id']}", f"birthday:{pb['id']}"
        try:
            s.post(f"{BASE}/reminders/snooze", json={"id": ra}, timeout=15).raise_for_status()
            s.post(f"{BASE}/reminders/dismiss", json={"id": rb}, timeout=15).raise_for_status()
            rems = s.get(f"{BASE}/reminders", timeout=15).json()["reminders"]
            ids = [r["id"] for r in rems]
            assert ra not in ids and rb not in ids
        finally:
            s.delete(f"{BASE}/people/{pa['id']}", timeout=15)
            s.delete(f"{BASE}/people/{pb['id']}", timeout=15)
