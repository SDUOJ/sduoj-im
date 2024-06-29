import json
from typing import Optional

from fastapi import APIRouter

from model.redis_db import redis_client
from service.message import MessageModel
from type.functions import get_redis_message_key
from type.message import message_get_interface
from type.notice import base_interface
from type.page import page
from utils.response import user_standard_response, makePageResult

message_router = APIRouter()
message_model = MessageModel()


@message_router.get("/getMessage")  # 查看与某人的消息
@user_standard_response
async def message_get(m_to: int, pageNow: int, pageSize: int, last_m_id: Optional[int] = None,
                      p_id: Optional[int] = None, ct_id: Optional[int] = None):
    # 处理查看消息逻辑
    m_from = 1
    Page = page(pageSize=pageSize, pageNow=pageNow)
    data = {'m_to': m_to, 'p_id': p_id} if p_id is not None else {'m_to': m_to, 'ct_id': ct_id}
    redis_message_key = get_redis_message_key(m_from, data)
    messages = []
    if not redis_client.zcard(redis_message_key) < pageSize:  # redis中数据少于能分页的，从数据库里查
        if last_m_id is not None:
            messages = redis_client.zrangebyscore(redis_message_key, int(last_m_id), '+inf', start=0, num=pageSize)
        else:
            messages = redis_client.zrange(redis_message_key, 1, pageSize, withscores=False)
    if len(messages) >= pageSize:
        messages_json = [json.loads(msg) for msg in messages]
        counts = int(redis_client.zrange(redis_message_key, 0, 0)[0])
    else:
        message = message_get_interface.model_validate(data)
        messages, counts = message_model.get_message(m_from, Page, message, last_m_id)
        messages_json = []
        redis_client.zremrangebyscore(redis_message_key, 0)
        redis_client.zadd(redis_message_key, {str(counts): 0})
        for mes in messages:
            if 'p_id' in data:
                tempt = {"m_gmt_create": mes[3].strftime('%Y-%m-%d %H:%M:%S'), "m_from": mes[0],
                         "p_id": data['p_id'], "m_id": mes[1]}
            elif 'ct_id' in data:
                tempt = {"m_gmt_create": mes[3].strftime('%Y-%m-%d %H:%M:%S'), "m_from": mes[0],
                         "ct_id": data['p_id'], "m_id": mes[1]}
            messages_json.append(tempt)
            redis_client.zadd(redis_message_key, {json.dumps(tempt): mes[1]})
        redis_client.expire(redis_message_key, 1 * 24 * 3600)
    result = makePageResult(Page, counts, messages_json)
    return {'message': '信息读取成功', 'data': result, 'code': 0}


@message_router.get("/viewMessage")  # 查看自己的提问
@user_standard_response
async def message_view(p_id: Optional[int] = None, ct_id: Optional[int] = None):
    # 处理查看提问列表逻辑
    m_from = 1
    data = {'p_id': p_id} if p_id is not None else {'ct_id': ct_id}
    redis_message_list_value = []
    redis_message_list_key = f"cache:messageLists:p:{data['p_id']}-{m_from}" if 'p_id' in data else f"cache:messageLists:ct-{data['ct_id']}-{m_from}"
    all_data = redis_client.hgetall(redis_message_list_key)
    if all_data:
        for key, value in all_data.items():
            value = json.loads(value)
            redis_message_list_value.append(
                {'m_last_content': value['m_last_content'], 'm_to': key, 'm_gmt_create': value['m_gmt_create']})
    else:
        base = base_interface.model_validate(data)
        redis_message_list_value = message_model.get_message_list(m_from, base)
        for mes in redis_message_list_value:
            redis_client.hset(redis_message_list_key, mes['m_to'], json.dumps(
                {"m_last_content": mes['m_last_content'], "m_gmt_create": mes['m_gmt_create']}))
    return {'message': '查看信息成功', 'data': redis_message_list_value, 'code': 0}
