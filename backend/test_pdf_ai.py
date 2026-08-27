import asyncio
import json

import main
import rag


def test_trim_history_keeps_system_and_last_n_exchanges():
    system = {"role": "system", "content": "S"}
    msgs = [system]
    for i in range(5):
        msgs.append({"role": "user", "content": f"u{i}"})
        msgs.append({"role": "assistant", "content": f"a{i}"})
    trimmed = main.trim_history(msgs, 2)  # system + últimes 2 parelles
    assert trimmed[0] is system
    assert [m["content"] for m in trimmed[1:]] == ["u3", "a3", "u4", "a4"]


def test_trim_history_shorter_than_limit_is_unchanged():
    msgs = [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "u"},
        {"role": "assistant", "content": "a"},
    ]
    assert main.trim_history(msgs, 3) == msgs


def test_trim_history_system_only():
    msgs = [{"role": "system", "content": "S"}]
    assert main.trim_history(msgs, 3) == msgs


def test_handle_pdf_message_bounds_history(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    monkeypatch.setattr(rag, "search", lambda q, top_k=2: ["CTX"])

    sizes = []

    async def fake_call(messages):
        sizes.append(len(messages))
        return "resp", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    monkeypatch.setattr(main, "call_groq", fake_call)

    for i in range(10):
        asyncio.run(m.handle_pdf_message("alice", f"pregunta {i}"))

    cap = 1 + 2 * main.PDF_MAX_EXCHANGES
    assert len(m.pdf_histories["alice"]) <= cap   # historial emmagatzemat acotat
    assert max(sizes) <= cap                       # cada petició a Groq acotada


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
