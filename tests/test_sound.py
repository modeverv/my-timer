from pomo import sound


def test_play_done_sound_uses_afplay_when_available(monkeypatch) -> None:
    calls = []

    monkeypatch.setattr(sound.shutil, "which", lambda name: "/usr/bin/afplay")
    monkeypatch.setattr(sound.subprocess, "run", lambda args, check: calls.append((args, check)))

    assert sound.play_done_sound("/tmp/done.aiff") is True
    assert calls == [(["afplay", "/tmp/done.aiff"], False)]


def test_play_done_sound_falls_back_to_bell(monkeypatch) -> None:
    writes = []

    monkeypatch.setattr(sound.shutil, "which", lambda name: None)
    monkeypatch.setattr(sound.sys.stdout, "write", lambda value: writes.append(value))
    monkeypatch.setattr(sound.sys.stdout, "flush", lambda: None)

    assert sound.play_done_sound("/tmp/done.aiff") is False
    assert writes == ["\a"]
