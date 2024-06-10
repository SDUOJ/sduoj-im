from typing import List

from model.redis_db import redis_client
from type.notice import notice_information_interface
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

    def disconnect(self, u_id: int):
        # 关闭时 移除ws对象
        if u_id in self.active_connections:
            del self.active_connections[u_id]

    @staticmethod
    async def send_personal_message(message, ws: WebSocket):
        # 发送个人消息
        if type(message) != str:
            await ws.send_json(message)
        else:
            await ws.send_text(message)

    async def broadcast(self, message, u_list: list, notice_id: int):
        # 广播通知
        for u_id in u_list:
            if u_id in ws_manager.active_connections:
                if type(message) == str:
                    await self.active_connections[u_id].send_text(message)
                else:
                    await self.active_connections[u_id].send_json(message)
            else:
                redis_client.rpush(f'cache:unreadUsers:{u_id}', f'notice-{notice_id}')
                redis_client.ltimeset(f'cache:unreadUsers:{u_id}', 1 * 24 * 3600)


ws_manager = WSConnectionManager()
