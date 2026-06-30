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


def test_pair_key_symmetric():
    assert main.ConnectionManager._pair_key("carme", "pau") == \
           main.ConnectionManager._pair_key("pau", "carme")


def test_send_text_exact_connection_no_prefix_match():
    m = main.ConnectionManager()
    received = {"carme": [], "carme-mobil": []}

    class FakeSocket:
        def __init__(self, name):
            self.name = name

        async def send_text(self, msg):
            received[self.name].append(msg)

    m.connections = {
        "carme": FakeSocket("carme"),
        "carme-mobil": FakeSocket("carme-mobil"),
    }
    asyncio.run(m.send_text("carme-mobil", "hi"))
    assert received["carme-mobil"] == ["hi"]
    assert received["carme"] == []  # cap lliurament per prefix/substring


def test_direct_mention_calls_groq_and_sends_to_both(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)

    async def fake_call(messages):
        return "Sóc la Yuki!", {
            "prompt_tokens": 8,
            "completion_tokens": 4,
            "total_tokens": 12,
        }

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to("carme", "pau", "@yuki ajuda"))

    key = main.ConnectionManager._pair_key("carme", "pau")
    history = m.direct_ai_histories[key]
    assert [x["role"] for x in history] == ["system", "user", "assistant"]
    assert history[1]["content"] == "carme: @yuki ajuda"

    directai = [(u, msg) for (u, msg) in sent if msg.startswith("DIRECTAI:")]
    by_recipient = {u: msg for (u, msg) in directai}
    assert by_recipient["carme"].startswith("DIRECTAI:pau:")
    assert by_recipient["pau"].startswith("DIRECTAI:carme:")
    payload = json.loads(by_recipient["carme"][len("DIRECTAI:pau:"):])
    assert payload["text"] == "Sóc la Yuki!"
    assert payload["usage"]["total_tokens"] == 12


def test_direct_no_mention_grows_history_without_groq(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    called = []

    async def fake_call(messages):
        called.append(1)
        return "x", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to("carme", "pau", "hola sense mencio"))

    assert called == []
    key = main.ConnectionManager._pair_key("carme", "pau")
    assert [x["role"] for x in m.direct_ai_histories[key]] == ["system", "user"]
    assert not any(msg.startswith("DIRECTAI:") for (u, msg) in sent)
