from pomo.timer import Timer, TimerState, format_remaining


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_timer_counts_down_from_monotonic_deadline() -> None:
    clock = FakeClock()
    timer = Timer(60, clock=clock)

    clock.advance(12.2)

    assert timer.remaining_seconds == 48
    assert timer.state == TimerState.RUNNING


def test_timer_finishes_at_zero() -> None:
    clock = FakeClock()
    timer = Timer(10, clock=clock)

    clock.advance(10)

    assert timer.remaining_seconds == 0
    assert timer.state == TimerState.FINISHED
    assert timer.ratio_remaining == 0


def test_pause_freezes_remaining_and_resume_rebuilds_deadline() -> None:
    clock = FakeClock()
    timer = Timer(30, clock=clock)

    clock.advance(5)
    timer.pause()
    clock.advance(20)

    assert timer.remaining_seconds == 25

    timer.resume()
    clock.advance(10)

    assert timer.remaining_seconds == 15


def test_restart_uses_original_duration() -> None:
    clock = FakeClock()
    timer = Timer(20, clock=clock)

    clock.advance(19)
    timer.restart()

    assert timer.remaining_seconds == 20
    assert timer.state == TimerState.RUNNING


def test_format_remaining() -> None:
    assert format_remaining(0) == "00:00"
    assert format_remaining(59) == "00:59"
    assert format_remaining(60) == "01:00"
    assert format_remaining(754) == "12:34"
