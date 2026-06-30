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


def test_send_to_room_mention_calls_groq_and_broadcasts(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    m.rooms = {"r1": ["anna", "bob"]}  # cap "Yuki" membre: la Yuki és ambient

    async def fake_call(messages):
        return "Hola a tothom!", {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        }

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to_room("anna", "r1", "ei @yuki què tal?"))

    history = m.room_ai_histories["r1"]
    assert [x["role"] for x in history] == ["system", "user", "assistant"]
    assert history[1]["content"] == "anna: ei @yuki què tal?"

    roomai = [(u, msg) for (u, msg) in sent if msg.startswith("ROOMAI:")]
    recipients = [u for (u, msg) in roomai]
    assert "anna" in recipients and "bob" in recipients  # inclòs el remitent
    payload = json.loads(roomai[0][1][len("ROOMAI:r1:"):])
    assert payload["text"] == "Hola a tothom!"
    assert payload["usage"]["total_tokens"] == 15


def test_send_to_room_no_mention_grows_history_without_groq(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    m.rooms = {"r1": ["anna", "bob"]}
    called = []

    async def fake_call(messages):
        called.append(1)
        return "x", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to_room("anna", "r1", "hola sense mencio"))

    assert called == []
    history = m.room_ai_histories["r1"]
    assert [x["role"] for x in history] == ["system", "user"]
    assert not any(msg.startswith("ROOMAI:") for (u, msg) in sent)
