import asyncio
import json
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {"agents": set(), "browsers": set(), "interfaces": set()}

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections[client_type].add(websocket)

    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections[client_type].remove(websocket)

    async def broadcast_to_type(self, message: str, client_type: str):
        for connection in self.active_connections[client_type]:
            await connection.send_text(message)

    async def broadcast_to_all(self, message: str):
        for client_type in self.active_connections:
            await self.broadcast_to_type(message, client_type)


class Message(BaseModel):
    sender: str
    message_type: str
    content: dict
    target: str = "all"


app = FastAPI()
manager = ConnectionManager()


@app.websocket("/ws/{client_id}/{client_type}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, client_type: str):
    await manager.connect(websocket, client_type)
    try:
        while True:
            data = await websocket.receive_text()
            message = Message.parse_raw(data)

            # Process message based on type
            if message.message_type == "agent_status":
                # Broadcast agent status updates
                await manager.broadcast_to_type(data, "interfaces")
                await manager.broadcast_to_type(data, "browsers")

            elif message.message_type == "task_update":
                # Broadcast task updates to all
                await manager.broadcast_to_all(data)

            elif message.message_type == "browser_command":
                # Send commands to browser extensions
                await manager.broadcast_to_type(data, "browsers")

            elif message.message_type == "interface_action":
                # Handle interface control actions
                await manager.broadcast_to_type(data, "agents")

            elif message.message_type == "direct_message":
                # Handle direct messages between agents
                target_connections = manager.active_connections.get(message.target, set())
                for conn in target_connections:
                    await conn.send_text(data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_type)
        disconnect_message = {
            "sender": client_id,
            "message_type": "disconnect",
            "content": {"client_type": client_type},
        }
        await manager.broadcast_to_all(json.dumps(disconnect_message))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
