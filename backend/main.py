from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import AsyncGroq

import rag

# Load backend/.env regardless of the working directory uvicorn is launched from.
# Existing environment variables (e.g. those set by Render) take precedence.
load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_ROOMS_PER_USER = 3

GROQ_MODEL = "openai/gpt-oss-120b"

AI_SYSTEM_PROMPT = (
    "Et dius Yuki i ets l'assistent d'aquest xat. Ets dolça, amable i una mica "
    "kawaii en el to: pots fer servir alguna expressió tendra de tant en tant, "
    "sense exagerar. Respon SEMPRE en el mateix idioma que fa servir l'usuari al "
    "seu missatge, adaptant-t'hi automàticament. Si et pregunten qui ets, presenta't "
    "com la Yuki, l'assistent del xat."
)

PDF_SYSTEM_PROMPT = (
    "Eres un asistente experto en gramática española. Respondes preguntas "
    "sobre gramática apoyándote en el contexto proporcionado (fragmentos "
    "extraídos de los libros).\n"
    "- Si el contexto contiene información relacionada con la pregunta, "
    "responde de forma clara y útil basándote en él; puedes explicarlo y "
    "resumirlo con tus palabras, pero sin añadir datos que no estén "
    "respaldados por el contexto.\n"
    "- Si la pregunta trata un tema ajeno a la gramática, o el contexto no "
    "contiene información relacionada con ella, responde únicamente: «No "
    "encuentro esa información en los libros.» En ese caso NO uses tu "
    "conocimiento externo para responder (por ejemplo, geografía, historia o "
    "cultura general).\n"
    "- No inventes información."
)

# Missatge que es mostra quan falla la infraestructura (Qdrant o Groq), NO quan
# simplement no hi ha resposta als llibres (això ho diu el propi model). En
# castellà i amable, coherent amb la resta del chatbot de gramàtica.
PDF_ERROR_MESSAGE = (
    "Lo siento, ha habido un problema al consultar los libros. "
    "Por favor, inténtalo de nuevo."
)

# Nombre màxim d'intercanvis (parella pregunta/resposta) que es conserven a
# l'historial del xat de gramàtica. Cada torn hi guarda el context del RAG, així
# que sense límit l'historial creix i supera el límit de tokens de Groq (413).
PDF_MAX_EXCHANGES = 3


def trim_history(messages: list[dict], max_exchanges: int) -> list[dict]:
    """Conserva el system prompt (primer missatge) + els últims `max_exchanges`
    intercanvis (2*max_exchanges missatges). No modifica la llista original."""
    if not messages:
        return messages
    keep = max_exchanges * 2
    return messages[:1] + messages[1:][-keep:] if keep else messages[:1]

_groq_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    return _groq_client


async def call_groq(messages: list[dict]) -> tuple[str, dict]:
    response = await get_groq_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
    )
    text = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return text, usage


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self.rooms: dict[str, list[str]] = {}
        self.room_ai_histories: dict[str, list[dict]] = {}
        self.ai_histories: dict[str, list[dict]] = {}
        self.direct_ai_histories: dict[str, list[dict]] = {}
        self.pdf_histories: dict[str, list[dict]] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[username] = websocket

    def disconnect(self, username: str):
        self.connections.pop(username, None)

    async def send_text(self, username: str, message: str):
        socket = self.connections.get(username)
        if socket:
            try:
                await socket.send_text(message)
            except Exception:
                self.connections.pop(username, None)

    @staticmethod
    def _pair_key(a: str, b: str) -> str:
        return "|".join(sorted([a, b]))

    def _ensure_direct_history(self, key: str) -> list[dict]:
        history = self.direct_ai_histories.get(key)
        if history is None:
            history = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
            self.direct_ai_histories[key] = history
        return history

    async def _handle_direct_ai(self, sender: str, receiver: str, message: str):
        history = self._ensure_direct_history(self._pair_key(sender, receiver))
        history.append({"role": "user", "content": f"{sender}: {message}"})
        if "@yuki" not in message.lower():
            return
        try:
            reply, usage = await call_groq(history)
        except Exception:
            logger.exception("Groq direct call failed for %s/%s", sender, receiver)
            return
        history.append({"role": "assistant", "content": reply})
        body = json.dumps({"text": reply, "usage": usage})
        await self.send_text(sender, f"DIRECTAI:{receiver}:{body}")
        await self.send_text(receiver, f"DIRECTAI:{sender}:{body}")

    async def send_to(self, sender: str, receiver: str, message: str):
        await self.send_text(receiver, f"{sender}:{message}")
        await self._handle_direct_ai(sender, receiver, message)

    async def broadcast(self, message: str):
        for username in list(self.connections.keys()):
            await self.send_text(username, message)

    async def broadcast_user_list(self):
        users = ",".join(self.connections.keys())
        await self.broadcast(f"SYSTEM:users:{users}")

    def _ensure_ai_history(self, username: str) -> list[dict]:
        history = self.ai_histories.get(username)
        if history is None:
            history = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
            self.ai_histories[username] = history
        return history

    async def handle_ai_message(self, username: str, text: str):
        history = self._ensure_ai_history(username)
        history.append({"role": "user", "content": text})
        try:
            reply, usage = await call_groq(history)
        except Exception:
            logger.exception("Groq call failed for %s", username)
            await self.send_text(
                username,
                "AI:" + json.dumps(
                    {"text": "⚠️ no s'ha pogut contactar amb la IA", "usage": None}
                ),
            )
            return
        history.append({"role": "assistant", "content": reply})
        logger.info(
            "AI: reply sent to %s (%s tokens)", username, usage["total_tokens"]
        )
        await self.send_text(
            username,
            "AI:" + json.dumps({"text": reply, "usage": usage}),
        )

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
                    {"text": PDF_ERROR_MESSAGE, "usage": None}
                ),
            )
            return
        history = self._ensure_pdf_history(username)
        context = "\n---\n".join(chunks)
        history.append({
            "role": "user",
            "content": f"Contexto:\n{context}\n\nPregunta: {query}",
        })
        # Acota l'historial abans d'enviar-lo a Groq perquè no superi el límit
        # de tokens (413). trim_history no muta, així que reassignem in place.
        history[:] = trim_history(history, PDF_MAX_EXCHANGES)
        try:
            reply, usage = await call_groq(history)
        except Exception:
            logger.exception("Groq PDF call failed for %s", username)
            await self.send_text(
                username,
                "PDF:" + json.dumps(
                    {"text": PDF_ERROR_MESSAGE, "usage": None}
                ),
            )
            return
        history.append({"role": "assistant", "content": reply})
        history[:] = trim_history(history, PDF_MAX_EXCHANGES)
        await self.send_text(
            username,
            "PDF:" + json.dumps({"text": reply, "usage": usage}),
        )

    # ---- Rooms ----

    def _ensure_room_history(self, room_name: str) -> list[dict]:
        history = self.room_ai_histories.get(room_name)
        if history is None:
            history = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
            self.room_ai_histories[room_name] = history
        return history

    def _room_count(self, user: str) -> int:
        return sum(1 for members in self.rooms.values() if user in members)

    async def join_room(self, creator: str, room_name: str, members: list[str]):
        existing = self.rooms.get(room_name, [])

        # The creator must be able to take a slot if they aren't already in.
        if creator not in existing and self._room_count(creator) >= MAX_ROOMS_PER_USER:
            await self.send_text(
                creator, f"SYSTEM:error:room limit reached ({MAX_ROOMS_PER_USER})"
            )
            return

        # Dedupe while preserving order; creator is always a member.
        desired = list(dict.fromkeys([creator] + members))
        final_members = list(existing)
        for user in desired:
            if user in final_members:
                continue
            if self._room_count(user) >= MAX_ROOMS_PER_USER:
                await self.send_text(
                    user, f"SYSTEM:error:room limit reached ({MAX_ROOMS_PER_USER})"
                )
                continue
            final_members.append(user)

        self.rooms[room_name] = final_members
        await self.broadcast_room_membership(room_name)

    async def broadcast_room_membership(self, room_name: str):
        members = self.rooms.get(room_name, [])
        payload = f"JOIN:{room_name}:{','.join(members)}"
        for user in members:
            await self.send_text(user, payload)

    async def send_to_room(self, sender: str, room_name: str, message: str):
        members = self.rooms.get(room_name, [])
        if sender not in members:
            return
        payload = f"ROOM:{room_name}:{sender}:{message}"
        for user in members:
            if user == sender:
                continue
            await self.send_text(user, payload)

        await self._handle_room_ai(room_name, sender, message)

    async def _handle_room_ai(self, room_name: str, sender: str, message: str):
        history = self._ensure_room_history(room_name)
        history.append({"role": "user", "content": f"{sender}: {message}"})
        if "@yuki" not in message.lower():
            return
        try:
            reply, usage = await call_groq(history)
        except Exception:
            logger.exception("Groq room call failed for %s", room_name)
            return
        history.append({"role": "assistant", "content": reply})
        payload = "ROOMAI:" + room_name + ":" + json.dumps(
            {"text": reply, "usage": usage}
        )
        for user in self.rooms.get(room_name, []):
            await self.send_text(user, payload)

    async def send_user_rooms(self, username: str):
        # Re-sync rooms this user already belongs to (e.g. after reconnect).
        for room_name, members in self.rooms.items():
            if username in members:
                await self.send_text(
                    username, f"JOIN:{room_name}:{','.join(members)}"
                )

manager = ConnectionManager()

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(username, websocket)
    await manager.broadcast_user_list()
    await manager.send_user_rooms(username)
    try:
        while True:
            data = await websocket.receive_text()

            if data.startswith("JOIN:"):
                _, room_name, members = data.split(":", 2)
                member_list = [m for m in members.split(",") if m]
                await manager.join_room(username, room_name, member_list)

            elif data.startswith("ROOM:"):
                _, room_name, message = data.split(":", 2)
                await manager.send_to_room(username, room_name, message)

            elif data.startswith("AI:"):
                await manager.handle_ai_message(username, data[len("AI:"):])

            elif data.startswith("PDF:"):
                await manager.handle_pdf_message(username, data[len("PDF:"):])

            else:
                receiver, message = data.split(":", 1)
                await manager.send_to(username, receiver, message)

    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_user_list()
