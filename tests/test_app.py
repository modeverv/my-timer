import argparse

import pytest

from pomo.app import parse_minutes


@pytest.mark.parametrize("raw, expected", [("1", 1), ("5", 5), ("25", 25)])
def test_parse_minutes_accepts_positive_integers(raw: str, expected: int) -> None:
    assert parse_minutes(raw) == expected


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "1.5", ""])
def test_parse_minutes_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_minutes(raw)
