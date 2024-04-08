from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict


class WSConnectionManager:
    def __init__(self):
        # 存放激活的ws连接对象
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, ws: WebSocket, u_id: int):
        # 等待连接
        await ws.accept()
        # 存储ws连接对象
        self.active_connections[u_id] = ws

    def disconnect(self, ws: WebSocket, u_id: int):
        # 关闭时 移除ws对象
        self.active_connections.pop(u_id)

    @staticmethod
    async def send_personal_message(message: str, ws: WebSocket):
        # 发送个人消息
        await ws.send_text(message)

    async def broadcast(self, message: str):
        # 广播消息
        for id, ws in self.active_connections.items():
            await ws.send_text(message)


ws_manager = WSConnectionManager()