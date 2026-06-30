import argparse
import itertools

import pytest

from pomo.app import PomodoroConfig, _escape_applescript, notify_macos, parse_minutes, pomodoro_sessions, run
from pomo.tui import Action


@pytest.mark.parametrize("raw, expected", [("1", 1), ("5", 5), ("25", 25)])
def test_parse_minutes_accepts_positive_integers(raw: str, expected: int) -> None:
    assert parse_minutes(raw) == expected


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "1.5", ""])
def test_parse_minutes_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_minutes(raw)


def test_pomodoro_sessions_repeats_work_and_break() -> None:
    config = PomodoroConfig(work_minutes=25, break_minutes=5)

    sessions = list(itertools.islice(pomodoro_sessions(config), 4))

    assert [(session.title, session.minutes) for session in sessions] == [
        ("WORK 1", 25),
        ("BREAK 1", 5),
        ("WORK 2", 25),
        ("BREAK 2", 5),
    ]


def test_pomodoro_sessions_uses_long_break_after_rounds() -> None:
    config = PomodoroConfig(work_minutes=25, break_minutes=5, long_break_minutes=15, rounds=4)

    sessions = list(itertools.islice(pomodoro_sessions(config), 8))

    assert [(session.title, session.minutes) for session in sessions] == [
        ("WORK 1", 25),
        ("BREAK 1", 5),
        ("WORK 2", 25),
        ("BREAK 2", 5),
        ("WORK 3", 25),
        ("BREAK 3", 5),
        ("WORK 4", 25),
        ("LONG BREAK 1", 15),
    ]


def test_run_cycle_stops_when_tui_returns_quit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, str, bool]] = []
    actions = iter([Action.DONE, Action.QUIT])

    def fake_run_timer(timer, on_finish, segments=24, title="POMODORO", wait_on_finish=True):
        calls.append((timer.total_seconds, title, wait_on_finish))
        return next(actions)

    monkeypatch.setattr("pomo.app.run_timer", fake_run_timer)

    assert run(["--cycle", "25", "5"]) == 0
    assert calls == [(1500, "WORK 1", False), (300, "BREAK 1", False)]


def test_run_cycle_repeats_cycle_minutes_until_quit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, str, bool]] = []
    actions = iter([Action.DONE, Action.DONE, Action.DONE, Action.QUIT])

    def fake_run_timer(timer, on_finish, segments=24, title="POMODORO", wait_on_finish=True):
        calls.append((timer.total_seconds, title, wait_on_finish))
        return next(actions)

    monkeypatch.setattr("pomo.app.run_timer", fake_run_timer)

    assert run(["--cycle", "25", "5"]) == 0
    assert calls == [
        (1500, "WORK 1", False),
        (300, "BREAK 1", False),
        (1500, "WORK 2", False),
        (300, "BREAK 2", False),
    ]


def test_notify_macos_uses_osascript(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []

    monkeypatch.setattr("pomo.app.shutil.which", lambda command: "/usr/bin/osascript" if command == "osascript" else None)
    monkeypatch.setattr("pomo.app.subprocess.run", lambda command, check=False: commands.append(command))

    assert notify_macos("Timer finished", "pomo") is True
    assert commands == [["osascript", "-e", 'display notification "Timer finished" with title "pomo"']]


def test_notify_macos_returns_false_without_osascript(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pomo.app.shutil.which", lambda command: None)

    assert notify_macos("Timer finished", "pomo") is False


def test_notify_macos_returns_false_on_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_os_error(command, check=False):
        raise OSError

    monkeypatch.setattr("pomo.app.shutil.which", lambda command: "/usr/bin/osascript")
    monkeypatch.setattr("pomo.app.subprocess.run", raise_os_error)

    assert notify_macos("Timer finished", "pomo") is False


def test_escape_applescript_quotes_and_backslashes() -> None:
    assert _escape_applescript('a "quote" and \\') == 'a \\"quote\\" and \\\\'
