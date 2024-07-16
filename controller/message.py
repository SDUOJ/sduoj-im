import copy
import json
from typing import Optional

from fastapi import APIRouter, Depends

from model.redis_db import redis_client
from service.message import MessageModel
from type.functions import get_redis_message_key
from type.message import message_get_interface
from type.notice import base_interface
from type.page import page
from utils.oj_authorization import oj_authorization
from utils.response import user_standard_response, makePageResult

message_router = APIRouter()
message_model = MessageModel()
messageNum = 20


@message_router.get("/getMessage")  # 查看与某人的消息
@user_standard_response
async def message_get(m_to: int, last_m_id: Optional[int] = None,
                      p_id: Optional[int] = None, ct_id: Optional[int] = None, user_information=Depends(oj_authorization)):
    # 处理查看消息逻辑
    m_from = user_information['userId']
    data = {'m_to': m_to, 'p_id': p_id} if p_id is not None else {'m_to': m_to, 'ct_id': ct_id}
    redis_message_key = get_redis_message_key(m_from, data)
    messages = []
    messages_json = []
    flag = 0
    if last_m_id is not None:  # 上次查看位置
        messages = redis_client.zrangebyscore(redis_message_key, int(last_m_id)+1, '+inf', start=0,
                                              num=messageNum)
        messages_length = len(messages)
        if messages_length != 0:
            for msg in messages:
                msg_json = json.loads(msg)
                if 'p_id' in msg_json:
                    msg_json.pop('p_id')
                elif 'ct_id' in msg_json:
                    msg_json.pop('ct_id')
                messages_json.append(msg_json)
            if messages_length >= messageNum:
                flag = 1
            last_m_id = json.loads(messages[-1])['m_id']
    if not flag:
        message = message_get_interface.model_validate(data)
        messages = message_model.get_message(m_from, messageNum - len(messages), message, last_m_id)
        for mes in messages:
            tempt = {"m_gmt_create": mes[3].strftime('%Y-%m-%d %H:%M:%S'), "m_from": mes[0],
                     "m_id": mes[1]}
            tempt_dcopy = copy.deepcopy(tempt)
            messages_json.append(tempt_dcopy)
            if 'p_id' in data:
                tempt["p_id"] = data['p_id']
            elif 'ct_id' in data:
                tempt["ct_id"] = data['ct_id']
            redis_client.zadd(redis_message_key, {json.dumps(tempt): mes[1]})
        redis_client.expire(redis_message_key, 1 * 24 * 3600)
    return {'message': '信息读取成功', 'data': messages_json, 'code': 0}


@message_router.get("/viewMessage")  # 查看自己的提问
@user_standard_response
async def message_view(p_id: Optional[int] = None, ct_id: Optional[int] = None,
                       user_information=Depends(oj_authorization)):
    # 处理查看提问列表逻辑
    m_from = user_information['userId']
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



# @message_router.get("/getManager")  # 查看某用户组组长信息
# @user_standard_response
# async def Manager_get():
#