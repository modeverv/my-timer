from __future__ import annotations

import argparse
import sys

from .config import DEFAULT_MINUTES, DEFAULT_SOUND_PATH, MAX_MINUTES
from .sound import play_done_sound
from .timer import Timer
from .tui import run_timer


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
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    minutes = args.minutes if args.minutes is not None else prompt_minutes()

    timer = Timer(minutes * 60)
    run_timer(timer, lambda: play_done_sound(args.sound))
    return 0


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
