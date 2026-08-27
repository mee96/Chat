<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=a8c4f0&height=180&section=header&text=REAL-TIME%20CHAT&fontColor=1b2e4b&fontSize=34&desc=FastAPI%20%2b%20Angular%2021%20%2b%20WebSockets%20%2b%20AI%20%2b%20RAG&descSize=16&descColor=1b2e4b&descAlignY=65&fontAlignY=42" width="100%" alt="Chat Header" />

<br/>

<div align="center">
<a href="README.md"><img src="https://img.shields.io/badge/English-1b2e4b?style=flat-square" alt="English"></a>
<a href="README.es.md"><img src="https://img.shields.io/badge/Espa%C3%B1ol-a8c4f0?style=flat-square&logoColor=1b2e4b" alt="Español"></a>
<a href="README.ca.md"><img src="https://img.shields.io/badge/Catal%C3%A0-5b9bd5?style=flat-square" alt="Català"></a>
</div>

<br/>

![Angular](https://img.shields.io/badge/Angular-21-a8c4f0?style=for-the-badge&logo=angular&logoColor=1b2e4b)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-5b9bd5?style=for-the-badge&logo=fastapi&logoColor=ffffff)
![Python](https://img.shields.io/badge/Python-3.11-b8e8d4?style=for-the-badge&logo=python&logoColor=1b2e4b)
![Groq](https://img.shields.io/badge/Groq-GPT_OSS_120B-2fb5ae?style=for-the-badge&logoColor=ffffff)
![Qdrant](https://img.shields.io/badge/Qdrant-RAG-f0e4a0?style=for-the-badge&logoColor=1b2e4b)

<br/>

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-a8c4f0?style=flat-square&logoColor=1b2e4b)](https://chat-frontend-o57q.onrender.com)
&nbsp;
[![Backend Render](https://img.shields.io/badge/⚙️_Backend_Render-5b9bd5?style=flat-square&logoColor=ffffff)](https://chat-backend-6g1r.onrender.com)
&nbsp;
[![GitHub Repo](https://img.shields.io/badge/🐙_GitHub_Repo-b8e8d4?style=flat-square&logoColor=1b2e4b)](https://github.com/mee96/Chat)
&nbsp;
[![Keep Alive Active](https://img.shields.io/badge/Keep--Alive-Active-b8e8d4?style=flat-square&logo=githubactions&logoColor=1b2e4b)](https://github.com/mee96/keep-alive)

</div>

<br/>

---

## <img src="https://api.iconify.design/ph/question-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;What is this?

**Real-Time Chat** is a full-stack messaging app with direct conversations, group rooms and an AI assistant, built with an **Angular 21** frontend and a **FastAPI** backend talking over **WebSockets**.

Users join with just a name, see who's online, start private conversations and create group rooms. They can also talk to **Yuki**, a **Groq**-powered AI, and to **Gramàtica**, a Spanish-grammar Q&A chat that only answers from three grammar volumes indexed with **RAG (Qdrant)**. Every message — direct, room or AI — travels over a single WebSocket connection per user.

<br/>

---

## <img src="https://api.iconify.design/ph/stack-fill.svg?color=%232FB5AE&height=24" height="22"> &nbsp;Technology Stack

| Layer | Technology |
| :--- | :--- |
| <img src="https://api.iconify.design/ph/desktop-tower-fill.svg?color=%235B9BD5&height=18" height="16"> **Frontend** | Angular 21 (standalone components, signals, `NgOptimizedImage`), TypeScript |
| <img src="https://api.iconify.design/ph/cpu-fill.svg?color=%232FB5AE&height=18" height="16"> **Backend** | FastAPI, Uvicorn, `websockets` |
| <img src="https://api.iconify.design/ph/robot-fill.svg?color=%235B9BD5&height=18" height="16"> **AI** | Groq (`AsyncGroq`, model `openai/gpt-oss-120b`) |
| <img src="https://api.iconify.design/ph/database-fill.svg?color=%232FB5AE&height=18" height="16"> **RAG** | Qdrant (vector DB) + Qdrant Cloud Inference (embeddings generated server-side — the backend process never loads a model itself) |
| <img src="https://api.iconify.design/ph/plugs-connected-fill.svg?color=%23E0A63B&height=18" height="16"> **Communication** | WebSocket (`/ws/{username}`) |
| <img src="https://api.iconify.design/ph/rocket-launch-fill.svg?color=%235B9BD5&height=18" height="16"> **Deploy** | Render (frontend as Static Site, backend as Web Service) |

<br/>

---

## <img src="https://api.iconify.design/ph/arrows-left-right-bold.svg?color=%235B9BD5&height=24" height="22"> &nbsp;WebSocket Protocol

Messages are plain text with prefixes. AI replies carry a JSON body `{text, usage}`, where `usage` is `{prompt_tokens, completion_tokens, total_tokens}` or `null` when it doesn't apply.

### <img src="https://api.iconify.design/ph/arrow-up-fill.svg?color=%232FB5AE&height=20" height="18"> Client → Server
<pre><code>receiver:text                     → Direct message to another user
JOIN:room:member1,member2         → Create / join a room
ROOM:room:text                    → Message to a room
AI:text                           → Message to Yuki's dedicated chat
PDF:text                          → Question to the grammar chat (RAG)</code></pre>

### <img src="https://api.iconify.design/ph/arrow-down-fill.svg?color=%23E0A63B&height=20" height="18"> Server → Client
<pre><code>SYSTEM:users:user1,user2          → Connected user list
SYSTEM:error:...                  → Error (e.g. room limit reached)
JOIN:room:member1,member2         → Room membership confirmation
ROOM:room:sender:text             → Incoming room message
AI:{json}                         → Yuki's reply (dedicated chat)
DIRECTAI:contact:{json}           → Yuki's reply in a 1-to-1 chat (via `@yuki`)
ROOMAI:room:{json}                → Yuki's reply in a room (via `@yuki`)
PDF:{json}                        → Grammar chat reply</code></pre>

> **`@yuki` in any conversation:** in 1-to-1 chats and rooms, Yuki only replies when a message contains `@yuki`. In her dedicated *"Yuki, la teva IA"* chat, she replies to every message without needing a mention.

<br/>

---

## <img src="https://api.iconify.design/ph/folder-fill.svg?color=%232FB5AE&height=24" height="22"> &nbsp;Project Structure

<pre><code>Chat/
├── 🐍 backend/
│   ├── main.py                 → FastAPI app: WebSocket, ConnectionManager, Yuki, RAG
│   ├── rag.py                  → Retrieval: embeddings (Qdrant Cloud Inference) + Qdrant search
│   ├── ingest_pdf.py           → OFFLINE ingestion of the PDFs into Qdrant (not run on Render)
│   ├── requirements.txt        → Server dependencies
│   ├── requirements-rag.txt    → Extra dependency for local ingestion only (pdfplumber)
│   ├── test_*.py               → Tests (pytest): Yuki, rooms, RAG, ingestion, grammar chat
│   ├── pdfs/                   → Source PDFs for ingestion (gitignored)
│   ├── .env                    → Keys: GROQ/QDRANT (gitignored)
│   └── venv/                   → Python virtual environment (gitignored)
│
└── 🅰️ frontend/
    └── chat-app/                → Angular project
        ├── src/app/
        │   ├── login/           → Entry screen (choose a username)
        │   ├── chat/            → Main chat view
        │   │   ├── chat.ts/.html/.scss   → Contacts, rooms, Yuki, Gramàtica, responsive layout
        │   │   ├── ai-protocol.ts        → Parses AI payloads (text + tokens)
        │   │   ├── ws-url.ts             → Resolves the backend (local vs Render)
        │   │   └── tooltip.directive.ts  → Tooltip for token counts
        │   ├── app.ts           → Root component
        │   └── app.config.ts
        ├── angular.json
        └── package.json</code></pre>

The backend keeps in **memory**:

* `connections`: a `username → WebSocket` map of connected users.
* `rooms`: a `room_name → [members]` map, capped at **3 rooms per user** (`MAX_ROOMS_PER_USER`).
* AI conversation histories (each seeded with its system prompt):
  * `ai_histories` — Yuki's dedicated chat, **per user**.
  * `direct_ai_histories` — `@yuki` mentions in 1-to-1 chats, **per pair**.
  * `room_ai_histories` — `@yuki` mentions in rooms, **per room**.
  * `pdf_histories` — the grammar chat (RAG), **per user**.

<br/>

---

## <img src="https://api.iconify.design/ph/play-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Run Locally

You'll need **Python 3.11+** and **Node.js 20+** (with npm).

### 1. Backend (FastAPI)

<pre><code>cd backend

# Create and activate the virtual environment
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install server dependencies
pip install -r requirements.txt

# Create backend/.env with your keys (see "Environment Variables")
# Start the server (port 8000)
uvicorn main:app --reload</code></pre>

The backend will be available at `http://localhost:8000` and the WebSocket at `ws://localhost:8000/ws/{username}`.

> ⚡ **Availability:** the production backend on Render stays active without *cold starts*, thanks to automatic pings from [Keep-Alive](https://github.com/mee96/keep-alive).

> The backend's CORS allows `http://localhost:4200` (Angular's dev server) by default.

### 2. Frontend (Angular)

<pre><code>cd frontend/chat-app

# Install dependencies
npm install

# Start the dev server (port 4200)
npm start</code></pre>

Open `http://localhost:4200` in your browser. ✨

> **WebSocket URL:** [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts) resolves it automatically — served from `localhost`/`127.0.0.1`, it points to `ws://localhost:8000`; from any other domain, to the Render backend (`wss://chat-backend-6g1r.onrender.com`). Nothing to edit for local development.

<br/>

---

## <img src="https://api.iconify.design/ph/sliders-horizontal-fill.svg?color=%23E0A63B&height=24" height="22"> &nbsp;Environment Variables

The backend reads `backend/.env` (via `python-dotenv`). Variables already set in the environment (e.g. on Render) take priority. On **Render**, configure them in the service's panel.

| Variable | Needed for | Description |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Yuki (AI) | Groq API key. |
| `QDRANT_URL` | Grammar chat | URL of the Qdrant cluster. |
| `QDRANT_API_KEY` | Grammar chat | Qdrant API key. |
| `QDRANT_TIMEOUT` | *(optional)* | Qdrant client timeout in seconds (defaults to `120`). |

`backend/.env` is in `.gitignore`: it is **not** pushed to the repository.

<br/>

---

## <img src="https://api.iconify.design/ph/book-open-text-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;PDF Ingestion (RAG)

The **Gramàtica** chat answers solely from three volumes of *Gramática descriptiva de la lengua española* (volumes 1, 2 and 3), chunked and indexed in Qdrant. Ingestion runs **once, locally** (not on Render): it uploads the chunks to Qdrant, which generates the vectors server-side (Cloud Inference).

* **Embedding model:** `intfloat/multilingual-e5-small` (384 dims, cosine distance), via **Qdrant Cloud Inference** — the backend process never loads a model locally, avoiding the OOM crashes that a locally-loaded model caused on Render's free tier (512Mi). As an E5-family model, the `"query: "`/`"passage: "` prefixes it expects are added manually (Qdrant Cloud Inference doesn't apply them automatically yet).
* **Collection:** `gramatica`.
* **Chunking:** ~500 words per chunk with 50 words of overlap. Bibliography/reference pages are skipped — they never contain grammar explanations and can otherwise outrank real content in the retrieval.

Steps:

<pre><code>cd backend
# (with the venv activated and backend/.env configured)

# Extra dependency, only needed to read the PDFs
pip install -r requirements-rag.txt

# Place the PDFs in backend/pdfs/ and launch the ingestion
python ingest_pdf.py
# or specific paths: python ingest_pdf.py path/to/volume1.pdf path/to/volume2.pdf</code></pre>

Ingestion is **resumable**: it uses deterministic (idempotent) IDs and skips pages already indexed, so if it's interrupted (network timeout, etc.) simply re-running it picks up where it left off. Upserts retry automatically with backoff on transient errors.

<br/>

---

## <img src="https://api.iconify.design/ph/cloud-arrow-up-fill.svg?color=%232FB5AE&height=24" height="22"> &nbsp;Deployment & High Availability

The project deploys as two independent services on Render.

### Backend — Web Service

1. In the Render dashboard: **New → Web Service** and connect the repository.
2. Configuration:
   * **Root Directory:** `backend`
   * **Runtime:** Python 3
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Under **Environment**, add `GROQ_API_KEY`, `QDRANT_URL` and `QDRANT_API_KEY` (see "Environment Variables").

> Render does **not** run the ingestion: `pdfplumber` (PDF reading) lives in `requirements-rag.txt`, installed locally only. The `gramatica` collection must already be indexed in Qdrant. Since embeddings are generated server-side by Qdrant Cloud Inference, the backend itself never loads an embedding model — nothing to download or cache during the build.

Render serves the service over HTTPS, so the WebSocket connects via `wss://`.

### Frontend — Static Site

1. **New → Static Site** and connect the same repository.
2. Configuration:
   * **Root Directory:** `frontend/chat-app`
   * **Build Command:** `npm install && npm run build`
   * **Publish Directory:** `dist/chat-app/browser`
3. The backend URL resolves itself in [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts); if the backend's domain changes, update `PROD_WS_BASE` there.

> ⚡ **No Cold Starts:** the backend on Render is kept constantly warm thanks to an automation bot running on GitHub Actions in my centralized [**keep-alive**](https://github.com/mee96/keep-alive) repository, which sends periodic pings to the relevant endpoints.

<br/>

---

## <img src="https://api.iconify.design/ph/sparkle-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Key Features

* <img src="https://api.iconify.design/ph/user-fill.svg?color=%235B9BD5&height=18" height="16"> **Username-only entry** — no password; each user opens their own WebSocket connection.
* <img src="https://api.iconify.design/ph/users-fill.svg?color=%232FB5AE&height=18" height="16"> **Live user list** — updates dynamically as users connect and disconnect.
* <img src="https://api.iconify.design/ph/chat-circle-dots-fill.svg?color=%23E0A63B&height=18" height="16"> **Direct messaging** — private 1-to-1 chat between connected users.
* <img src="https://api.iconify.design/ph/users-three-fill.svg?color=%235B9BD5&height=18" height="16"> **Group rooms** — create a named group by picking several users; messages broadcast to every member.
* <img src="https://api.iconify.design/ph/hash-fill.svg?color=%232FB5AE&height=18" height="16"> **Room limit** — a maximum of 3 rooms per user, enforced server-side.
* <img src="https://api.iconify.design/ph/arrows-clockwise-fill.svg?color=%23E0A63B&height=18" height="16"> **Room re-sync** — on reconnect, a user recovers every room they belong to.
* <img src="https://api.iconify.design/ph/robot-fill.svg?color=%235B9BD5&height=18" height="16"> **Yuki, the chat's AI** — a Groq-powered assistant (`openai/gpt-oss-120b`) that replies in the user's own language and keeps a **per-user history**. Every reply shows its **token usage**, with a hover **tooltip** (prompt · completion · total).
* <img src="https://api.iconify.design/ph/at-fill.svg?color=%232FB5AE&height=18" height="16"> **`@yuki` anywhere** — mention `@yuki` in a 1-to-1 chat or a room and she replies right there, visible to everyone in it; she also has her own dedicated chat.
* <img src="https://api.iconify.design/ph/book-open-text-fill.svg?color=%23E0A63B&height=18" height="16"> **Grammar Chat (RAG)** — the *"Gramàtica"* chat answers **only** from the three grammar volumes indexed in Qdrant; if a question falls outside that context, it says so instead of making something up.
* <img src="https://api.iconify.design/ph/device-mobile-fill.svg?color=%235B9BD5&height=18" height="16"> **Responsive design (mobile)** — a Messenger/WhatsApp-style pattern: on narrow screens (≤ 768px) the chat list shows first, and opening a conversation takes over the full screen with a "back" button.
* <img src="https://api.iconify.design/ph/lightning-fill.svg?color=%232FB5AE&height=18" height="16"> **Reactive UI with signals** — Angular 21 with standalone components and signal-based state.

<br/>

---

## <img src="https://api.iconify.design/ph/warning-circle-fill.svg?color=%23E0A63B&height=24" height="22"> &nbsp;Known Limitations

* State (users, rooms and **AI histories**) is kept **in memory**: it's lost on every backend restart.
* No message-history persistence and no database beyond the grammar vectors in Qdrant.
* Authentication is nominal (username only, no verification).
* The grammar chat depends on a **prior ingestion** of the PDFs into Qdrant (a manual, local step) and on `GROQ_API_KEY`/`QDRANT_URL`/`QDRANT_API_KEY` being configured.
* Groq/Qdrant's free tiers can impose **rate limits** (slower replies or retries).
* The production backend's domain is hardcoded as a constant in [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts) (`PROD_WS_BASE`).

<br/>

---

<div align="center">

Developed by **Carme Medina Canalda**
*Full Stack Developer · Barcelona*

<br/>

[![LinkedIn](https://img.shields.io/badge/LinkedIn-a8c4f0?style=flat-square&logo=linkedin&logoColor=1b2e4b)](https://www.linkedin.com/in/carme-medina-canalda-250457132/)
[![Portfolio](https://img.shields.io/badge/Portfolio-5b9bd5?style=flat-square&logoColor=ffffff)](https://carme-portfoli.onrender.com/)

</div>
