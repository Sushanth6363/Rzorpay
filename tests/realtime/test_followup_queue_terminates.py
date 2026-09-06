"""A due follow-up must be retired after it runs, or the worker never stops.

WHY THIS EXISTS
    `due_followups` selected rows and NOTHING ever changed their status. The only
    transitions were `_stop` for the recovery window and `cancel_for_entity` for a
    payment. So a row that came due stayed SCHEDULED and was re-run on every worker tick,
    forever.

    That single omission produced most of the strange behaviour seen during demo prep:

        - one log line repeating hundreds of times for the same opportunity
        - nineteen "overdue" rows accumulating from a single uploaded case
        - Razorpay returning 429 Too Many Requests, because the worker asked it for a new
          payment link every two seconds, indefinitely

    The last one is why waiting never helped. The throttle could not clear while the loop
    was still running, and stopping the server was the only thing that ever fixed it.

WHAT MUST NOT CHANGE
    Retiring the row does not break the chain. A follow-up schedules its successor under a
    NEW opportunity id (`<origin>#f2`), which is a separate row with its own due time.
"""

import sqlite3

import pytest

from app.domain.enums import ActionType


@pytest.fixture()
def queue(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOVERY_DB_PATH", str(tmp_path / "q.db"))
    import importlib
    from app.realtime import config as cfg
    importlib.reload(cfg)
    from app.realtime import ingest as ing
    importlib.reload(ing)
    from app.realtime import followup as f
    importlib.reload(f)
    f.ensure_schema()
    return f, str(tmp_path / "q.db")


def _schedule_due(f, path, opportunity_id="opp_1"):
    f.schedule(opportunity_id=opportunity_id, merchant_id="m1", customer_id="c1",
               origin_event_id="e1", event={}, diagnosis_code="INVOICE_OVERDUE",
               last_action=ActionType.EMAIL_LINK, attempt=0)
    c = sqlite3.connect(path)
    c.execute("UPDATE followup_queue SET next_touch_at='2020-01-01T00:00:00+00:00' "
              "WHERE opportunity_id=?;", (opportunity_id,))
    c.commit()
    c.close()


def test_a_handled_follow_up_does_not_come_due_again(queue):
    """The defect. Before this, every tick returned the same row for ever."""
    f, path = queue
    _schedule_due(f, path)

    first = f.due_followups()
    for item in first:
        f.mark_handled(item["opportunity_id"])
    second = f.due_followups()

    assert len(first) == 1
    assert second == [], "the same follow-up came due twice"


def test_ten_worker_ticks_process_it_exactly_once(queue):
    """Stated the way the outage actually happened: the worker runs every two seconds."""
    f, path = queue
    _schedule_due(f, path)

    processed = 0
    for _ in range(10):
        for item in f.due_followups():
            processed += 1
            f.mark_handled(item["opportunity_id"])

    assert processed == 1, f"one follow-up ran {processed} times across ten ticks"


def test_the_row_is_kept_as_a_record_rather_than_deleted(queue):
    f, path = queue
    _schedule_due(f, path)
    f.mark_handled("opp_1", "handled")

    row = sqlite3.connect(path).execute(
        "SELECT status, stop_reason FROM followup_queue WHERE opportunity_id='opp_1';"
    ).fetchone()

    assert row == ("HANDLED", "handled")


def test_a_failure_is_retired_too(queue):
    """Retrying the same row every two seconds is not resilience, it is the loop that
    caused the outage. The genuine retry is the next scheduled follow-up."""
    f, path = queue
    _schedule_due(f, path)

    f.mark_handled("opp_1", "failed: boom")

    assert f.due_followups() == []
    reason = sqlite3.connect(path).execute(
        "SELECT stop_reason FROM followup_queue WHERE opportunity_id='opp_1';").fetchone()[0]
    assert "boom" in reason


def test_the_chain_continues_under_the_successor_id(queue):
    """Retiring this row must not stop the sequence: `#f2` is its own row."""
    f, path = queue
    _schedule_due(f, path, "opp_1")
    f.mark_handled("opp_1")

    _schedule_due(f, path, "opp_1#f2")

    assert [d["opportunity_id"] for d in f.due_followups()] == ["opp_1#f2"]


def test_marking_an_unknown_row_is_a_no_op(queue):
    f, path = queue

    f.mark_handled("never_existed")   # must not raise


def test_it_does_not_disturb_a_row_that_is_not_due(queue):
    f, path = queue
    f.schedule(opportunity_id="future", merchant_id="m1", customer_id="c1",
               origin_event_id="e1", event={}, diagnosis_code="INVOICE_OVERDUE",
               last_action=ActionType.EMAIL_LINK, attempt=0)

    f.mark_handled("opp_1")

    status = sqlite3.connect(path).execute(
        "SELECT status FROM followup_queue WHERE opportunity_id='future';").fetchone()[0]
    assert status == "SCHEDULED"
