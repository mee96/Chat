# Disseny: RAG "Gramàtica" (PDF + Qdrant)

**Data:** 2026-07-01
**Projecte:** Chat (Angular 21 + FastAPI + WebSocket, desplegat a Render)
**Relacionat:** [[2026-06-29-chat-amb-ia-groq-design]] (patró del xat amb IA / prefix AI:)

## Objectiu

Afegir un xat RAG que respon preguntes sobre la "Gramática descriptiva de la lengua
española" (3 volums, PDFs acadèmics en castellà). Un script offline processa els PDFs i
els indexa a Qdrant; el servidor, en rebre `PDF:<pregunta>`, recupera els fragments més
rellevants i els passa a Groq com a context perquè respongui **només** a partir d'aquests.
El frontend té un xat ancorat "📚 Gramàtica" que usa el prefix `PDF:`.

## Decisió d'embeddings (resolta)

Un únic model a tot arreu via **fastembed** (ONNX, sense torch):
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (dimensió **384**,
distància **cosinus**). La ingesta i la query usen el mateix model → vectors compatibles.
S'ha verificat que fastembed suporta aquest model exacte.

## Dependències

- **`backend/requirements.txt` (Render):** afegir `fastembed` (lleuger). `qdrant-client`
  ja hi és. **Treure `pdfplumber`** d'aquí (el servidor no llegeix PDFs).
- **`backend/requirements-rag.txt` (ingesta local):** `-r requirements.txt` + `pdfplumber`.
  **Eliminar `sentence-transformers`** (fastembed cobreix la ingesta → torch desapareix
  del tot del projecte).
- Fixar `fastembed` a la versió instal·lada al venv.

## Arquitectura

### `backend/ingest_pdf.py` (offline, s'executa un sol cop en local, NO a Render)

- Llegeix els PDFs de `backend/pdfs/` (carpeta gitignorada) — per defecte tots els
  `*.pdf` d'aquella carpeta; opcionalment accepta rutes per `sys.argv`.
- **Extracció:** pdfplumber, text pàgina a pàgina.
- **Chunking:** fragments de ~500 paraules amb ~50 de solapament. Cada chunk guarda
  metadades: `source` (nom del fitxer/volum) i `page` (número de pàgina d'origen).
- **Embeddings:** fastembed amb el model indicat (dim 384).
- **Qdrant:** connecta amb `QDRANT_URL` i `QDRANT_API_KEY` del `.env`. Crea la col·lecció
  **`gramatica`** (vector size 384, distància cosinus) si no existeix. Upsert per lots
  dels punts `{id, vector, payload={text, source, page}}`.
- Imprimeix un resum: nombre de fitxers, pàgines, chunks i vectors indexats.

### `backend/rag.py` (usat pel servidor)

- Client Qdrant i model fastembed a nivell de mòdul, inicialitzats de forma **lazy**
  (una sola vegada), amb `QDRANT_URL`/`QDRANT_API_KEY` del `.env`.
- Constant `COLLECTION = "gramatica"`, `EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"`.
- `search(query: str, top_k: int = 3) -> list[str]`: genera l'embedding de `query` amb
  fastembed, fa una cerca top-k a la col·lecció `gramatica` i retorna el **text** dels
  chunks trobats (llista de strings, en ordre de rellevància). Si no hi ha resultats,
  retorna una llista buida.

### `backend/main.py` — prefix `PDF:`

- `PDF_SYSTEM_PROMPT` (castellà, literal):
  > "Eres un asistente experto en gramática española. Responde ÚNICAMENTE basándote en el
  > contexto proporcionado. Si la pregunta no tiene respuesta en el contexto, di
  > explícitamente que no encuentras esa información en los libros. No inventes información."
- `pdf_histories: dict[str, list[dict]]` a `ConnectionManager`, amb un helper
  `_ensure_pdf_history(username)` que sembra amb `PDF_SYSTEM_PROMPT` (idempotent).
- `handle_pdf_message(username, query)`:
  1. `chunks = rag.search(query)` (top_k=3).
  2. Construeix el contingut del torn de l'usuari:
     `"Contexto:\n" + "\n---\n".join(chunks) + "\n\nPregunta: " + query`
     (si `chunks` és buit, el context queda buit i el system prompt fa que la Yuki digui
     que no ho troba).
  3. Afegeix aquest missatge a l'historial de l'usuari.
  4. `reply, usage = await call_groq(history)`; afegeix la resposta com a `assistant`.
  5. Envia `PDF:` + JSON `{text: reply, usage}`.
  6. En error (Groq o Qdrant): log + envia `PDF:` + `{text: "⚠️ no s'ha pogut consultar els llibres", usage: null}`, sense contaminar l'historial amb una resposta fallida.
- Routing al `websocket_endpoint`: branca `elif data.startswith("PDF:")` →
  `handle_pdf_message(username, data[len("PDF:"):])` (paral·lela a `AI:`).
- `import rag` al capdamunt de main.py. `rag.py` no importa `main` (sense cicles).

### Frontend (`chat.ts` / `chat.html` / `chat.scss` / `ai-protocol.ts`)

- Constant `PDF_CHAT = '📚 Gramàtica'` a `ai-protocol.ts` (nom/títol del xat).
- Objecte `pdfChat` (com `aiChat`: `name`, `messages` signal, `lastMessage`), signals
  `activePdf` i `pdfTyping`. Entrada fixa a la sidebar **sota** "Yuki, la teva IA".
- El `computed` `active` guanya una branca `activePdf()` amb `isPdf: true` (i les altres
  branques afegeixen `isPdf: false` per consistència de tipus). `selectPdf()` activa el
  xat i neteja `activeContact`/`activeRoom`/`activeAi`; els altres selectors posen
  `activePdf(false)`.
- Enviar amb el xat de gramàtica actiu: `socket.send('PDF:' + text)`, pinta el missatge
  propi i activa `pdfTyping`.
- Handler `PDF:` a `onmessage` (abans del fallback de missatge directe): `handlePdfMessage`
  reaprofita `parseAiPayload`, afegeix el missatge amb `usage`, apaga `pdfTyping`.
- La línia de tokens + tooltip kawaii ja s'apliquen a qualsevol `Message` amb `usage`.
- Avatar 📚 a l'entrada de la sidebar i a la capçalera (per `a.isPdf`).

## Convencions (CLAUDE.md)

- Angular 21: `@if`/`@for`, class bindings (no `ngClass`/`ngStyle`), signals `.set`/`.update`
  (no `.mutate`), sense `standalone: true`.
- Backend: `QDRANT_URL`/`QDRANT_API_KEY`/`GROQ_API_KEY` del `.env` (mai al codi).

## Gestió d'errors / edge cases

- Col·lecció buida o `search` sense resultats → context buit → la Yuki respon que no
  troba la informació (comportament desitjat pel system prompt).
- Fallada de Qdrant/fastembed/Groq → payload d'error `PDF:` amb `usage: null`; el frontend
  apaga el "escrivint…" i mostra el text sense línia de tokens.
- La ingesta descarrega el model ONNX de fastembed el primer cop (~un cop, en local).

## Testing

- **Backend (pytest):**
  - `chunk_text(text, size=500, overlap=50)`: funció pura de nivell superior a
    `ingest_pdf.py` (tota la lògica d'execució de la ingesta va sota
    `if __name__ == "__main__":`, perquè el test pugui `import ingest_pdf` sense processar
    cap PDF ni tocar Qdrant). Verificar mida dels chunks i solapament correcte amb un text
    sintètic.
  - `handle_pdf_message` amb `rag.search` i `call_groq` mockejats (monkeypatch): comprova
    que recupera context, que el torn de l'usuari conté "Contexto:" + els chunks + la
    pregunta, que envia `PDF:{json}` amb `usage`, que l'historial creix (system+user+assistant),
    i el camí d'error (`usage: null`, sense torn d'assistant fallit). Cap accés real a Qdrant.
- **Frontend (vitest):** reaprofita el test de `parseAiPayload` (mateix format `{text,usage}`).
- **Manual:** amb els 3 PDFs a `backend/pdfs/` i el `.env` configurat, executar
  `python ingest_pdf.py`; després, al xat, obrir "📚 Gramàtica" i fer preguntes de gramàtica
  → resposta amb tokens; una pregunta fora d'abast → resposta que no ho troba als llibres.

## Fora d'abast (YAGNI)

- Re-ingesta incremental / detecció de canvis al PDF (es re-executa el script sencer).
- Citacions de font a la UI (es guarden `source`/`page` al payload per al futur, però
  `search` retorna només text).
- Deploy de la ingesta a Render (és offline/local per disseny).

## Nota de desplegament

- El servidor a Render només necessita `qdrant-client` + `fastembed` (tots dos lleugers) a
  més de les deps existents; sense torch. Cal que `QDRANT_URL`/`QDRANT_API_KEY` estiguin
  configurades com a variables d'entorn a Render (a més de `GROQ_API_KEY`).
- La col·lecció `gramatica` s'ha d'haver indexat (executant `ingest_pdf.py` en local
  contra la mateixa instància de Qdrant) abans que el `PDF:` funcioni en producció.
