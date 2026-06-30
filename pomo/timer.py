from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
import time
from typing import Callable


class TimerState(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


Clock = Callable[[], float]


@dataclass
class Timer:
    total_seconds: int
    clock: Clock = time.monotonic
    _deadline: float = field(init=False)
    _paused_remaining: float | None = field(default=None, init=False)
    state: TimerState = field(default=TimerState.RUNNING, init=False)

    def __post_init__(self) -> None:
        if self.total_seconds <= 0:
            raise ValueError("total_seconds must be positive")
        self._deadline = self.clock() + self.total_seconds

    @property
    def remaining_seconds(self) -> int:
        remaining = self.remaining_float
        return int(math.ceil(remaining)) if remaining > 0 else 0

    @property
    def remaining_float(self) -> float:
        if self.state == TimerState.PAUSED:
            return max(0.0, self._paused_remaining or 0.0)
        if self.state == TimerState.FINISHED:
            return 0.0

        remaining = max(0.0, self._deadline - self.clock())
        if remaining <= 0:
            self.state = TimerState.FINISHED
            return 0.0
        return remaining

    @property
    def ratio_remaining(self) -> float:
        return min(1.0, max(0.0, self.remaining_float / self.total_seconds))

    @property
    def is_finished(self) -> bool:
        return self.remaining_seconds == 0

    @property
    def is_paused(self) -> bool:
        return self.state == TimerState.PAUSED

    def pause(self) -> None:
        if self.state != TimerState.RUNNING:
            return
        self._paused_remaining = max(0.0, self._deadline - self.clock())
        self.state = TimerState.PAUSED

    def resume(self) -> None:
        if self.state != TimerState.PAUSED:
            return
        self._deadline = self.clock() + max(0.0, self._paused_remaining or 0.0)
        self._paused_remaining = None
        self.state = TimerState.RUNNING

    def toggle_pause(self) -> None:
        if self.state == TimerState.PAUSED:
            self.resume()
        elif self.state == TimerState.RUNNING:
            self.pause()

    def restart(self) -> None:
        self._paused_remaining = None
        self._deadline = self.clock() + self.total_seconds
        self.state = TimerState.RUNNING


def format_remaining(seconds: int) -> str:
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{secs:02d}"
