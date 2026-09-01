"""Controllable clock abstraction for Unified Recovery Engine.

INVARIANT: No wall-clock datetime.now() calls outside this adapter.
Tests inject FakeClock for 100% deterministic time manipulation.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional, Union


class Clock(ABC):
    """Abstract clock interface."""

    @abstractmethod
    def now_utc(self) -> datetime:
        """Return current datetime in UTC timezone."""
        pass

    def now_iso(self) -> str:
        """Return current datetime as ISO 8601 string."""
        return self.now_utc().isoformat()


class SystemClock(Clock):
    """Real system clock providing current UTC time."""

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


class FakeClock(Clock):
    """Controllable fake clock for deterministic testing."""

    def __init__(self, initial_time: Optional[Union[datetime, str]] = None) -> None:
        if initial_time is None:
            self._current_time = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        elif isinstance(initial_time, str):
            dt = datetime.fromisoformat(initial_time.replace("Z", "+00:00"))
            self._current_time = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        else:
            self._current_time = initial_time if initial_time.tzinfo else initial_time.replace(tzinfo=timezone.utc)

    def now_utc(self) -> datetime:
        return self._current_time

    def set_time(self, new_time: Union[datetime, str]) -> None:
        """Set explicit fake time."""
        if isinstance(new_time, str):
            dt = datetime.fromisoformat(new_time.replace("Z", "+00:00"))
            self._current_time = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        else:
            self._current_time = new_time if new_time.tzinfo else new_time.replace(tzinfo=timezone.utc)

    def advance(self, seconds: float = 0, minutes: float = 0, hours: float = 0, days: float = 0) -> None:
        """Advance fake time by given duration."""
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        self._current_time += delta
