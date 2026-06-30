from __future__ import annotations

import argparse
from dataclasses import dataclass
import shutil
import subprocess
import sys
from typing import Iterator

from .config import DEFAULT_MINUTES, DEFAULT_SOUND_PATH, MAX_MINUTES
from .sound import play_done_sound
from .timer import Timer
from .tui import Action, run_timer


@dataclass(frozen=True)
class PomodoroConfig:
    work_minutes: int
    break_minutes: int
    long_break_minutes: int | None = None
    rounds: int | None = None


@dataclass(frozen=True)
class PomodoroSession:
    title: str
    minutes: int


def parse_minutes(raw: str) -> int:
    try:
        minutes = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("minutes must be a positive integer") from exc

    if minutes <= 0:
        raise argparse.ArgumentTypeError("minutes must be a positive integer")
    if minutes > MAX_MINUTES:
        raise argparse.ArgumentTypeError(f"minutes must be {MAX_MINUTES} or less")
    return minutes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pomo", description="A small TUI pomodoro timer.")
    parser.add_argument("minutes", nargs="?", type=parse_minutes, help="timer duration in minutes")
    parser.add_argument("--sound", default=DEFAULT_SOUND_PATH, help="sound file to play when done")
    parser.add_argument(
        "--cycle",
        nargs=2,
        metavar=("WORK", "BREAK"),
        type=parse_minutes,
        help="repeat work and break timers until quit",
    )
    parser.add_argument("--work", type=parse_minutes, help="work duration in minutes for pomodoro cycles")
    parser.add_argument("--break", dest="break_minutes", type=parse_minutes, help="break duration in minutes")
    parser.add_argument("--long-break", type=parse_minutes, help="long break duration in minutes")
    parser.add_argument("--rounds", type=parse_minutes, help="work rounds before a long break")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = _cycle_config(args, parser)
    if config is not None:
        return _run_cycle(config, args.sound)

    minutes = args.minutes if args.minutes is not None else prompt_minutes()
    timer = Timer(minutes * 60)
    run_timer(timer, lambda: finish_alarm(args.sound))
    return 0


def _cycle_config(args: argparse.Namespace, parser: argparse.ArgumentParser) -> PomodoroConfig | None:
    uses_cycle_options = any(
        value is not None
        for value in (args.cycle, args.work, args.break_minutes, args.long_break, args.rounds)
    )
    if not uses_cycle_options:
        return None
    if args.minutes is not None:
        parser.error("minutes cannot be used with pomodoro cycle options")
    if args.cycle is not None and (args.work is not None or args.break_minutes is not None):
        parser.error("--cycle cannot be combined with --work or --break")

    if args.cycle is not None:
        work_minutes, break_minutes = args.cycle
    else:
        work_minutes = args.work
        break_minutes = args.break_minutes
        if work_minutes is None or break_minutes is None:
            parser.error("--work and --break must be used together")

    if args.long_break is not None and args.rounds is None:
        parser.error("--long-break requires --rounds")
    if args.rounds is not None and args.long_break is None:
        parser.error("--rounds requires --long-break")

    return PomodoroConfig(
        work_minutes=work_minutes,
        break_minutes=break_minutes,
        long_break_minutes=args.long_break,
        rounds=args.rounds,
    )


def _run_cycle(config: PomodoroConfig, sound_path: str) -> int:
    for session in pomodoro_sessions(config):
        timer = Timer(session.minutes * 60)
        action = run_timer(
            timer,
            lambda title=session.title: finish_alarm(sound_path, title, wait_for_sound=False),
            title=session.title,
            wait_on_finish=False,
        )
        if action == Action.QUIT:
            break
    return 0


def pomodoro_sessions(config: PomodoroConfig) -> Iterator[PomodoroSession]:
    round_count = 0
    while True:
        round_count += 1
        yield PomodoroSession(f"WORK {round_count}", config.work_minutes)

        if config.long_break_minutes is not None and config.rounds is not None and round_count % config.rounds == 0:
            yield PomodoroSession(f"LONG BREAK {round_count // config.rounds}", config.long_break_minutes)
        else:
            yield PomodoroSession(f"BREAK {round_count}", config.break_minutes)


def finish_alarm(sound_path: str, title: str = "pomo", wait_for_sound: bool = True) -> None:
    play_done_sound(sound_path, wait=wait_for_sound)
    notify_macos("Timer finished", "pomo")


def notify_macos(message: str, title: str = "pomo") -> bool:
    if not shutil.which("osascript"):
        return False
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{_escape_applescript(message)}" with title "{_escape_applescript(title)}"'],
            check=False,
        )
        return True
    except OSError:
        return False


def _escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def prompt_minutes() -> int:
    while True:
        try:
            raw = input(f"Minutes [{DEFAULT_MINUTES}]: ").strip()
        except EOFError:
            raw = ""

        if raw == "":
            return DEFAULT_MINUTES
        try:
            return parse_minutes(raw)
        except argparse.ArgumentTypeError as exc:
            print(f"error: {exc}", file=sys.stderr)


def main() -> None:
    raise SystemExit(run())
