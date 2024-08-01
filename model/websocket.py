from typing import List

from model.redis_db import redis_client
from type.notice import notice_information_interface
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict


class WSConnectionManager:
    def __init__(self):
        # 存放激活的ws连接对象
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, username: str):
        # 等待连接
        await ws.accept()
        # 存储ws连接对象
        self.active_connections[username] = ws

    def disconnect(self, username: str):
        # 关闭时 移除ws对象
        if username in self.active_connections:
            del self.active_connections[username]

    @staticmethod
    async def send_personal_message(message, ws: WebSocket):
        # 发送个人消息
        if type(message) != str:
            await ws.send_json(message)
        else:
            await ws.send_text(message)

    async def broadcast(self, mode: int, message, u_list: list, project_id: int = None, m_from: int = None,
                        mg_id: int = None):
        # 广播通知
        for u_id in u_list:
            u_id = u_id['userId']
            if u_id == m_from:
                continue
            if u_id in ws_manager.active_connections:
                if type(message) == str:
                    await self.active_connections[u_id].send_text(message)
                else:
                    await self.active_connections[u_id].send_json(message)
            else:
                if mode == 0:
                    redis_client.rpush(f'cache:unreadUsers:{u_id}', f'cache:messageGroup:{mg_id}-{project_id}')
                    redis_client.ltimeset(f'cache:unreadUsers:{u_id}', 1 * 24 * 3600)
                elif mode == 1:
                    redis_client.rpush(f'cache:unreadUsers:{u_id}', f'notice-{project_id}')
                    redis_client.ltimeset(f'cache:unreadUsers:{u_id}', 1 * 24 * 3600)


ws_manager = WSConnectionManager()
