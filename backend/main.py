from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[username] = websocket

    def disconnect(self, username: str):
        self.connections.pop(username, None)

    async def send_to(self, sender: str, receiver: str, message: str):
        receiver_socket = self.connections.get(receiver)
        if receiver_socket:
            await receiver_socket.send_text(f"{sender}:{message}")

    async def broadcast(self, message: str):
        for username, socket in list(self.connections.items()):
            try:
                await socket.send_text(message)
            except Exception:
                self.connections.pop(username, None)

    async def broadcast_user_list(self):
        users = ",".join(self.connections.keys())
        await self.broadcast(f"SYSTEM:users:{users}")

manager = ConnectionManager()

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(username, websocket)
    await manager.broadcast_user_list()
    try:
        while True:
            data = await websocket.receive_text()
            receiver, message = data.split(":", 1)
            await manager.send_to(username, receiver, message)
    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_user_list()