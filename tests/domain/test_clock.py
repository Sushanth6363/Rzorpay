"""Unit tests for Clock abstraction."""

from datetime import datetime, timezone
from app.clock import SystemClock, FakeClock


def test_system_clock() -> None:
    clock = SystemClock()
    now = clock.now_utc()
    assert now.tzinfo == timezone.utc
    assert isinstance(clock.now_iso(), str)


def test_fake_clock_control() -> None:
    start_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(start_time)

    assert clock.now_utc() == start_time
    assert clock.now_iso() == "2026-09-01T10:00:00+00:00"

    clock.advance(minutes=30)
    assert clock.now_iso() == "2026-09-01T10:30:00+00:00"

    clock.advance(hours=2)
    assert clock.now_iso() == "2026-09-01T12:30:00+00:00"

    new_time = datetime(2026, 9, 5, 8, 0, 0, tzinfo=timezone.utc)
    clock.set_time(new_time)
    assert clock.now_utc() == new_time
