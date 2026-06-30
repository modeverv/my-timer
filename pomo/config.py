from pathlib import Path


DEFAULT_MINUTES = 25
DEFAULT_SOUND_PATH = str(Path(__file__).with_name("assets") / "alarm-or-siren.mp3")
DEFAULT_SEGMENTS = 24
MAX_MINUTES = 24 * 60
TICK_INTERVAL_SEC = 1

