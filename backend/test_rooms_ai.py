import asyncio
import json

import main


def _mgr_with_capture(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    monkeypatch.setattr(m, "send_text", fake_send)
    return m, sent


def test_room_history_seeded_with_system_prompt():
    m = main.ConnectionManager()
    history = m._ensure_room_history("r1")
    assert history[0]["role"] == "system"
    assert "Yuki" in history[0]["content"]
    assert m._ensure_room_history("r1") is history  # idempotent


def test_join_room_adds_yuki_without_limit(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    Y = main.YUKI_MEMBER
    # Yuki ja és a 3 rooms; sense bypass seria rebutjada pel límit.
    m.rooms = {"a": [Y], "b": [Y], "c": [Y]}
    asyncio.run(m.join_room("anna", "d", ["bob", Y]))
    assert "anna" in m.rooms["d"]
    assert "bob" in m.rooms["d"]
    assert Y in m.rooms["d"]
