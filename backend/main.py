from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import json
import os

from groq import AsyncGroq

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_ROOMS_PER_USER = 3

GROQ_MODEL = "llama-3.1-8b-instant"

AI_SYSTEM_PROMPT = (
    "Et dius Yuki i ets l'assistent d'aquest xat. Ets dolça, amable i una mica "
    "kawaii en el to: pots fer servir alguna expressió tendra de tant en tant, "
    "sense exagerar. Respon SEMPRE en català. Si et pregunten qui ets, presenta't "
    "com la Yuki, l'assistent del xat."
)

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
    text = response.choices[0].message.content
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
        self.ai_histories: dict[str, list[dict]] = {}

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

    async def send_to(self, sender: str, receiver: str, message: str):
        await self.send_text(receiver, f"{sender}:{message}")

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
            await self.send_text(
                username,
                "AI:" + json.dumps(
                    {"text": "⚠️ no s'ha pogut contactar amb la IA", "usage": None}
                ),
            )
            return
        history.append({"role": "assistant", "content": reply})
        await self.send_text(
            username,
            "AI:" + json.dumps({"text": reply, "usage": usage}),
        )

    # ---- Rooms ----

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

            else:
                receiver, message = data.split(":", 1)
                await manager.send_to(username, receiver, message)

    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_user_list()
