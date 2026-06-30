from __future__ import annotations

import shutil
import subprocess
import sys

from .config import DEFAULT_SOUND_PATH


def play_done_sound(sound_path: str = DEFAULT_SOUND_PATH) -> bool:
    """Play the completion sound, returning whether afplay was used."""
    if shutil.which("afplay"):
        try:
            subprocess.run(["afplay", sound_path], check=False)
            return True
        except OSError:
            pass

    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except OSError:
        pass
    return False
