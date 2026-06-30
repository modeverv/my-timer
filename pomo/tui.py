from __future__ import annotations

import curses
import math
import time

from .config import DEFAULT_SEGMENTS, TICK_INTERVAL_SEC
from .timer import Timer, TimerState, format_remaining


COLOR_GREEN = 1
COLOR_YELLOW = 2
COLOR_RED = 3
COLOR_EMPTY = 4


class Action:
    QUIT = "quit"
    DONE = "done"


def run_timer(
    timer: Timer,
    on_finish,
    segments: int = DEFAULT_SEGMENTS,
    title: str = "POMODORO",
    wait_on_finish: bool = True,
) -> str:
    return curses.wrapper(_run, timer, on_finish, segments, title, wait_on_finish)


def _run(stdscr, timer: Timer, on_finish, segments: int, title: str, wait_on_finish: bool) -> str:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    if curses.has_colors():
        _init_colors()

    sound_played = False

    while True:
        if timer.is_finished and not sound_played:
            on_finish()
            if not wait_on_finish:
                return Action.DONE
            sound_played = True

        _draw(stdscr, timer, segments, sound_played, title)
        key = stdscr.getch()

        if key in (ord("q"), ord("Q"), 3):
            return Action.QUIT
        if key in (ord("p"), ord("P")) and timer.state != TimerState.FINISHED:
            timer.toggle_pause()
        elif key in (ord("r"), ord("R")):
            timer.restart()
            sound_played = False
        elif timer.state == TimerState.FINISHED and key != -1:
            return Action.DONE

        time.sleep(TICK_INTERVAL_SEC)


def _draw(stdscr, timer: Timer, segments: int, sound_played: bool, title: str = "POMODORO") -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    status = _status_label(timer, sound_played)
    time_text = "DONE" if timer.state == TimerState.FINISHED else format_remaining(timer.remaining_seconds)
    help_text = "p: pause/resume   r: restart   q: quit"

    progress_row = 2
    rows = [title if status == "" else f"{title}  {status}", "", "", "", time_text, "", help_text]

    top = max(0, (height - len(rows)) // 2)
    for offset, text in enumerate(rows):
        row = top + offset
        if row >= height:
            break
        _add_centered(stdscr, row, text[: max(0, width - 1)])

    if top + progress_row < height:
        _add_progress_bar(stdscr, top + progress_row, timer.ratio_remaining, _segments_for_width(width, segments))

    stdscr.refresh()


def _status_label(timer: Timer, sound_played: bool) -> str:
    if timer.state == TimerState.PAUSED:
        return "[PAUSED]"
    if timer.state == TimerState.FINISHED:
        return "[DONE]" if sound_played else "[FINISHING]"
    return ""


def _progress_bar(ratio_remaining: float, segments: int) -> str:
    active = int(math.ceil(segments * ratio_remaining)) if ratio_remaining > 0 else 0
    parts = []
    for index in range(segments):
        parts.append("████" if index < active else "░░░░")
    return " ".join(parts)


def _progress_parts(ratio_remaining: float, segments: int) -> list[tuple[str, int]]:
    active = int(math.ceil(segments * ratio_remaining)) if ratio_remaining > 0 else 0
    parts = []
    for index in range(segments):
        segment_ratio = (index + 1) / max(1, segments)
        if index >= active:
            parts.append(("░░░░", COLOR_EMPTY))
        elif segment_ratio <= 0.5:
            parts.append(("████", COLOR_RED))
        elif segment_ratio <= 0.8:
            parts.append(("████", COLOR_YELLOW))
        else:
            parts.append(("████", COLOR_GREEN))
    return parts


def _add_progress_bar(stdscr, row: int, ratio_remaining: float, segments: int) -> None:
    parts = _progress_parts(ratio_remaining, segments)
    text_width = max(0, segments * 4 + max(0, segments - 1))
    _, width = stdscr.getmaxyx()
    col = max(0, (width - text_width) // 2)

    for index, (text, color_pair) in enumerate(parts):
        attr = curses.color_pair(color_pair) if _colors_ready() else curses.A_NORMAL
        try:
            stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass
        col += len(text)
        if index != len(parts) - 1:
            try:
                stdscr.addstr(row, col, " ")
            except curses.error:
                pass
            col += 1


def _segments_for_width(width: int, preferred: int) -> int:
    if width <= 12:
        return 1
    max_segments = max(1, (width - 2 + 1) // 5)
    return max(1, min(preferred, max_segments))


def _add_centered(stdscr, row: int, text: str) -> None:
    _, width = stdscr.getmaxyx()
    col = max(0, (width - len(text)) // 2)
    try:
        stdscr.addstr(row, col, text)
    except curses.error:
        pass


def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_RED, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_EMPTY, curses.COLOR_BLACK, -1)


def _colors_ready() -> bool:
    try:
        return curses.has_colors() and curses.COLORS > 0
    except curses.error:
        return False
