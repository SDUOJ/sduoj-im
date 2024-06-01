import json
from typing import Optional

from fastapi import APIRouter

from model.redis_db import redis_client
from service.message import MessageModel
from type.functions import get_redis_message_key
from type.message import message_get_interface
from type.notice import base_interface
from utils.response import user_standard_response

message_router = APIRouter()
message_model = MessageModel()


@message_router.get("/getMessage")  # 查看与某人的消息
@user_standard_response
async def message_get(m_to: int, p_id: Optional[int] = None, ct_id: Optional[int] = None):
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
    m_from = 1
    data = {'m_to': m_to, 'p_id': p_id} if p_id is not None else {'m_to': m_to, 'ct_id': ct_id}
    redis_message_key = get_redis_message_key(m_from, data)
    redis_message_value = redis_client.lrange(redis_message_key, 0, -1)
    if redis_message_value:
        redis_message_json = [json.loads(json_string) for json_string in redis_message_value]
    else:
        message = message_get_interface.model_validate(data)
        messages = message_model.get_message(m_from, message)
        redis_message_json = messages
        for mes in messages:
            if 'p_id' in data:
                redis_client.rpush(redis_message_key, json.dumps(
                    {"m_gmt_create": mes['m_gmt_create'], "m_from": mes['m_from'], "p_id": data['p_id']}))
            elif 'ct_id' in data:
                redis_client.rpush(redis_message_key, json.dumps(
                    {"m_gmt_create": mes['m_gmt_create'], "m_from": mes['m_from'], "ct_id": data['ct_id']}))
        redis_client.ltimeset(redis_message_key, 1 * 24 * 3600)

    return {'message': '信息读取成功', 'data': redis_message_json, 'code': 0}


@message_router.get("/viewMessage")  # 查看自己的提问
@user_standard_response
async def message_view(p_id: Optional[int] = None, ct_id: Optional[int] = None):
    # 处理查看提问列表逻辑
    m_from = 1
    data = {'p_id': p_id} if p_id is not None else {'ct_id': ct_id}
    redis_message_list_key = f"list-p-{data['p_id']}-{m_from}" if 'p_id' in data else f"list-ct-{data['ct_id']}-{m_from}"
    redis_message_list_value = redis_client.lrange(redis_message_list_key, 0, -1)
    if not redis_message_list_value:
        base = base_interface.model_validate(data)
        redis_message_list_value = message_model.get_message_list(m_from, base)
        for mes in redis_message_list_value:
            redis_client.lpush(redis_message_list_key, json.dumps(
                {"m_gmt_create": mes['m_gmt_create'], "m_to": mes['m_to']}))
    return {'message': '查看信息成功', 'data': redis_message_list_value, 'code': 0}
