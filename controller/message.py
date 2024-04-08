import asyncio
from model.websocket import ws_manager
from fastapi import APIRouter
from fastapi import Request
from fastapi import WebSocket, WebSocketDisconnect
from type.message import message_add_interface
from utils.response import user_standard_response
from service.message import MessageModel
message_router = APIRouter()

message_model = MessageModel()
@message_router.websocket("/sendMessage/{m_to}")  # 发送消息
async def message_send(websocket: WebSocket, m_to : int):
    m_from = 1  # 获取当前用户u_id
    await ws_manager.connect(websocket, m_from)
    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=50)  # websocket过期时间
            await ws_manager.send_personal_message(f"{data}", websocket)
            if m_to in ws_manager.active_connections:
                await ws_manager.send_personal_message(f"{data}",
                                                   ws_manager.active_connections[m_to])

            message_model
    except asyncio.TimeoutError:
        ws_manager.disconnect(websocket, message.m_from)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, message.m_from)


@message_router.get("/getMessage")  # 查看与某人的消息
@user_standard_response
async def message_get(request: Request, ):
    # 获取发送消息的用户的id   m_from =
    # 获取接收消息的用户的id   m_to =

    return {'message': '信息发送成功', 'data': True, 'code': 0}


@message_router.post("/viewMessage")  # 查看自己的提问
@user_standard_response
async def message_view(request: Request):
    return {'message': '查看信息成功', 'data': True, 'code': 0}
