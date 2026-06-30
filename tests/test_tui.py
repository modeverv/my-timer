from pomo.tui import COLOR_EMPTY, COLOR_GREEN, COLOR_RED, COLOR_YELLOW, _progress_bar, _progress_parts, _segments_for_width


def test_progress_bar_decreases_active_segments() -> None:
    assert _progress_bar(1.0, 4) == "████ ████ ████ ████"
    assert _progress_bar(0.5, 4) == "████ ████ ░░░░ ░░░░"
    assert _progress_bar(0.0, 4) == "░░░░ ░░░░ ░░░░ ░░░░"


def test_segments_for_width_caps_to_available_columns() -> None:
    assert _segments_for_width(80, 24) == 15
    assert _segments_for_width(200, 24) == 24
    assert _segments_for_width(8, 24) == 1


def test_progress_parts_assigns_active_and_empty_colors() -> None:
    assert _progress_parts(1.0, 4) == [
        ("████", COLOR_RED),
        ("████", COLOR_RED),
        ("████", COLOR_YELLOW),
        ("████", COLOR_GREEN),
    ]
    assert _progress_parts(0.25, 4) == [
        ("████", COLOR_RED),
        ("░░░░", COLOR_EMPTY),
        ("░░░░", COLOR_EMPTY),
        ("░░░░", COLOR_EMPTY),
    ]
