<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=a8c4f0&height=180&section=header&text=CHAT%20EN%20TIEMPO%20REAL&fontColor=1b2e4b&fontSize=32&desc=FastAPI%20%2b%20Angular%2021%20%2b%20WebSockets%20%2b%20%20AI%20%2b%20RAG&descSize=15&descColor=1b2e4b&descAlignY=65&fontAlignY=42" width="100%" alt="Chat Header" />

<br/>

![Angular](https://img.shields.io/badge/Angular-21-a8c4f0?style=for-the-badge&logo=angular&logoColor=1b2e4b)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-5b9bd5?style=for-the-badge&logo=fastapi&logoColor=ffffff)
![Python](https://img.shields.io/badge/Python-3.11-b8e8d4?style=for-the-badge&logo=python&logoColor=1b2e4b)
![Groq](https://img.shields.io/badge/Groq-Llama_3.1-2fb5ae?style=for-the-badge&logoColor=ffffff)
![Qdrant](https://img.shields.io/badge/Qdrant-RAG-f0e4a0?style=for-the-badge&logoColor=1b2e4b)

<br/>

[![Demo en vivo](https://img.shields.io/badge/Demo_en_vivo-a8c4f0?style=flat-square&logoColor=1b2e4b)](https://chat-frontend-o57q.onrender.com)
&nbsp;
[![Backend Render](https://img.shields.io/badge/Backend_Render-5b9bd5?style=flat-square&logoColor=ffffff)](https://chat-backend-6g1r.onrender.com)
&nbsp;
[![GitHub Repo](https://img.shields.io/badge/GitHub_Repo-b8e8d4?style=flat-square&logoColor=1b2e4b)](https://github.com/mee96/Chat)

</div>

<br/>

---

## <img src="https://api.iconify.design/ph/chats-teardrop-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;¿Qué es esto?

Aplicación de chat en tiempo real con mensajería directa, grupos y asistente de IA, construida con un frontend en **Angular 21** y un backend en **FastAPI** comunicados mediante **WebSockets**.

Los usuarios entran con un nombre, ven quién está conectado, inician conversaciones privadas y crean salas de grupo. Además pueden hablar con **Yuki**, una IA basada en **Groq**, y con **Gramàtica**, un chat de preguntas y respuestas sobre gramática española que responde **solo** a partir de tres tomos de gramática indexados con **RAG (Qdrant)**. Toda la mensajería viaja por una única conexión WebSocket por usuario.

<br/>

---

## <img src="https://api.iconify.design/ph/stack-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Tech Stack

| Capa | Tecnología |
| :--- | :--- |
| <img src="https://api.iconify.design/ph/desktop-tower-fill.svg?color=%235B9BD5&height=18" height="16"> **Frontend** | Angular 21 (standalone components, signals, `NgOptimizedImage`), TypeScript |
| <img src="https://api.iconify.design/ph/cpu-fill.svg?color=%232FB5AE&height=18" height="16"> **Backend** | FastAPI, Uvicorn, `websockets` |
| <img src="https://api.iconify.design/ph/robot-fill.svg?color=%235B9BD5&height=18" height="16"> **IA** | Groq (`AsyncGroq`, modelo `llama-3.1-8b-instant`) |
| <img src="https://api.iconify.design/ph/database-fill.svg?color=%232FB5AE&height=18" height="16"> **RAG** | Qdrant (vector DB) + `fastembed` (embeddings ONNX, sin torch) |
| <img src="https://api.iconify.design/ph/plugs-connected-fill.svg?color=%23E0A63B&height=18" height="16"> **Comunicación** | WebSocket (`/ws/{username}`) |
| <img src="https://api.iconify.design/ph/rocket-launch-fill.svg?color=%235B9BD5&height=18" height="16"> **Deploy** | Render (frontend como Static Site, backend como Web Service) |

<br/>

---

## <img src="https://api.iconify.design/ph/folder-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Estructura del Proyecto

<pre><code>Chat/
├── backend/
│   ├── main.py                # App FastAPI: WebSocket, ConnectionManager, Yuki, RAG
│   ├── rag.py                 # Recuperación: embeddings (fastembed) + búsqueda en Qdrant
│   ├── ingest_pdf.py          # Ingesta OFFLINE de los PDFs a Qdrant (no se ejecuta en Render)
│   ├── requirements.txt       # Dependencias del servidor (incluye fastembed)
│   ├── requirements-rag.txt   # Extra solo para la ingesta local (pdfplumber)
│   ├── test_*.py              # Tests (pytest): Yuki, rooms, RAG, ingesta, PDF chat
│   ├── pdfs/                  # PDFs fuente de la ingesta (ignorado en git)
│   ├── .env                   # Claves: GROQ/QDRANT (ignorado en git)
│   └── venv/                  # Entorno virtual de Python (ignorado en git)
│
└── frontend/
    └── chat-app/              # Proyecto Angular
        ├── src/app/
        │   ├── login/         # Pantalla de entrada (elegir nombre de usuario)
        │   ├── chat/          # Vista principal del chat
        │   │   ├── chat.ts/.html/.scss   # Contactos, salas, Yuki, Gramàtica, responsive
        │   │   ├── ai-protocol.ts        # Parseo de payloads de IA (texto + tokens)
        │   │   ├── ws-url.ts             # Resuelve el backend (local vs Render)
        │   │   └── tooltip.directive.ts  # Tooltip para los tokens
        │   ├── app.ts         # Componente raíz
        │   └── app.config.ts
        ├── angular.json
        └── package.json</code></pre>

El backend mantiene **en memoria**:

* `connections`: mapa `username → WebSocket` de los usuarios conectados.
* `rooms`: mapa `nombre_sala → [miembros]`, con un límite de **3 salas por usuario** (`MAX_ROOMS_PER_USER`).
* Historiales de conversación con la IA (todos con su *system prompt* inicial):
  * `ai_histories` — chat dedicado con Yuki, **por usuario**.
  * `direct_ai_histories` — menciones `@yuki` en chats 1 a 1, **por pareja**.
  * `room_ai_histories` — menciones `@yuki` en salas, **por sala**.
  * `pdf_histories` — chat de gramática (RAG), **por usuario**.

<br/>

### <img src="https://api.iconify.design/ph/arrows-left-right-bold.svg?color=%232FB5AE&height=20" height="18"> Protocolo de mensajes (WebSocket)

Los mensajes son texto plano con prefijos. Las respuestas de IA llevan un cuerpo JSON `{text, usage}`, donde `usage` es `{prompt_tokens, completion_tokens, total_tokens}` o `null` si no aplica.

| Mensaje | Dirección | Significado |
| :--- | :--- | :--- |
| `receptor:texto` | cliente → server | Mensaje directo a otro usuario |
| `JOIN:sala:miembro1,miembro2` | cliente → server | Crear / unirse a una sala |
| `ROOM:sala:texto` | cliente → server | Mensaje a una sala |
| `AI:texto` | cliente → server | Mensaje al chat dedicado de Yuki |
| `PDF:texto` | cliente → server | Pregunta al chat de gramática (RAG) |
| `SYSTEM:users:user1,user2` | server → cliente | Lista de usuarios conectados |
| `SYSTEM:error:...` | server → cliente | Error (p. ej. límite de salas alcanzado) |
| `JOIN:sala:miembro1,miembro2` | server → cliente | Confirmación de membresía de sala |
| `ROOM:sala:emisor:texto` | server → cliente | Mensaje entrante de una sala |
| `AI:{json}` | server → cliente | Respuesta de Yuki (chat dedicado) |
| `DIRECTAI:contacto:{json}` | server → cliente | Respuesta de Yuki en un chat 1 a 1 (por `@yuki`) |
| `ROOMAI:sala:{json}` | server → cliente | Respuesta de Yuki en una sala (por `@yuki`) |
| `PDF:{json}` | server → cliente | Respuesta del chat de gramática |

> **`@yuki` en cualquier conversación:** en los chats 1 a 1 y en las salas, Yuki solo responde cuando el mensaje contiene `@yuki`. En el chat dedicado *"Yuki, la teva IA"* responde a todos los mensajes sin necesidad de mencionarla.

<br/>

---

## <img src="https://api.iconify.design/ph/play-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Ejecutar en Local

Necesitas **Python 3.11+** y **Node.js 20+** (con npm).

### 1. Backend (FastAPI)

<pre><code>cd backend

# Crear y activar el entorno virtual
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias del servidor
pip install -r requirements.txt

# Crear backend/.env con las claves (ver "Variables de entorno")
# Arrancar el servidor (puerto 8000)
uvicorn main:app --reload</code></pre>

El backend quedará disponible en `http://localhost:8000` y el WebSocket en `ws://localhost:8000/ws/{username}`.

> El CORS del backend permite por defecto el origen `http://localhost:4200` (el dev server de Angular).

### 2. Frontend (Angular)

<pre><code>cd frontend/chat-app

# Instalar dependencias
npm install

# Arrancar el dev server (puerto 4200)
npm start</code></pre>

Abre `http://localhost:4200` en el navegador.

> **URL del WebSocket:** [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts) la resuelve automáticamente — si la página se sirve desde `localhost`/`127.0.0.1` apunta a `ws://localhost:8000`; en cualquier otro dominio, al backend de Render (`wss://chat-backend-6g1r.onrender.com`). No hace falta editar nada para el desarrollo local.

<br/>

---

## <img src="https://api.iconify.design/ph/sliders-horizontal-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Variables de entorno

El backend lee `backend/.env` (vía `python-dotenv`). Las variables ya definidas en el entorno (p. ej. en Render) tienen prioridad. En **Render** hay que configurarlas en el panel del servicio.

| Variable | Necesaria para | Descripción |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Yuki (IA) | Clave de la API de Groq. |
| `QDRANT_URL` | Chat de gramática | URL del clúster de Qdrant. |
| `QDRANT_API_KEY` | Chat de gramática | Clave de la API de Qdrant. |
| `QDRANT_TIMEOUT` | *(opcional)* | Timeout del cliente Qdrant en segundos (por defecto `120`). |
| `FASTEMBED_CACHE_DIR` | *(opcional)* | Ruta de caché del modelo de embeddings (por defecto `backend/.fastembed_cache`). |

`backend/.env` está en `.gitignore`: **no** se sube al repositorio.

<br/>

---

## <img src="https://api.iconify.design/ph/book-open-text-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Ingesta de los PDFs (RAG)

El chat **Gramàtica** responde solo a partir de tres tomos de *Gramática descriptiva de la lengua española* (volúmenes 1, 2 y 3), troceados e indexados en Qdrant. La ingesta se ejecuta **una vez en local** (no en Render): descarga el modelo de embeddings y sube los vectores al clúster.

* **Modelo de embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dims, distancia coseno), vía `fastembed` (ONNX, sin torch) — el mismo modelo para indexar y para buscar, así los vectores son compatibles.
* **Colección:** `gramatica`.
* **Troceado:** ~500 palabras por *chunk* con 50 de solapamiento.

Pasos:

<pre><code>cd backend
# (con el venv activado y backend/.env configurado)

# Dependencia extra solo para leer los PDFs
pip install -r requirements-rag.txt

# Coloca los PDFs en backend/pdfs/ y lanza la ingesta
python ingest_pdf.py
# o rutas concretas: python ingest_pdf.py ruta/a/tomo1.pdf ruta/a/tomo2.pdf</code></pre>

La ingesta es **reanudable**: usa IDs deterministas (idempotentes) y salta las páginas ya indexadas, así que si se corta (timeout de red, etc.) basta con volver a ejecutarla y continúa donde estaba. Los *upserts* reintentan automáticamente con *backoff* ante errores transitorios.

<br/>

---

## <img src="https://api.iconify.design/ph/cloud-arrow-up-fill.svg?color=%232FB5AE&height=24" height="22"> &nbsp;Despliegue en Render

El proyecto se despliega como dos servicios independientes.

### Backend — Web Service

1. En el panel de Render: **New → Web Service** y conecta el repositorio.
2. Configuración:
   * **Root Directory:** `backend`
   * **Runtime:** Python 3
   * **Build Command:** `pip install -r requirements.txt && python -c "from rag import get_model; get_model()"`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. En **Environment**, añade `GROQ_API_KEY`, `QDRANT_URL` y `QDRANT_API_KEY` (ver "Variables de entorno").

> **Caché del modelo de embeddings:** el `python -c "..."` del Build Command **descarga el modelo durante el build** hacia `backend/.fastembed_cache/`. Como los ficheros creados en el build forman parte del deploy, quedan disponibles en runtime y **se reutilizan entre cold starts** (en vez de descargarlos de HuggingFace en cada arranque, que hacía el cold start ~50s). El servidor además **pre-carga** el modelo en el arranque (evento `lifespan` de FastAPI), así la primera pregunta al chat de gramática no falla ni se cuelga esperando la carga. La ruta es configurable con `FASTEMBED_CACHE_DIR`.

> Render **no** ejecuta la ingesta: `fastembed` (búsqueda) sí está en `requirements.txt`, pero `pdfplumber` (lectura de PDFs) queda en `requirements-rag.txt`, que solo se instala en local. La colección `gramatica` debe estar ya indexada en Qdrant.

Render expone el servicio sobre HTTPS, por lo que el WebSocket se conecta vía `wss://`.

### Frontend — Static Site

1. **New → Static Site** y conecta el mismo repositorio.
2. Configuración:
   * **Root Directory:** `frontend/chat-app`
   * **Build Command:** `npm install && npm run build`
   * **Publish Directory:** `dist/chat-app/browser`
3. La URL del backend se resuelve sola en [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts); si cambia el dominio del backend, actualiza `PROD_WS_BASE` ahí.

> Recuerda actualizar `allow_origins` en [main.py](backend/main.py) para incluir el dominio del frontend en producción.

<br/>

---

## <img src="https://api.iconify.design/ph/sparkle-fill.svg?color=%235B9BD5&height=24" height="22"> &nbsp;Funcionalidades actuales

* **Entrada por nombre de usuario** — sin contraseña; cada usuario abre su propia conexión WebSocket.
* **Lista de usuarios en línea** — actualizada dinámicamente al conectarse/desconectarse usuarios.
* **Mensajería directa** — chat privado 1 a 1 entre usuarios conectados.
* **Salas de grupo** — crear grupos con nombre seleccionando varios usuarios; mensajes difundidos a todos los miembros.
* **Límite de salas** — máximo de 3 salas por usuario, controlado por el servidor.
* **Re-sincronización de salas** — al reconectar, el usuario recupera las salas a las que pertenece.
* **Yuki, la IA del chat** — asistente basado en Groq (`llama-3.1-8b-instant`), que responde en el idioma del usuario y mantiene **historial por usuario**. Cada respuesta muestra los **tokens** consumidos, con un **tooltip** al pasar por encima (prompt · respuesta · total).
* **`@yuki` en todas las conversaciones** — menciona `@yuki` en un chat 1 a 1 o en una sala y responde ahí mismo para todos los participantes; además tiene su propio chat dedicado.
* **Chat de Gramática (RAG)** — el chat *"Gramàtica"* responde **solo** con el contenido de los tres tomos de gramática indexados en Qdrant; si la pregunta se sale del contexto, lo dice en vez de inventar.
* **Diseño responsive (móvil)** — patrón tipo Messenger/WhatsApp: en pantallas estrechas (≤ 768 px) se ve primero la lista de chats y, al abrir una conversación, esta ocupa toda la pantalla con un botón de "atrás".
* **UI reactiva con signals** — Angular 21 con componentes standalone y estado basado en signals.

<br/>

---

## <img src="https://api.iconify.design/ph/warning-circle-fill.svg?color=%23E0A63B&height=24" height="22"> &nbsp;Limitaciones conocidas

* El estado (usuarios, salas e **historiales de IA**) se guarda **en memoria**: se pierde al reiniciar el backend.
* No hay persistencia del historial de mensajes ni base de datos (más allá de los vectores de gramática en Qdrant).
* La autenticación es nominal (solo nombre de usuario, sin verificación).
* El chat de gramática depende de una **ingesta previa** de los PDFs a Qdrant (paso manual en local) y de que `GROQ_API_KEY`/`QDRANT_URL`/`QDRANT_API_KEY` estén configuradas.
* Con la capa gratuita de Groq/Qdrant puede haber **límites de tasa** (respuestas más lentas o reintentos); el modelo `8b` es pequeño y puede fallar en casos límite.
* El dominio del backend de producción está fijado como constante en [ws-url.ts](frontend/chat-app/src/app/chat/ws-url.ts) (`PROD_WS_BASE`).

<br/>

---

<div align="center">

Desenvolupat per **Carme Medina Canalda**  
*Full Stack Developer · Barcelona*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-a8c4f0?style=flat-square&logo=linkedin&logoColor=1b2e4b)](https://www.linkedin.com/in/carme-medina-canalda-250457132/)
[![Portfolio](https://img.shields.io/badge/Portfolio-5b9bd5?style=flat-square&logoColor=ffffff)](https://carme-portfoli.onrender.com/)

</div>
