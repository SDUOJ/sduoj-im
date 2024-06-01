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
from type.functions import send_heartbeat, get_redis_message_key
from type.message import message_add_interface, message_receive_interface, message_get_interface
from type.notice import base_interface, notice_information_interface, notice_add_interface, notice_interface, \
    notice_update_interface
from utils.response import user_standard_response

ws_router = APIRouter()
message_model = MessageModel()
notice_model = NoticeModel()


@ws_router.websocket("/buildConnect/{m_from}")  # 建立websocket连接(注释掉的部分为判断已读未读)
async def connect_build(websocket: WebSocket, m_from: int):
    try:
        if m_from not in ws_manager.active_connections:  # 发送者刚上线
            await ws_manager.connect(websocket, m_from)
            redis_user_key = f'u-{m_from}'
            missed_msg_notice = redis_client.lrange(redis_user_key, 0, -1)
            redis_set = set()  # 用来去重
            if missed_msg_notice:  # 是否有错过的消息
                for missed in missed_msg_notice:
                    if missed in redis_set:
                        redis_client.lpop(redis_user_key)
                        continue
                    else:
                        redis_set.add(missed)
                    if missed.startswith('n'):
                        notice_information = json.loads(redis_client.get(missed))
                        send_thing = {'u_id': notice_information['u_id'], 'n_title': notice_information['n_title'],
                                      'n_gmt_create': notice_information['n_gmt_create']}
                        key_value = {'p_id': notice_information['p_id']} if 'p_id' in notice_information else {
                            'ct_id': notice_information['ct_id']}
                        send_thing.update(key_value)
                    else:
                        send_thing = json.loads(missed)
                    await ws_manager.send_personal_message(
                        json.dumps(send_thing),
                        ws_manager.active_connections[m_from])
                    redis_client.lpop(redis_user_key)
                redis_set.clear()

        asyncio.create_task(send_heartbeat(websocket))
        while True:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=1000)  # websocket过期时间
            mode = data['mode']  # 1为向他人发送消息; 2为发布公告; 3为修改公告
            data.pop('mode')
            if mode == 0:  # 建立连接
                pass
            elif mode == 1:
                # 处理消息发送逻辑
                # this_page = data["this_page"]  # 接收者是否在当前页查看消息
                # data.pop('this_page')
                redis_message_key = get_redis_message_key(m_from, data)
                data['m_from'] = m_from
                message_add = message_add_interface(**data)
                current_time, m_id = message_model.add_message(message_add)
                current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
                data["m_gmt_create"] = current_time
                m_to = data['m_to']
                data.pop('m_to')
                if message_add.m_to in ws_manager.active_connections:  # 如果接收者在线
                    await ws_manager.send_personal_message(
                        data,
                        ws_manager.active_connections[message_add.m_to])
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
                    redis_client.rpush(f'u-{m_to}', json.dumps(data))
                    redis_client.ltimeset(f'u-{m_to}', 1 * 24 * 3600)
                    # unread_key = f"p-{data['p_id']}-{m_from}-{data['m_to']}-{current_timestamp}" if 'p_id' in data else f"ct-{data['ct_id']}-{m_from}-{data['m_to']}-{current_timestamp}"
                    # unread_count = redis_client.get(unread_key)  # 查找未读消息数量
                    # if unread_count is None:
                    #     redis_client.set(unread_key, 1, 7 * 24 * 3600)
                    # else:
                    #     redis_client.set(unread_key, int(unread_count) + 1, 7 * 24 * 3600)
                # redis_client.rpush(redis_message_key, json.dumps(data))
                # redis_client.ltimeset(redis_message_key, 1 * 24 * 3600)

            elif mode == 2:
                # 处理发布公告逻辑
                student_list = [2]
                n_content = data['n_content']
                data['u_id'] = m_from
                notice_add = notice_add_interface(**data)
                n_id, n_gmt_create = notice_model.add_notice(notice_add)
                n_gmt_create = n_gmt_create.strftime('%Y-%m-%d %H:%M:%S')
                data['n_id'] = n_id
                data['n_gmt_create'] = n_gmt_create
                data.pop('n_content')
                await ws_manager.broadcast(data, student_list, n_id)
                notice_read_key = f"notice-{n_id}"
                key_value = {'p_id': data['p_id']} if 'p_id' in data else {
                    'ct_id': data['ct_id']}
                notice_information = {'n_gmt_create': n_gmt_create,
                                      'n_gmt_modified': n_gmt_create,
                                      'u_id': m_from,
                                      'n_title': notice_add.n_title,
                                      'n_content': n_content,
                                      'n_read_user': None}
                notice_information.update(key_value)

                redis_client.set(notice_read_key, json.dumps(notice_information), 1 * 24 * 3600)
            elif mode == 3:
                student_list = [2]
                # 处理修改公告逻辑
                notice_update = notice_update_interface(**data)
                timenow = notice_model.update_notice(notice_update)
                n_id = data['n_id']
                data.pop('n_id')
                notice_information = notice_add_interface(**data, u_id=m_from)
                if notice_information.p_id is None:
                    del notice_information.p_id
                if notice_information.ct_id is None:
                    del notice_information.ct_id
                await ws_manager.broadcast(notice_information.model_dump_json(), student_list, n_id)
                notice_read_key = f"notice-{n_id}"
                redis_value = redis_client.get(notice_read_key)
                key_value = {'p_id': data['p_id']} if 'p_id' in data else {
                    'ct_id': data['ct_id']}
                if redis_value is not None:
                    redis_notice = json.loads(redis_value)
                    notice_redis_information = {'n_gmt_create': redis_notice['n_gmt_create'],
                                                'n_gmt_modified': timenow,
                                                'u_id': m_from,
                                                'n_title': data["n_title"],
                                                'n_content': data["n_content"],
                                                'n_read_user': redis_notice['n_read_user']}
                    notice_redis_information.update(key_value)
                    redis_client.set(notice_read_key, json.dumps(notice_redis_information), 1 * 24 * 3600)
                else:
                    ans = notice_model.get_notice_by_n_id(n_id)
                    redis_client.set(notice_read_key, json.dumps(ans), ex=1 * 24 * 3600)


    except Exception as e:  # 所有异常
        ws_manager.disconnect(m_from)
    # except asyncio.TimeoutError:  # 无动作超时
    #     ws_manager.disconnect(m_from)
    # except WebSocketDisconnect:  # 意外断开
    #     ws_manager.disconnect(m_from)
    # except websockets.exceptions.ConnectionClosedOK:  # 主动断开
    #     ws_manager.disconnect(m_from)
