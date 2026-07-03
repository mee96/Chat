# RAG "Gramàtica" (PDF + Qdrant) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un xat RAG "📚 Gramàtica" que respon preguntes sobre 3 PDFs (Gramática descriptiva) indexats a Qdrant: `PDF:<pregunta>` → recupera chunks rellevants → Groq respon només amb aquest context.

**Architecture:** Un sol model d'embeddings via fastembed (ONNX, sense torch) a ingesta i query. `ingest_pdf.py` (offline) indexa a Qdrant; `rag.py` fa la cerca; `main.py` afegeix el prefix `PDF:` (mirall d'`AI:`); el frontend afegeix un xat ancorat que usa `PDF:`.

**Tech Stack:** Backend FastAPI + qdrant-client + fastembed + pdfplumber (ingesta) + pytest. Frontend Angular 21 (signals) + Vitest.

## Global Constraints

- Model d'embeddings (ingesta i query): `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, dimensió **384**, distància **cosinus**. Via **fastembed** (sense torch).
- Col·lecció Qdrant: **`gramatica`**. Connexió amb `QDRANT_URL` i `QDRANT_API_KEY` del `.env`.
- Chunking: ~**500** paraules amb ~**50** de solapament.
- `requirements.txt` (Render) afegeix `fastembed==0.8.0` i **no** conté `pdfplumber`. `requirements-rag.txt` = `-r requirements.txt` + `pdfplumber` (sense `sentence-transformers`).
- Protocol nou: client→servidor `PDF:<pregunta>`; servidor→client `PDF:` + JSON `{"text": str, "usage": {...} | null}` (mateix format que `AI:`).
- System prompt del RAG (castellà, EXACTE): `"Eres un asistente experto en gramática española. Responde ÚNICAMENTE basándote en el contexto proporcionado. Si la pregunta no tiene respuesta en el contexto, di explícitamente que no encuentras esa información en los libros. No inventes información."`
- Historial `PDF:` per usuari, sembrat amb el system prompt.
- Angular 21: `@if`/`@for`, class bindings (no `ngClass`/`ngStyle`), signals `.set`/`.update` (no `.mutate`), sense `standalone: true`.
- Backend: comandes des de `backend/` amb `./venv/Scripts/python.exe`; tests `./venv/Scripts/python.exe -m pytest <fitxer> -v`.
- Frontend: des de `frontend/chat-app/`; build `npm run build`; tests `npm run test:unit`.

---

### Task 1: Dependències — fastembed al servidor, pdfplumber només a RAG

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/requirements-rag.txt`

**Interfaces:**
- Produces: `fastembed` disponible al venv per al servidor; `sentence-transformers` eliminat de requirements-rag.txt.

- [ ] **Step 1: Reescriure `backend/requirements.txt`** amb aquest contingut exacte:

```
fastapi==0.136.3
uvicorn==0.49.0
websockets==16.0
groq==1.5.0
python-dotenv==1.2.2
qdrant-client==1.18.0
fastembed==0.8.0
```

- [ ] **Step 2: Reescriure `backend/requirements-rag.txt`** amb aquest contingut exacte:

```
# Dependències per a la ingesta/RAG offline — NO les instal·la Render.
# S'instal·len a part (en local) per processar el PDF. La cerca en temps real i
# els embeddings usen fastembed (ONNX, lleuger), que ja és al requirements.txt.
#
# Ús:  pip install -r requirements-rag.txt

-r requirements.txt

pdfplumber==0.11.10
```

- [ ] **Step 3: Verificar que fastembed està instal·lat i importa**

Run (des de `backend/`): `./venv/Scripts/python.exe -c "import fastembed, qdrant_client, pdfplumber; print('ok')"`
Expected: `ok` (les tres ja estan instal·lades al venv).

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt backend/requirements-rag.txt
git commit -m "build(backend): fastembed al servidor; pdfplumber només a RAG"
```

---

### Task 2: `rag.py` — cerca a Qdrant amb fastembed

**Files:**
- Create/replace: `backend/rag.py` (ara és un placeholder amb només comentaris)
- Test: `backend/test_rag.py`

**Interfaces:**
- Produces:
  - `rag.COLLECTION = "gramatica"`, `rag.EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"`, `rag.VECTOR_SIZE = 384`
  - `rag.get_model() -> TextEmbedding` (lazy)
  - `rag.get_client() -> QdrantClient` (lazy, de l'entorn)
  - `rag.embed_one(text: str) -> list[float]`
  - `rag.search(query: str, top_k: int = 3) -> list[str]`

- [ ] **Step 1: Escriure el test que falla** — crear `backend/test_rag.py`:

```python
import rag


def test_search_returns_chunk_texts_in_order(monkeypatch):
    monkeypatch.setattr(rag, "embed_one", lambda q: [0.0] * rag.VECTOR_SIZE)

    class FakePoint:
        def __init__(self, text):
            self.payload = {"text": text}

    class FakeResult:
        points = [FakePoint("chunk A"), FakePoint("chunk B")]

    class FakeClient:
        def query_points(self, collection_name, query, limit):
            assert collection_name == rag.COLLECTION
            assert limit == 3
            assert query == [0.0] * rag.VECTOR_SIZE
            return FakeResult()

    monkeypatch.setattr(rag, "get_client", lambda: FakeClient())

    assert rag.search("com es fa el plural?", top_k=3) == ["chunk A", "chunk B"]
```

- [ ] **Step 2: Executar per veure'l fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rag.py -v`
Expected: FAIL (`AttributeError: module 'rag' has no attribute 'search'` — el placeholder actual no té codi).

- [ ] **Step 3: Implementar `backend/rag.py`** — substituir tot el contingut del fitxer per:

```python
"""rag.py — Recuperació (retrieval) per al xat de gramàtica: cerca a Qdrant.

Els embeddings (ingesta i query) usen el mateix model via fastembed (ONNX, sense
torch), de manera que els vectors són compatibles. El client de Qdrant i el model
s'inicialitzen de forma lazy (una sola vegada) amb QDRANT_URL/QDRANT_API_KEY del .env.
"""

import os

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

COLLECTION = "gramatica"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_SIZE = 384

_model: TextEmbedding | None = None
_client: QdrantClient | None = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBED_MODEL)
    return _model


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            url=os.environ.get("QDRANT_URL"),
            api_key=os.environ.get("QDRANT_API_KEY"),
        )
    return _client


def embed_one(text: str) -> list[float]:
    return list(get_model().embed([text]))[0].tolist()


def search(query: str, top_k: int = 3) -> list[str]:
    vector = embed_one(query)
    result = get_client().query_points(
        collection_name=COLLECTION, query=vector, limit=top_k
    )
    return [point.payload["text"] for point in result.points]
```

- [ ] **Step 4: Executar per veure'l passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rag.py -v`
Expected: PASS (1 test). (El test monkeypatcheja `embed_one` i `get_client`, així que no descarrega el model ni toca Qdrant.)

- [ ] **Step 5: Commit**

```bash
git add backend/rag.py backend/test_rag.py
git commit -m "feat(backend): rag.search() — cerca a Qdrant amb fastembed"
```

---

### Task 3: `main.py` — prefix `PDF:` amb RAG

**Files:**
- Modify: `backend/main.py`
- Test: `backend/test_pdf_ai.py`

**Interfaces:**
- Consumes: `rag.search` (Task 2), `call_groq`, `logger`, `send_text` existents.
- Produces:
  - `main.PDF_SYSTEM_PROMPT`
  - `ConnectionManager.pdf_histories: dict[str, list[dict]]`
  - `ConnectionManager._ensure_pdf_history(username) -> list[dict]`
  - `ConnectionManager.handle_pdf_message(username, query) -> None`
  - Branca de routing `PDF:` al `websocket_endpoint`.

- [ ] **Step 1: Escriure els tests que fallen** — crear `backend/test_pdf_ai.py`:

```python
import asyncio
import json

import main
import rag


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


def test_handle_pdf_message_search_error(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)

    def boom(q, top_k=3):
        raise RuntimeError("qdrant down")

    monkeypatch.setattr(rag, "search", boom)
    asyncio.run(m.handle_pdf_message("carol", "hola"))

    assert "carol" not in m.pdf_histories  # no s'ha creat historial
    payload = json.loads(sent[0][1][len("PDF:"):])
    assert payload["usage"] is None
```

- [ ] **Step 2: Executar per veure'ls fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_pdf_ai.py -v`
Expected: FAIL (`AttributeError: ... _ensure_pdf_history` / `PDF_SYSTEM_PROMPT`).

- [ ] **Step 3: Importar `rag` i afegir el system prompt** — a `backend/main.py`, afegir amb les altres importacions de tercers/locals (a prop de `from groq import AsyncGroq`):

```python
import rag
```

I després de la definició d'`AI_SYSTEM_PROMPT`, afegir:

```python
PDF_SYSTEM_PROMPT = (
    "Eres un asistente experto en gramática española. Responde ÚNICAMENTE "
    "basándote en el contexto proporcionado. Si la pregunta no tiene respuesta "
    "en el contexto, di explícitamente que no encuentras esa información en los "
    "libros. No inventes información."
)
```

- [ ] **Step 4: Afegir l'historial PDF i el helper** — a `ConnectionManager.__init__`, sota `self.direct_ai_histories`:

```python
        self.pdf_histories: dict[str, list[dict]] = {}
```

I afegir aquest mètode a `ConnectionManager` (p. ex. just abans de `# ---- Rooms ----`):

```python
    def _ensure_pdf_history(self, username: str) -> list[dict]:
        history = self.pdf_histories.get(username)
        if history is None:
            history = [{"role": "system", "content": PDF_SYSTEM_PROMPT}]
            self.pdf_histories[username] = history
        return history

    async def handle_pdf_message(self, username: str, query: str):
        try:
            chunks = rag.search(query)
        except Exception:
            logger.exception("RAG search failed for %s", username)
            await self.send_text(
                username,
                "PDF:" + json.dumps(
                    {"text": "⚠️ no s'ha pogut consultar els llibres", "usage": None}
                ),
            )
            return
        history = self._ensure_pdf_history(username)
        context = "\n---\n".join(chunks)
        history.append({
            "role": "user",
            "content": f"Contexto:\n{context}\n\nPregunta: {query}",
        })
        try:
            reply, usage = await call_groq(history)
        except Exception:
            logger.exception("Groq PDF call failed for %s", username)
            await self.send_text(
                username,
                "PDF:" + json.dumps(
                    {"text": "⚠️ no s'ha pogut consultar els llibres", "usage": None}
                ),
            )
            return
        history.append({"role": "assistant", "content": reply})
        await self.send_text(
            username,
            "PDF:" + json.dumps({"text": reply, "usage": usage}),
        )
```

- [ ] **Step 5: Afegir la branca de routing `PDF:`** — a `backend/main.py`, dins el `while True` del `websocket_endpoint`, afegir un `elif` just després de la branca `AI:` i abans de l'`else`:

```python
            elif data.startswith("PDF:"):
                await manager.handle_pdf_message(username, data[len("PDF:"):])
```

- [ ] **Step 6: Executar per veure'ls passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_pdf_ai.py -v`
Expected: PASS (4 tests).

- [ ] **Step 7: Tota la suite verda + import del mòdul**

Run (des de `backend/`): `./venv/Scripts/python.exe -c "import main; print('import ok')"` → Expected: `import ok`.
Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest -v` → Expected: PASS (test_ai 3 + test_rooms_ai 3 + test_direct_ai 4 + test_rag 1 + test_pdf_ai 4 = 15).

- [ ] **Step 8: Commit**

```bash
git add backend/main.py backend/test_pdf_ai.py
git commit -m "feat(backend): prefix PDF: — RAG amb Qdrant + Groq"
```

---

### Task 4: `ingest_pdf.py` — chunking + indexat a Qdrant

**Files:**
- Create/replace: `backend/ingest_pdf.py` (ara és un placeholder amb només comentaris)
- Test: `backend/test_ingest.py`

**Interfaces:**
- Consumes: `rag.COLLECTION`, `rag.VECTOR_SIZE`, `rag.get_client`, `rag.get_model` (Task 2).
- Produces: `ingest_pdf.chunk_text(text, size=500, overlap=50) -> list[str]` (funció pura de nivell superior); la resta de la ingesta viu sota `if __name__ == "__main__":`.

- [ ] **Step 1: Escriure els tests que fallen** — crear `backend/test_ingest.py`:

```python
import ingest_pdf


def test_chunk_text_size_and_overlap():
    words = [f"w{i}" for i in range(1000)]
    text = " ".join(words)
    chunks = ingest_pdf.chunk_text(text, size=500, overlap=50)
    # step = 500 - 50 = 450 -> inicis 0, 450, 900
    assert len(chunks) == 3
    assert chunks[0].split()[0] == "w0"
    assert len(chunks[0].split()) == 500
    assert chunks[1].split()[0] == "w450"   # solapament de 50 amb l'anterior
    assert chunks[2].split()[0] == "w900"
    assert len(chunks[2].split()) == 100     # últim chunk més curt


def test_chunk_text_short_text_single_chunk():
    chunks = ingest_pdf.chunk_text("una dos tres", size=500, overlap=50)
    assert chunks == ["una dos tres"]


def test_chunk_text_empty():
    assert ingest_pdf.chunk_text("") == []
```

- [ ] **Step 2: Executar per veure'ls fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_ingest.py -v`
Expected: FAIL (`AttributeError: module 'ingest_pdf' has no attribute 'chunk_text'`).

- [ ] **Step 3: Implementar `backend/ingest_pdf.py`** — substituir tot el contingut del fitxer per:

```python
"""ingest_pdf.py — Ingesta offline dels PDFs cap a Qdrant (s'executa en local).

Llegeix els PDFs de backend/pdfs/, els parteix en chunks, genera embeddings amb
fastembed (mateix model que la cerca) i els indexa a la col·lecció de Qdrant.
NO s'executa a Render. Ús:  python ingest_pdf.py [ruta1.pdf ruta2.pdf ...]
"""

import glob
import os
import sys

import pdfplumber
from qdrant_client.models import Distance, PointStruct, VectorParams

from rag import COLLECTION, VECTOR_SIZE, get_client, get_model

PDF_DIR = os.path.join(os.path.dirname(__file__), "pdfs")


def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """Parteix `text` en chunks de ~`size` paraules amb `overlap` de solapament."""
    words = text.split()
    if not words:
        return []
    step = max(size - overlap, 1)
    chunks: list[str] = []
    for start in range(0, len(words), step):
        chunk = words[start:start + size]
        if chunk:
            chunks.append(" ".join(chunk))
        if start + size >= len(words):
            break
    return chunks


def main() -> None:
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    if not paths:
        print(f"No s'han trobat PDFs a {PDF_DIR}")
        return

    model = get_model()
    client = get_client()
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    point_id = 0
    total_pages = 0
    total_chunks = 0
    for path in paths:
        source = os.path.basename(path)
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                total_pages += 1
                chunks = chunk_text(page.extract_text() or "")
                if not chunks:
                    continue
                vectors = list(model.embed(chunks))
                points = []
                for chunk, vec in zip(chunks, vectors):
                    points.append(PointStruct(
                        id=point_id,
                        vector=vec.tolist(),
                        payload={"text": chunk, "source": source, "page": page_num},
                    ))
                    point_id += 1
                    total_chunks += 1
                client.upsert(COLLECTION, points=points)
        print(f"Indexat: {source}")

    print(f"Fitxers: {len(paths)} | pàgines: {total_pages} | chunks: {total_chunks}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Executar per veure'ls passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_ingest.py -v`
Expected: PASS (3 tests). (Importar `ingest_pdf` és segur: la lògica d'ingesta viu sota `if __name__ == "__main__":` i no s'executa.)

- [ ] **Step 5: Commit**

```bash
git add backend/ingest_pdf.py backend/test_ingest.py
git commit -m "feat(backend): ingest_pdf.py — chunking + indexat a Qdrant"
```

> Nota: la ingesta real (executar `python ingest_pdf.py` amb els PDFs a `backend/pdfs/` i el `.env`) és una verificació manual posterior, no part dels tests.

---

### Task 5: Frontend — xat ancorat "📚 Gramàtica" (prefix PDF:)

**Files:**
- Modify: `frontend/chat-app/src/app/chat/ai-protocol.ts`
- Modify: `frontend/chat-app/src/app/chat/chat.ts`
- Modify: `frontend/chat-app/src/app/chat/chat.html`
- Modify: `frontend/chat-app/src/app/chat/chat.scss`

**Interfaces:**
- Consumes: `parseAiPayload`, `Message`, backend `PDF:` (Task 3).
- Produces: `PDF_CHAT` exportat; `pdfChat`/`activePdf`/`pdfTyping`; `selectPdf`; `handlePdfMessage`; branca `isPdf` a `active()`.

- [ ] **Step 1: Constant** — a `ai-protocol.ts`, afegir sota `export const AI_ROOM = ...`:

```typescript
export const PDF_CHAT = '📚 Gramàtica';
```

- [ ] **Step 2: Import al component** — a `chat.ts`, afegir `PDF_CHAT` a la importació de `./ai-protocol` (junt amb `AI_ROOM, AiUsage, parseAiPayload, YUKI_NAME`):

```typescript
import { AI_ROOM, AiUsage, parseAiPayload, YUKI_NAME, PDF_CHAT } from './ai-protocol';
```

- [ ] **Step 3: Estat del xat de gramàtica** — a `chat.ts`, just després del bloc `readonly aiTyping = signal(false);`:

```typescript
  readonly pdfChat = {
    name: PDF_CHAT,
    messages: signal<Message[]>([]),
    lastMessage: signal('')
  };
  readonly activePdf = signal(false);
  readonly pdfTyping = signal(false);
```

- [ ] **Step 4: Track del typing PDF a l'efecte d'auto-scroll** — a `chat.ts`, dins l'`effect(...)` del constructor, afegir la línia de track just després de `this.aiTyping();`:

```typescript
      this.pdfTyping();                 // track l'indicador de gramàtica
```

- [ ] **Step 5: Branca `isPdf` al computed `active`** — a `chat.ts`, dins `active`, afegir aquesta branca **just després** de la branca `if (this.activeAi()) { ... }`:

```typescript
    if (this.activePdf()) {
      return {
        title: this.pdfChat.name,
        subtitle: this.pdfTyping() ? 'consultant els llibres…' : 'gramàtica espanyola ✦',
        initials: '📚',
        online: true,
        isRoom: false,
        isAi: false,
        isPdf: true,
        messages: this.pdfChat.messages,
      };
    }
```

I afegir `isPdf: false,` als **altres tres** objectes retornats de `active` (la branca AI, la de contacte i la de room), just al costat del seu `isAi:`, perquè el tipus del `computed` sigui consistent.

- [ ] **Step 6: Routing de `PDF:`** — a `chat.ts`, dins `this.socket.onmessage`, just després del bloc `if (data.startsWith('DIRECTAI:')) { ... }`:

```typescript
      if (data.startsWith('PDF:')) {
        this.handlePdfMessage(data.slice('PDF:'.length));
        return;
      }
```

- [ ] **Step 7: Mètode `handlePdfMessage`** — a `chat.ts`, just després de `handleAiMessage`:

```typescript
  private handlePdfMessage(json: string) {
    this.pdfTyping.set(false);

    let payload;
    try {
      payload = parseAiPayload(json);
    } catch {
      console.warn('Invalid PDF payload', json);
      return;
    }

    this.pdfChat.messages.update(msgs => [...msgs, {
      text: payload.text,
      sender: PDF_CHAT,
      time: this.getTime(),
      isMe: false,
      usage: payload.usage ?? undefined
    }]);
    this.pdfChat.lastMessage.set(payload.text);
  }
```

- [ ] **Step 8: `selectPdf` + netejar `activePdf` als altres selectors** — a `chat.ts`, afegir el mètode:

```typescript
  selectPdf() {
    this.activeContact.set(null);
    this.activeRoom.set(null);
    this.activeAi.set(false);
    this.activePdf.set(true);
  }
```

I afegir `this.activePdf.set(false);` com a primera línia de `selectAi`, `selectContact`, `selectRoom` i `closeConversation`.

- [ ] **Step 9: Enviar amb el xat de gramàtica actiu** — a `chat.ts`, dins `sendMessage`, just després del bloc `if (this.activeAi()) { ... }` (i abans de `const room = ...`):

```typescript
    if (this.activePdf()) {
      this.socket.send('PDF:' + text);
      this.pdfChat.messages.update(msgs => [...msgs, {
        text,
        sender: this.myName(),
        time: this.getTime(),
        isMe: true
      }]);
      this.pdfChat.lastMessage.set(text);
      this.pdfTyping.set(true);
      this.newMessage = '';
      return;
    }
```

- [ ] **Step 10: Entrada a la sidebar** — a `chat.html`, just després del `</div>` que tanca l'entrada `<div class="contact ai" ...>` (la de "Yuki, la teva IA") i abans del `@for (contact of contacts(); ...)`:

```html
      <div class="contact pdf" [class.active]="activePdf()" (click)="selectPdf()">
        <div class="avatar pdf">📚</div>
        <div class="contact-info">
          <div class="contact-name">📚 Gramàtica</div>
          <div class="contact-last">{{ pdfChat.lastMessage() || 'pregunta sobre gramàtica ✦' }}</div>
        </div>
      </div>
```

- [ ] **Step 11: Estils de l'avatar/entrada PDF** — al final de `chat.scss`, afegir:

```scss
.avatar.pdf {
  background: #cbe6c0;
  border-color: #6aa84f;
  color: #274d16;
}

.contact.pdf {
  &.active {
    background: #dcefd3;
    border-color: #6aa84f;
  }
}
```

- [ ] **Step 12: Build + tests**

Run (des de `frontend/chat-app/`): `npm run build`
Expected: build OK, sense errors de TypeScript/plantilla (l'avís de budget CSS és acceptable).
Run (des de `frontend/chat-app/`): `npm run test:unit`
Expected: PASS (4 tests).

- [ ] **Step 13: Commit**

```bash
git add frontend/chat-app/src/app/chat/ai-protocol.ts frontend/chat-app/src/app/chat/chat.ts frontend/chat-app/src/app/chat/chat.html frontend/chat-app/src/app/chat/chat.scss
git commit -m "feat(frontend): xat ancorat '📚 Gramàtica' (prefix PDF:)"
```

---

## Verificació manual (extrem a extrem, després de les tasques)

Requereix `QDRANT_URL`, `QDRANT_API_KEY`, `GROQ_API_KEY` al `.env` i els 3 PDFs a `backend/pdfs/`.

1. **Ingesta:** des de `backend/`, `./venv/Scripts/python.exe ingest_pdf.py` → indexa la col·lecció `gramatica` (mostra el resum de pàgines/chunks). Es fa un sol cop.
2. Backend: `./venv/Scripts/python.exe -m uvicorn main:app --reload`.
3. Frontend: `npm start`; obrir `http://localhost:4200`.
4. Obrir "📚 Gramàtica" i preguntar alguna cosa de gramàtica → resposta basada en els llibres, amb la línia de tokens.
5. Preguntar alguna cosa clarament fora dels llibres → la resposta ha de dir que no ho troba als llibres.
