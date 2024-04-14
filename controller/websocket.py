import asyncio
import json
from typing import Optional

from fastapi import APIRouter
from fastapi import Request
from fastapi import WebSocket, WebSocketDisconnect

from model.websocket import ws_manager
from service.message import MessageModel
from service.notice import NoticeModel
from type.message import message_add_interface, message_receive_interface, message_get_interface
from type.notice import base_interface, notice_information_interface, notice_add_interface, notice_interface,notice_update_interface
from utils.response import user_standard_response

ws_router = APIRouter()
message_model = MessageModel()
notice_model = NoticeModel()

num = 1


@ws_router.websocket("/buildConnect/{m_from}")  # 建立websocket连接
async def connect_build(websocket: WebSocket, m_from: int):
    if m_from not in ws_manager.active_connections:
        await ws_manager.connect(websocket, m_from)
    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=500000)  # websocket过期时间
            mode = data['mode']  # 0为向他人发送消息; 1为查看与某人的消息; 2为查看提问列表; 3为发布公告; 4为修改公告
            data.pop('mode')
            if mode == 0:
                message = message_receive_interface.model_validate(data)
                if message.m_to in ws_manager.active_connections:  # 如果接收者在线
                    await ws_manager.send_personal_message(json.dumps({"m_content":message.m_content}),
                                                           ws_manager.active_connections[message.m_to])
                message_add = message_add_interface(**data, m_from=m_from)
                message_model.add_message(message_add)
            elif mode == 1:
                message = message_get_interface.model_validate(data)
                messages = message_model.get_message(m_from, message)
                await ws_manager.send_personal_message(messages, websocket)
            elif mode == 2:
                base = base_interface.model_validate(data)
                message_list = message_model.get_message_list(m_from, base)
                await ws_manager.send_personal_message(message_list, websocket)
            elif mode == 3:
                student_list = [2]
                notice_add = notice_add_interface(**data, u_id=m_from)
                await ws_manager.broadcast(notice_add.model_dump_json(), student_list)
                notice_model.add_notice(notice_add)
            elif mode == 4:
                notice_update = notice_update_interface(**data)
                print(notice_update)
                notice_model.update_notice(notice_update)
                data.pop('n_id')
                notice_information = notice_add_interface(**data, u_id=m_from)
                student_list = [2]
                await ws_manager.broadcast(notice_information.model_dump_json(), student_list)
    except asyncio.TimeoutError:
        ws_manager.disconnect(websocket, m_from)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, m_from)
