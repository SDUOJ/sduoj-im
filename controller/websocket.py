import asyncio
import json
import time
from datetime import datetime
from typing import Optional
from model.redis_db import redis_client
import websockets
from fastapi import APIRouter
from fastapi import Request
from fastapi import WebSocket, WebSocketDisconnect

from model.websocket import ws_manager
from service.message import MessageModel
from service.notice import NoticeModel
from type.functions import send_heartbeat
from type.message import message_add_interface, message_receive_interface, message_get_interface
from type.notice import base_interface, notice_information_interface, notice_add_interface, notice_interface, \
    notice_update_interface
from utils.response import user_standard_response

ws_router = APIRouter()
message_model = MessageModel()
notice_model = NoticeModel()


@ws_router.websocket("/buildConnect/{m_from}")  # 建立websocket连接(注释掉的部分为判断已读未读)
async def connect_build(websocket: WebSocket, m_from: int):
    if m_from not in ws_manager.active_connections:
        await ws_manager.connect(websocket, m_from)
    try:
        asyncio.create_task(send_heartbeat(websocket))
        while True:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=1000)  # websocket过期时间
            mode = data['mode']  # 1为向他人发送消息; 2为查看与某人的消息; 3为查看提问列表;  4为发布公告; 5为修改公告
            data.pop('mode')
            if mode == 1 or mode == 2:
                if m_from > data['m_to']:  # 固定格式为:p/ct_id - 小id - 大id
                    m_small = data['m_to']
                    m_big = m_from
                else:
                    m_small = m_from
                    m_big = data['m_to']
                redis_message_key = f"p-{data['p_id']}-{m_small}-{m_big}" if 'p_id' in data else f"ct-{data['ct_id']}-{m_small}-{m_big}"
            if mode == 1:
                # 处理消息发送逻辑
                # this_page = data["this_page"]  # 接收者是否在当前页查看消息
                # data.pop('this_page')
                message_add = message_add_interface(**data, m_from=m_from)
                current_time = message_model.add_message(message_add).strftime('%Y-%m-%d %H:%M:%S')
                message = message_receive_interface.model_validate(data)
                if message.m_to in ws_manager.active_connections:  # 如果接收者在线
                    await ws_manager.send_personal_message(
                        json.dumps({"m_content": message.m_content, "m_gmt_create": current_time}),
                        ws_manager.active_connections[message.m_to])
                    # if this_page:
                    #     unread_key = f"p-{data['p_id']}-{m_from}-{data['m_to']}-{current_timestamp}" if 'p_id' in data else f"ct-{data['ct_id']}-{m_from}-{data['m_to']}-{current_timestamp}"
                    #     if 'p_id' not in data:
                    #         await ws_manager.send_personal_message(
                    #             json.dumps(
                    #                 {"mode": 0, "time": current_timestamp, "m_to": data['m_to'], "ct_id": data['ct_id']}),
                    #             websocket)
                    #     else:
                    #         await ws_manager.send_personal_message(
                    #             json.dumps(
                    #                 {"mode": 0, "time": current_timestamp, "m_to": data['m_to'], "p_id": data['p_id']}),
                    #             websocket)
                    #     redis_client.set(unread_key, 1, 1 * 24 * 3600)
                else:  # 接收者不在线
                    pass
                    # 使用rabbitMQ存储消息

                    # unread_key = f"p-{data['p_id']}-{m_from}-{data['m_to']}-{current_timestamp}" if 'p_id' in data else f"ct-{data['ct_id']}-{m_from}-{data['m_to']}-{current_timestamp}"
                    # unread_count = redis_client.get(unread_key)  # 查找未读消息数量
                    # if unread_count is None:
                    #     redis_client.set(unread_key, 1, 7 * 24 * 3600)
                    # else:
                    #     redis_client.set(unread_key, int(unread_count) + 1, 7 * 24 * 3600)
                if 'p_id' in data:
                    redis_client.rpush(redis_message_key, json.dumps(
                        {"m_gmt_create": current_time, "m_from": m_from, "p_id": data['p_id']}))
                elif 'ct_id' in data:
                    redis_client.rpush(redis_message_key, json.dumps(
                        {"m_gmt_create": current_time, "m_from": m_from, "ct_id": data['ct_id']}))
                redis_client.ltimeset(redis_message_key, 1 * 24 * 3600)

            elif mode == 2:
                # 处理查看消息逻辑
                # unread_key = f"p-{data['p_id']}-{m_from}-{data['m_to']}-{current_timestamp}" if 'p_id' in data else f"ct-{data['ct_id']}-{m_from}-{data['m_to']}-{current_timestamp}"
                # if 'p_id' not in data:
                #     await ws_manager.send_personal_message(
                #         json.dumps(
                #             {"mode": 0, "time": current_timestamp, "m_to": data['m_to'], "ct_id": data['ct_id']}),
                #         websocket)
                # else:
                #     await ws_manager.send_personal_message(
                #         json.dumps(
                #             {"mode": 0, "time": current_timestamp, "m_to": data['m_to'], "p_id": data['p_id']}),
                #         websocket)
                # redis_client.set(unread_key, 1, 1 * 24 * 3600)
                redis_message_value = redis_client.lrange(redis_message_key, 0, -1)
                if redis_message_value:
                    redis_message_json = [json.loads(json_string) for json_string in redis_message_value]
                    await ws_manager.send_personal_message(redis_message_json, websocket)
                else:
                    message = message_get_interface.model_validate(data)
                    messages = message_model.get_message(m_from, message)
                    await ws_manager.send_personal_message(messages, websocket)
                    for mes in messages:
                        if 'p_id' in data:
                            redis_client.rpush(redis_message_key, json.dumps(
                                {"m_gmt_create": mes['m_gmt_create'], "m_from": mes['m_from'], "p_id": data['p_id']}))
                        elif 'ct_id' in data:
                            redis_client.rpush(redis_message_key, json.dumps(
                                {"m_gmt_create": mes['m_gmt_create'], "m_from": mes['m_from'], "ct_id": data['ct_id']}))
                    redis_client.ltimeset(redis_message_key, 1 * 24 * 3600)

            elif mode == 3:
                # 处理查看提问列表逻辑
                redis_message_list_key = f"list-p-{data['p_id']}-{m_from}" if 'p_id' in data else f"list-ct-{data['ct_id']}-{m_from}"
                redis_message_list_value = redis_client.lrange(redis_message_list_key, 0, -1)
                if redis_message_list_value:
                    await ws_manager.send_personal_message(redis_message_list_value, websocket)
                else:
                    base = base_interface.model_validate(data)
                    message_list = message_model.get_message_list(m_from, base)
                    await ws_manager.send_personal_message(message_list, websocket)
                    for mes in message_list:
                        redis_client.lpush(redis_message_list_key, json.dumps(
                            {"m_gmt_create": mes['m_gmt_create'], "m_to": mes['m_to']}))
            elif mode == 4:
                # 处理发布公告逻辑
                student_list = [2]
                notice_add = notice_add_interface(**data, u_id=m_from)
                if notice_add.p_id is None:
                    del notice_add.__dict__['p_id']
                if notice_add.ct_id is None:
                    del notice_add.__dict__['ct_id']
                await ws_manager.broadcast(notice_add.model_dump_json(), student_list)
                n_id, n_gmt_create = notice_model.add_notice(notice_add)
                notice_read_key = f"notice-{n_id}"
                notice_information = {'n_gmt_create': n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                                      'n_gmt_modified': n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                                      'u_id': m_from,
                                      'n_title': notice_add.n_title,
                                      'n_content': notice_add.n_content,
                                      'n_read_user': None}
                redis_client.set(notice_read_key, json.dumps(notice_information), 1 * 24 * 3600)
            elif mode == 5:
                # 处理修改公告逻辑
                notice_update = notice_update_interface(**data)
                notice_model.update_notice(notice_update)
                data.pop('n_id')
                notice_information = notice_add_interface(**data, u_id=m_from)
                student_list = [2]
                await ws_manager.broadcast(notice_information.model_dump_json(), student_list)


    except asyncio.TimeoutError:  # 无动作超时
        ws_manager.disconnect(m_from)
    except WebSocketDisconnect:  # 意外断开
        ws_manager.disconnect(m_from)
    except websockets.exceptions.ConnectionClosedOK:  # 主动断开
        ws_manager.disconnect(m_from)
