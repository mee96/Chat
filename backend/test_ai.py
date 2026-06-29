import asyncio
import json

import main


def test_history_seeded_with_system_prompt():
    m = main.ConnectionManager()
    history = m._ensure_ai_history("alice")
    assert history[0]["role"] == "system"
    assert "Yuki" in history[0]["content"]
    # Cridar-ho dos cops no duplica el system prompt.
    again = m._ensure_ai_history("alice")
    assert again is history
    assert len([msg for msg in again if msg["role"] == "system"]) == 1


def test_handle_ai_message_appends_and_sends(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    async def fake_call(messages):
        return "Hola! soc la Yuki", {
            "prompt_tokens": 5,
            "completion_tokens": 7,
            "total_tokens": 12,
        }

    monkeypatch.setattr(m, "send_text", fake_send)
    monkeypatch.setattr(main, "call_groq", fake_call)

    asyncio.run(m.handle_ai_message("alice", "qui ets?"))

    history = m.ai_histories["alice"]
    assert [msg["role"] for msg in history] == ["system", "user", "assistant"]
    assert history[1]["content"] == "qui ets?"
    assert history[2]["content"] == "Hola! soc la Yuki"

    assert len(sent) == 1
    username, message = sent[0]
    assert username == "alice"
    assert message.startswith("AI:")
    payload = json.loads(message[len("AI:"):])
    assert payload["text"] == "Hola! soc la Yuki"
    assert payload["usage"]["total_tokens"] == 12


def test_handle_ai_message_error_path(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    async def fake_call(messages):
        raise RuntimeError("groq down")

    monkeypatch.setattr(m, "send_text", fake_send)
    monkeypatch.setattr(main, "call_groq", fake_call)

    asyncio.run(m.handle_ai_message("bob", "hola"))

    history = m.ai_histories["bob"]
    # L'usuari hi és, però NO s'afegeix cap resposta d'assistant fallida.
    assert [msg["role"] for msg in history] == ["system", "user"]
    payload = json.loads(sent[0][1][len("AI:"):])
    assert payload["usage"] is None
    assert "no s'ha pogut" in payload["text"]
