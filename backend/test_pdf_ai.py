import asyncio
import json

from fastapi.testclient import TestClient

import main
import rag


def test_startup_preloads_embedding_model(monkeypatch):
    # El model s'ha de precarregar a l'arrencada (lifespan), no de forma lazy a
    # la primera petició, perquè el primer RAG no falli ni bloquegi el loop.
    calls = []
    monkeypatch.setattr(rag, "get_model", lambda: calls.append("loaded"))
    with TestClient(main.app):
        pass
    assert calls == ["loaded"]


def _mgr_with_capture(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    monkeypatch.setattr(m, "send_text", fake_send)
    return m, sent


def test_pdf_history_seeded_with_system_prompt():
    m = main.ConnectionManager()
    history = m._ensure_pdf_history("alice")
    assert history[0]["role"] == "system"
    assert "gramática española" in history[0]["content"]
    assert m._ensure_pdf_history("alice") is history  # idempotent


def test_pdf_system_prompt_grounds_and_guards_outside_knowledge():
    # Ancorat al context + frase de rebuig clara + prohibició de coneixement
    # extern per a preguntes fora de la gramàtica (p. ex. "la capital de França").
    # Però NO tan estricte que rebutgi gramàtica bàsica (això ho valida l'ús real).
    prompt = main.PDF_SYSTEM_PROMPT.lower()
    assert "contexto" in prompt
    assert "no encuentro esa información en los libros" in prompt
    assert "conocimiento externo" in prompt


def test_handle_pdf_message_retrieves_context_and_sends(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    monkeypatch.setattr(rag, "search", lambda q, top_k=3: ["CHUNK U", "CHUNK D"])

    async def fake_call(messages):
        return "El plural es forma...", {
            "prompt_tokens": 20,
            "completion_tokens": 8,
            "total_tokens": 28,
        }

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.handle_pdf_message("alice", "com es fa el plural?"))

    history = m.pdf_histories["alice"]
    assert [x["role"] for x in history] == ["system", "user", "assistant"]
    user_turn = history[1]["content"]
    assert "Contexto:" in user_turn
    assert "CHUNK U" in user_turn and "CHUNK D" in user_turn
    assert "Pregunta: com es fa el plural?" in user_turn

    assert len(sent) == 1
    username, message = sent[0]
    assert username == "alice"
    assert message.startswith("PDF:")
    payload = json.loads(message[len("PDF:"):])
    assert payload["text"] == "El plural es forma..."
    assert payload["usage"]["total_tokens"] == 28


def test_handle_pdf_message_groq_error(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    monkeypatch.setattr(rag, "search", lambda q, top_k=3: ["CHUNK U"])

    async def fake_call(messages):
        raise RuntimeError("groq down")

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.handle_pdf_message("bob", "hola"))

    history = m.pdf_histories["bob"]
    assert [x["role"] for x in history] == ["system", "user"]  # sense assistant fallit
    payload = json.loads(sent[0][1][len("PDF:"):])
    assert payload["usage"] is None
    assert payload["text"] == main.PDF_ERROR_MESSAGE


def test_handle_pdf_message_search_error(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)

    def boom(q, top_k=3):
        raise RuntimeError("qdrant down")

    monkeypatch.setattr(rag, "search", boom)
    asyncio.run(m.handle_pdf_message("carol", "hola"))

    assert "carol" not in m.pdf_histories  # no s'ha creat historial
    payload = json.loads(sent[0][1][len("PDF:"):])
    assert payload["usage"] is None
    assert payload["text"] == main.PDF_ERROR_MESSAGE


def test_pdf_error_message_is_friendly_spanish():
    # Missatge amable i en castellà (coherent amb la resta del chatbot).
    assert main.PDF_ERROR_MESSAGE == (
        "Lo siento, ha habido un problema al consultar los libros. "
        "Por favor, inténtalo de nuevo."
    )
