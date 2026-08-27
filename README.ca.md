<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=a8c4f0&height=180&section=header&text=XAT%20EN%20TEMPS%20REAL&fontColor=1b2e4b&fontSize=34&desc=FastAPI%20%2b%20Angular%2021%20%2b%20WebSockets%20%2b%20AI%20%2b%20RAG&descSize=16&descColor=1b2e4b&descAlignY=65&fontAlignY=42" width="100%" alt="Chat Header" />

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

[![Demo en directe](https://img.shields.io/badge/🌐_Demo_en_directe-a8c4f0?style=flat-square&logoColor=1b2e4b)](https://chat-frontend-o57q.onrender.com)
&nbsp;
[![Backend Render](https://img.shields.io/badge/⚙️_Backend_Render-5b9bd5?style=flat-square&logoColor=ffffff)](https://chat-backend-6g1r.onrender.com)
&nbsp;
[![GitHub Repo](https://img.shields.io/badge/🐙_GitHub_Repo-b8e8d4?style=flat-square&logoColor=1b2e4b)](https://github.com/mee96/Chat)
&nbsp;
[![Keep Alive Active](https://img.shields.io/badge/Keep--Alive-Active-b8e8d4?style=flat-square&logo=githubactions&logoColor=1b2e4b)](https://github.com/mee96/keep-alive)

</div>

<br/>

---

## <img src="https://api.iconify.design/ph/question-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Què és això?

**Xat en Temps Real** és una aplicació de missatgeria full-stack amb converses directes, sales de grup i un assistent d'IA, construïda amb un frontend en **Angular 21** i un backend en **FastAPI** comunicats mitjançant **WebSockets**.

Els usuaris entren només amb un nom, veuen qui està connectat, inicien converses privades i creen sales de grup. A més poden parlar amb la **Yuki**, una IA basada en **Groq**, i amb **Gramàtica**, un xat de preguntes i respostes sobre gramàtica espanyola que respon únicament a partir de tres toms de gramàtica indexats amb **RAG (Qdrant)**. Tota la missatgeria —directa, de sala o d'IA— circula per una única connexió WebSocket per usuari.

<br/>

---

## <img src="https://api.iconify.design/ph/stack-fill.svg?color=%232FB5AE&height=24" height="22"> &nbsp;Stack Tecnològic

| Capa | Tecnologia |
| :--- | :--- |
| <img src="https://api.iconify.design/ph/desktop-tower-fill.svg?color=%235B9BD5&height=18" height="16"> **Frontend** | Angular 21 (components standalone, signals, `NgOptimizedImage`), TypeScript |
| <img src="https://api.iconify.design/ph/cpu-fill.svg?color=%232FB5AE&height=18" height="16"> **Backend** | FastAPI, Uvicorn, `websockets` |
| <img src="https://api.iconify.design/ph/robot-fill.svg?color=%235B9BD5&height=18" height="16"> **IA** | Groq (`AsyncGroq`, model `openai/gpt-oss-120b`) |
| <img src="https://api.iconify.design/ph/database-fill.svg?color=%232FB5AE&height=18" height="16"> **RAG** | Qdrant (vector DB) + Qdrant Cloud Inference (embeddings generats al servidor — el backend mai carrega cap model en local) |
| <img src="https://api.iconify.design/ph/plugs-connected-fill.svg?color=%23E0A63B&height=18" height="16"> **Comunicació** | WebSocket (`/ws/{username}`) |
| <img src="https://api.iconify.design/ph/rocket-launch-fill.svg?color=%235B9BD5&height=18" height="16"> **Deploy** | Render (frontend com a Static Site, backend com a Web Service) |

<br/>

---

## <img src="https://api.iconify.design/ph/arrows-left-right-bold.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Protocol WebSocket

Els missatges són text pla amb prefixos. Les respostes d'IA porten un cos JSON `{text, usage}`, on `usage` és `{prompt_tokens, completion_tokens, total_tokens}` o `null` si no aplica.

### <img src="https://api.iconify.design/ph/arrow-up-fill.svg?color=%232FB5AE&height=20" height="18"> Client → Servidor
<pre><code>receptor:text                     → Missatge directe a un altre usuari
JOIN:sala:membre1,membre2         → Crear / unir-se a una sala
ROOM:sala:text                    → Missatge a una sala
AI:text                           → Missatge al xat dedicat de la Yuki
PDF:text                          → Pregunta al xat de gramàtica (RAG)</code></pre>

### <img src="https://api.iconify.design/ph/arrow-down-fill.svg?color=%23E0A63B&height=20" height="18"> Servidor → Client
<pre><code>SYSTEM:users:usuari1,usuari2      → Llista d'usuaris connectats
SYSTEM:error:...                  → Error (p. ex. límit de sales assolit)
JOIN:sala:membre1,membre2         → Confirmació de membresia de sala
ROOM:sala:emissor:text            → Missatge entrant d'una sala
AI:{json}                         → Resposta de la Yuki (xat dedicat)
DIRECTAI:contacte:{json}          → Resposta de la Yuki en un xat 1 a 1 (via `@yuki`)
ROOMAI:sala:{json}                → Resposta de la Yuki en una sala (via `@yuki`)
PDF:{json}                        → Resposta del xat de gramàtica</code></pre>

> **`@yuki` a qualsevol conversa:** als xats 1 a 1 i a les sales, la Yuki només respon quan el missatge conté `@yuki`. Al seu xat dedicat *"Yuki, la teva IA"* respon a tots els missatges sense necessitat de mencionar-la.

<br/>

---

## <img src="https://api.iconify.design/ph/folder-fill.svg?color=%232FB5AE&height=24" height="22"> &nbsp;Estructura del Projecte

<pre><code>Chat/
├── 🐍 backend/
│   ├── main.py                 → App FastAPI: WebSocket, ConnectionManager, Yuki, RAG
│   ├── rag.py                  → Recuperació: embeddings (Qdrant Cloud Inference) + cerca a Qdrant
│   ├── ingest_pdf.py           → Ingesta OFFLINE dels PDFs a Qdrant (no s'executa a Render)
│   ├── requirements.txt        → Dependències del servidor
│   ├── requirements-rag.txt    → Extra només per a la ingesta local (pdfplumber)
│   ├── test_*.py               → Tests (pytest): Yuki, sales, RAG, ingesta, xat de gramàtica
│   ├── pdfs/                   → PDFs font de la ingesta (ignorat a git)
│   ├── .env                    → Claus: GROQ/QDRANT (ignorat a git)
│   └── venv/                   → Entorn virtual de Python (ignorat a git)
│
└── 🅰️ frontend/
    └── chat-app/                → Projecte Angular
        ├── src/app/
        │   ├── login/           → Pantalla d'entrada (triar nom d'usuari)
        │   ├── chat/            → Vista principal del xat
        │   │   ├── chat.ts/.html/.scss   → Contactes, sales, Yuki, Gramàtica, responsive
        │   │   ├── ai-protocol.ts        → Parseig dels payloads d'IA (text + tokens)
        │   │   ├── ws-url.ts             → Resol el backend (local vs Render)
        │   │   └── tooltip.directive.ts  → Tooltip pels tokens
        │   ├── app.ts           → Component arrel
        │   └── app.config.ts
        ├── angular.json
        └── package.json</code></pre>

El backend manté **en memòria**:

* `connections`: mapa `username → WebSocket` dels usuaris connectats.
* `rooms`: mapa `nom_sala → [membres]`, amb un límit de **3 sales per usuari** (`MAX_ROOMS_PER_USER`).
* Historials de conversa amb la IA (tots amb el seu *system prompt* inicial):
  * `ai_histories` — xat dedicat amb la Yuki, **per usuari**.
  * `direct_ai_histories` — mencions `@yuki` en xats 1 a 1, **per parella**.
  * `room_ai_histories` — mencions `@yuki` en sales, **per sala**.
  * `pdf_histories` — xat de gramàtica (RAG), **per usuari**.

<br/>

---

## <img src="https://api.iconify.design/ph/play-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Executar en Local

Calen **Python 3.11+** i **Node.js 20+** (amb npm).

### 1. Backend (FastAPI)

<pre><code>cd backend

# Crear i activar l'entorn virtual
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Instal·lar dependències del servidor
pip install -r requirements.txt

# Crear backend/.env amb les claus (veure "Variables d'Entorn")
# Arrencar el servidor (port 8000)
uvicorn main:app --reload</code></pre>

El backend quedarà disponible a `http://localhost:8000` i el WebSocket a `ws://localhost:8000/ws/{username}`.

> ⚡ **Disponibilitat:** el backend de producció a Render es manté actiu sense *cold starts*, gràcies a pings automàtics de [Keep-Alive](https://github.com/mee96/keep-alive).

> El CORS del backend permet per defecte l'origen `http://localhost:4200` (el dev server d'Angular).

### 2. Frontend (Angular)

<pre><code>cd frontend/chat-app

# Instal·lar dependències
npm install

# Arrencar el dev server (port 4200)
npm start</code></pre>

Obre `http://localhost:4200` al navegador. ✨

> **URL del WebSocket:** [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts) la resol automàticament — si la pàgina es serveix des de `localhost`/`127.0.0.1` apunta a `ws://localhost:8000`; en qualsevol altre domini, al backend de Render (`wss://chat-backend-6g1r.onrender.com`). No cal editar res per al desenvolupament local.

<br/>

---

## <img src="https://api.iconify.design/ph/sliders-horizontal-fill.svg?color=%23E0A63B&height=24" height="22"> &nbsp;Variables d'Entorn

El backend llegeix `backend/.env` (via `python-dotenv`). Les variables ja definides a l'entorn (p. ex. a Render) tenen prioritat. A **Render** cal configurar-les al panell del servei.

| Variable | Necessària per a | Descripció |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Yuki (IA) | Clau de l'API de Groq. |
| `QDRANT_URL` | Xat de gramàtica | URL del clúster de Qdrant. |
| `QDRANT_API_KEY` | Xat de gramàtica | Clau de l'API de Qdrant. |
| `QDRANT_TIMEOUT` | *(opcional)* | Timeout del client Qdrant en segons (per defecte `120`). |

`backend/.env` és a `.gitignore`: **no** es puja al repositori.

<br/>

---

## <img src="https://api.iconify.design/ph/book-open-text-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Ingesta dels PDFs (RAG)

El xat **Gramàtica** respon només a partir de tres toms de *Gramática descriptiva de la lengua española* (volums 1, 2 i 3), trossejats i indexats a Qdrant. La ingesta s'executa **un cop en local** (no a Render): puja els fragments a Qdrant, que genera els vectors al servidor (Cloud Inference).

* **Model d'embeddings:** `intfloat/multilingual-e5-small` (384 dims, distància cosinus), via **Qdrant Cloud Inference** — el backend mai carrega cap model en local, evitant els errors de memòria que provocava un model carregat en local al pla gratuït de Render (512Mi). En pertànyer a la família E5, els prefixos `"query: "`/`"passage: "` que necessita s'afegeixen manualment (Qdrant Cloud Inference encara no els aplica automàticament).
* **Col·lecció:** `gramatica`.
* **Trossejat:** ~500 paraules per fragment amb 50 de solapament. Es descarten les pàgines de bibliografia/referències: mai contenen explicacions de gramàtica i, si no es filtren, poden puntuar més alt que el contingut real a la cerca.

Passos:

<pre><code>cd backend
# (amb el venv activat i backend/.env configurat)

# Dependència extra, només necessària per llegir els PDFs
pip install -r requirements-rag.txt

# Col·loca els PDFs a backend/pdfs/ i llança la ingesta
python ingest_pdf.py
# o rutes concretes: python ingest_pdf.py ruta/al/tom1.pdf ruta/al/tom2.pdf</code></pre>

La ingesta és **represa**: fa servir IDs deterministes (idempotents) i salta les pàgines ja indexades, així que si es talla (timeout de xarxa, etc.) només cal tornar a executar-la i continua on s'havia quedat. Els *upserts* reintenten automàticament amb *backoff* davant errors transitoris.

<br/>

---

## <img src="https://api.iconify.design/ph/cloud-arrow-up-fill.svg?color=%232FB5AE&height=24" height="22"> &nbsp;Desplegament i Alta Disponibilitat

El projecte es desplega com a dos serveis independents a Render.

### Backend — Web Service

1. Al panell de Render: **New → Web Service** i connecta el repositori.
2. Configuració:
   * **Root Directory:** `backend`
   * **Runtime:** Python 3
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. A **Environment**, afegeix `GROQ_API_KEY`, `QDRANT_URL` i `QDRANT_API_KEY` (veure "Variables d'Entorn").

> Render **no** executa la ingesta: `pdfplumber` (lectura de PDFs) queda a `requirements-rag.txt`, que només s'instal·la en local. La col·lecció `gramatica` ha d'estar ja indexada a Qdrant. Com que els embeddings es generen al servidor amb Qdrant Cloud Inference, el backend mai carrega cap model d'embeddings: res a descarregar ni cachejar durant el build.

Render exposa el servei sobre HTTPS, per la qual cosa el WebSocket es connecta via `wss://`.

### Frontend — Static Site

1. **New → Static Site** i connecta el mateix repositori.
2. Configuració:
   * **Root Directory:** `frontend/chat-app`
   * **Build Command:** `npm install && npm run build`
   * **Publish Directory:** `dist/chat-app/browser`
3. La URL del backend es resol sola a [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts); si canvia el domini del backend, actualitza `PROD_WS_BASE` allà.

> ⚡ **Sense Cold Starts:** el backend a Render es manté constantment en calent gràcies a un bot d'automatització via GitHub Actions configurat al meu repositori centralitzat [**keep-alive**](https://github.com/mee96/keep-alive), que envia pings periòdics als endpoints corresponents.

<br/>

---

## <img src="https://api.iconify.design/ph/sparkle-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Funcionalitats Principals

* <img src="https://api.iconify.design/ph/user-fill.svg?color=%235B9BD5&height=18" height="16"> **Entrada per nom d'usuari** — sense contrasenya; cada usuari obre la seva pròpia connexió WebSocket.
* <img src="https://api.iconify.design/ph/users-fill.svg?color=%232FB5AE&height=18" height="16"> **Llista d'usuaris en línia** — actualitzada dinàmicament en connectar-se o desconnectar-se.
* <img src="https://api.iconify.design/ph/chat-circle-dots-fill.svg?color=%23E0A63B&height=18" height="16"> **Missatgeria directa** — xat privat 1 a 1 entre usuaris connectats.
* <img src="https://api.iconify.design/ph/users-three-fill.svg?color=%235B9BD5&height=18" height="16"> **Sales de grup** — crear grups amb nom seleccionant diversos usuaris; missatges difosos a tots els membres.
* <img src="https://api.iconify.design/ph/hash-fill.svg?color=%232FB5AE&height=18" height="16"> **Límit de sales** — màxim de 3 sales per usuari, controlat pel servidor.
* <img src="https://api.iconify.design/ph/arrows-clockwise-fill.svg?color=%23E0A63B&height=18" height="16"> **Re-sincronització de sales** — en reconnectar, l'usuari recupera les sales a què pertany.
* <img src="https://api.iconify.design/ph/robot-fill.svg?color=%235B9BD5&height=18" height="16"> **Yuki, la IA del xat** — assistent basat en Groq (`openai/gpt-oss-120b`), que respon en l'idioma de l'usuari i manté **historial per usuari**. Cada resposta mostra els **tokens** consumits, amb un **tooltip** en passar-hi per sobre (prompt · resposta · total).
* <img src="https://api.iconify.design/ph/at-fill.svg?color=%232FB5AE&height=18" height="16"> **`@yuki` a totes les converses** — menciona-la en un xat 1 a 1 o en una sala i respon allà mateix, visible per a tots els participants; a més té el seu propi xat dedicat.
* <img src="https://api.iconify.design/ph/book-open-text-fill.svg?color=%23E0A63B&height=18" height="16"> **Xat de Gramàtica (RAG)** — el xat *"Gramàtica"* respon **només** amb el contingut dels tres toms indexats a Qdrant; si la pregunta surt del context, ho diu en comptes d'inventar-se res.
* <img src="https://api.iconify.design/ph/device-mobile-fill.svg?color=%235B9BD5&height=18" height="16"> **Disseny responsive (mòbil)** — patró tipus Messenger/WhatsApp: en pantalles estretes (≤ 768px) es veu primer la llista de xats i, en obrir una conversa, aquesta ocupa tota la pantalla amb un botó d'"enrere".
* <img src="https://api.iconify.design/ph/lightning-fill.svg?color=%232FB5AE&height=18" height="16"> **UI reactiva amb signals** — Angular 21 amb components standalone i estat basat en signals.

<br/>

---

## <img src="https://api.iconify.design/ph/warning-circle-fill.svg?color=%23E0A63B&height=24" height="22"> &nbsp;Limitacions Conegudes

* L'estat (usuaris, sales i **historials d'IA**) es desa **en memòria**: es perd en reiniciar el backend.
* No hi ha persistència de l'historial de missatges ni base de dades, més enllà dels vectors de gramàtica a Qdrant.
* L'autenticació és nominal (només nom d'usuari, sense verificació).
* El xat de gramàtica depèn d'una **ingesta prèvia** dels PDFs a Qdrant (pas manual en local) i que `GROQ_API_KEY`/`QDRANT_URL`/`QDRANT_API_KEY` estiguin configurades.
* Amb la capa gratuïta de Groq/Qdrant hi pot haver **límits de taxa** (respostes més lentes o reintents).
* El domini del backend de producció està fixat com a constant a [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts) (`PROD_WS_BASE`).

<br/>

---

<div align="center">

Desenvolupat per **Carme Medina Canalda**
*Full Stack Developer · Barcelona*

<br/>

[![LinkedIn](https://img.shields.io/badge/LinkedIn-a8c4f0?style=flat-square&logo=linkedin&logoColor=1b2e4b)](https://www.linkedin.com/in/carme-medina-canalda-250457132/)
[![Portfolio](https://img.shields.io/badge/Portfolio-5b9bd5?style=flat-square&logoColor=ffffff)](https://carme-portfoli.onrender.com/)

</div>
