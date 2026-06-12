# Chat en Tiempo Real

Aplicación de chat en tiempo real con mensajería directa y grupos, construida con un frontend en **Angular 21** y un backend en **FastAPI** comunicados mediante **WebSockets**.

Los usuarios entran con un nombre, ven quién está conectado, inician conversaciones privadas y crean salas de grupo. Toda la mensajería viaja por una única conexión WebSocket por usuario.

## Tech Stack

| Capa     | Tecnología                                              |
| -------- | ------------------------------------------------------- |
| Frontend | Angular 21 (standalone components, signals), TypeScript |
| Backend  | FastAPI, Uvicorn, `websockets`                          |
| Comunicación | WebSocket (`/ws/{username}`)                        |
| Deploy   | Render (frontend como Static Site, backend como Web Service) |

## Estructura del Proyecto

```
Chat/
├── backend/
│   ├── main.py              # App FastAPI: endpoint WebSocket y ConnectionManager
│   └── venv/                # Entorno virtual de Python (ignorado en git)
│
└── frontend/
    └── chat-app/            # Proyecto Angular
        ├── src/app/
        │   ├── login/       # Pantalla de entrada (elegir nombre de usuario)
        │   ├── chat/        # Vista principal del chat (contactos, salas, mensajes)
        │   ├── app.ts       # Componente raíz
        │   └── app.config.ts
        ├── angular.json
        └── package.json
```

El backend mantiene en memoria:

- `connections`: mapa `username → WebSocket` de los usuarios conectados.
- `rooms`: mapa `nombre_sala → [miembros]`, con un límite de **3 salas por usuario** (`MAX_ROOMS_PER_USER`).

### Protocolo de mensajes (WebSocket)

Los mensajes son texto plano con prefijos:

| Mensaje                          | Dirección        | Significado                              |
| -------------------------------- | ---------------- | ---------------------------------------- |
| `receptor:texto`                 | cliente → server | Mensaje directo a otro usuario           |
| `JOIN:sala:miembro1,miembro2`    | cliente → server | Crear / unirse a una sala                |
| `ROOM:sala:texto`                | cliente → server | Mensaje a una sala                       |
| `SYSTEM:users:user1,user2`       | server → cliente | Lista de usuarios conectados             |
| `SYSTEM:error:...`               | server → cliente | Error (p. ej. límite de salas alcanzado) |
| `JOIN:sala:miembro1,miembro2`    | server → cliente | Confirmación de membresía de sala        |
| `ROOM:sala:emisor:texto`         | server → cliente | Mensaje entrante de una sala             |

## Ejecutar en Local

Necesitas **Python 3.11+** y **Node.js 20+** (con npm).

### 1. Backend (FastAPI)

```bash
cd backend

# Crear y activar el entorno virtual
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install fastapi "uvicorn[standard]" websockets

# Arrancar el servidor (puerto 8000)
uvicorn main:app --reload
```

El backend quedará disponible en `http://localhost:8000` y el WebSocket en `ws://localhost:8000/ws/{username}`.

> El CORS del backend permite por defecto el origen `http://localhost:4200` (el dev server de Angular).

### 2. Frontend (Angular)

```bash
cd frontend/chat-app

# Instalar dependencias
npm install

# Arrancar el dev server (puerto 4200)
npm start
```

Abre `http://localhost:4200` en el navegador.

> **Nota:** la URL del WebSocket está fijada en [chat.ts](frontend/chat-app/src/app/chat/chat.ts#L94) apuntando al backend desplegado en Render (`wss://chat-backend-6g1r.onrender.com`). Para probar contra el backend local, cámbiala temporalmente a `ws://localhost:8000/ws/${this.myName()}`.

## Despliegue en Render

El proyecto se despliega como dos servicios independientes.

### Backend — Web Service

1. En el panel de Render: **New → Web Service** y conecta el repositorio.
2. Configuración:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Crea un `requirements.txt` dentro de `backend/` con las dependencias:

   ```txt
   fastapi
   uvicorn[standard]
   websockets
   ```

Render expone el servicio sobre HTTPS, por lo que el WebSocket se conecta vía `wss://`.

### Frontend — Static Site

1. **New → Static Site** y conecta el mismo repositorio.
2. Configuración:
   - **Root Directory:** `frontend/chat-app`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist/chat-app/browser`
3. Asegúrate de que la URL del WebSocket en [chat.ts](frontend/chat-app/src/app/chat/chat.ts) apunte al dominio `wss://` del backend desplegado.

> Recuerda actualizar `allow_origins` en [main.py](backend/main.py) para incluir el dominio del frontend en producción.

## Funcionalidades actuales

- 🔐 **Entrada por nombre de usuario** — sin contraseña; cada usuario abre su propia conexión WebSocket.
- 🟢 **Lista de usuarios en línea** — actualizada dinámicamente al conectarse/desconectarse usuarios.
- 💬 **Mensajería directa** — chat privado 1 a 1 entre usuarios conectados.
- 👥 **Salas de grupo** — crear grupos seleccionando varios usuarios; mensajes difundidos a todos los miembros.
- 📌 **Límite de salas** — máximo de 3 salas por usuario, controlado por el servidor.
- 🔄 **Re-sincronización de salas** — al reconectar, el usuario recupera las salas a las que pertenece.
- ⚡ **UI reactiva con signals** — Angular 21 con componentes standalone y estado basado en signals.

## Limitaciones conocidas

- El estado (usuarios y salas) se guarda **en memoria**: se pierde al reiniciar el backend.
- No hay persistencia del historial de mensajes ni base de datos.
- La autenticación es nominal (solo nombre de usuario, sin verificación).
- La URL del WebSocket está codificada en el frontend; conviene moverla a la configuración de entorno de Angular.
