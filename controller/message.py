import copy
import json
from typing import Optional

from controller.websocket import WebSocketCustomException
from type.functions import judge_in_groups
from fastapi import APIRouter, Depends, HTTPException, WebSocketException
from sduojApi import getGroupMember
from model.redis_db import redis_client
from service.group import ContestExamModel
from service.message import MessageModel, MessageGroupModel
from type.message import message_group_add_interface
from type.notice import base_interface
from type.page import page
from utils.oj_authorization import oj_http_authorization
from utils.response import user_standard_response, makePageResult

message_router = APIRouter()
message_model = MessageModel()
message_group_model = MessageGroupModel()
contest_exam_model = ContestExamModel()
messageNum = 20


@message_router.get("/getMessage")  # 查看群聊聊天记录
@user_standard_response
async def message_get(mg_id: int, last_m_id: Optional[int] = None, user_information=Depends(oj_http_authorization)):
    # 处理查看消息逻辑
    m_from = user_information['userId']
    message_information = message_group_model.get_mg_by_id(mg_id)  # 找群组创建者，不存在即群不存在
    if message_information is None:
        raise HTTPException(status_code=404, detail='群聊组不存在')
    else:
        groups = user_information['groups']  # 查出用户所属组
        role_group_id = contest_exam_model.get_role_group(message_information.ct_id,
                                                          message_information.e_id)  # 判断用户是否在群聊组里
        if not role_group_id in groups and not message_information.build_u_id == m_from:  # 用户不在TA组内也不是发起答疑人
            raise WebSocketException(code=403, reason="用户不在当前群聊组内")
    redis_message_key = f"cache:messageGroup:{mg_id}"
    messages = []
    messages_json = []
    flag = 0
    if last_m_id is not None:  # 上次查看位置
        messages = redis_client.zrangebyscore(redis_message_key, int(last_m_id) + 1, '+inf', start=0,
                                              num=messageNum)
        messages_length = len(messages)
        if messages_length != 0:
            for msg in messages:
                msg_json = json.loads(msg)
                msg_json.pop('mg_id')
                messages_json.append(msg_json)
            if messages_length >= messageNum:
                flag = 1
            last_m_id = json.loads(messages[-1])['m_id']
    if not flag:
        messages = message_model.get_message(mg_id, messageNum - len(messages), last_m_id)
        for mes in messages:
            tempt = {"m_gmt_create": mes[3].strftime('%Y-%m-%d %H:%M:%S'), "m_from": mes[0],
                     "m_id": mes[1], "m_content": mes[2]}
            tempt_dcopy = copy.deepcopy(tempt)
            messages_json.append(tempt_dcopy)
            tempt['mg_id'] = mg_id
            redis_client.zadd(redis_message_key, {json.dumps(tempt): mes[1]})
        redis_client.expire(redis_message_key, 1 * 24 * 3600)
    return {'message': '信息读取成功', 'data': messages_json, 'code': 0}


@message_router.get("/viewMessage")  # 查看自己的提问(群聊)
@user_standard_response
async def message_view(e_id: Optional[int] = None, ct_id: Optional[int] = None,
                       user_information=Depends(oj_http_authorization)):
    # 处理查看提问列表逻辑
    m_from = user_information['userId']
    data = {'e_id': e_id} if e_id is not None else {'ct_id': ct_id}
    redis_message_list_value = []
    # redis_message_list_key = f"cache:messageLists:e:{data['e_id']}-{m_from}" if 'e_id' in data else f"cache:messageLists:ct-{data['ct_id']}-{m_from}"
    # all_data = redis_client.hgetall(redis_message_list_key)
    # if all_data:
    #     for key, value in all_data.items():
    #         value = json.loads(value)
    #         redis_message_list_value.append(
    #             {'m_last_content': value['m_last_content'], 'mg_id': key, 'm_gmt_create': value['m_gmt_create']})
    # else:
    base = base_interface.model_validate(data)
    redis_message_list_value = message_model.get_message_list(m_from, base)
    # for mes in redis_message_list_value:
    #     redis_client.hset(redis_message_list_key, mes['mg_id'], json.dumps(
    #         {"m_last_content": mes['m_last_content'], "m_gmt_create": mes['m_gmt_create'], "mg_id": mes['mg_id']}))
    # redis_client.expire(redis_message_list_key, 7200)
    return {'message': '查看信息成功', 'data': redis_message_list_value, 'code': 0}


@message_router.post("/addMessageGroup")  # 创建群聊组(用户点击提问)
@user_standard_response
async def message_group_add(mg_add: base_interface, user_information=Depends(oj_http_authorization)):
    try:
        u_id = user_information['userId']
        groups = user_information['groups']  # 查出用户所属组
        await judge_in_groups(mg_add.ct_id, mg_add.e_id, groups)  # 鉴权
        mg_id = message_group_model.add_message_group(
            message_group_add_interface(ct_id=mg_add.ct_id, u_id=u_id, e_id=mg_add.e_id))
        role_group_id = contest_exam_model.get_role_group(mg_add.ct_id, mg_add.e_id)[0]
        managers = getGroupMember(role_group_id)
        redis_client.set(f"cache:messageGroupMember:{mg_id}", json.dumps(managers), ex=9000)
        result = {'mg_id': mg_id, 'members': managers}
    except Exception as e:
        raise HTTPException(status_code=409, detail="创建失败，资源冲突")
    return {'message': '创建群聊组成功', 'data': result, 'code': 0}

# @message_router.get("/getMessage")  # 查看与某人的消息(私聊)
# @user_standard_response
# async def message_get(m_to: int, last_m_id: Optional[int] = None,
#                       e_id: Optional[int] = None, ct_id: Optional[int] = None, user_information=Depends(oj_authorization)):
#     # 处理查看消息逻辑
#     m_from = user_information['userId']
#     data = {'m_to': m_to, 'e_id': e_id} if e_id is not None else {'m_to': m_to, 'ct_id': ct_id}
#     redis_message_key = get_redis_message_key(m_from, data)
#     messages = []
#     messages_json = []
#     flag = 0
#     if last_m_id is not None:  # 上次查看位置
#         messages = redis_client.zrangebyscore(redis_message_key, int(last_m_id)+1, '+inf', start=0,
#                                               num=messageNum)
#         messages_length = len(messages)
#         if messages_length != 0:
#             for msg in messages:
#                 msg_json = json.loads(msg)
#                 if 'e_id' in msg_json:
#                     msg_json.pop('e_id')
#                 elif 'ct_id' in msg_json:
#                     msg_json.pop('ct_id')
#                 messages_json.append(msg_json)
#             if messages_length >= messageNum:
#                 flag = 1
#             last_m_id = json.loads(messages[-1])['m_id']
#     if not flag:
#         message = message_get_interface.model_validate(data)
#         messages = message_model.get_message(m_from, messageNum - len(messages), message, last_m_id)
#         for mes in messages:
#             tempt = {"m_gmt_create": mes[3].strftime('%Y-%m-%d %H:%M:%S'), "m_from": mes[0],
#                      "m_id": mes[1]}
#             tempt_dcopy = copy.deepcopy(tempt)
#             messages_json.append(tempt_dcopy)
#             if 'e_id' in data:
#                 tempt["e_id"] = data['e_id']
#             elif 'ct_id' in data:
#                 tempt["ct_id"] = data['ct_id']
#             redis_client.zadd(redis_message_key, {json.dumps(tempt): mes[1]})
#         redis_client.expire(redis_message_key, 1 * 24 * 3600)
#     return {'message': '信息读取成功', 'data': messages_json, 'code': 0}


# @message_router.get("/viewMessage")  # 查看自己的提问(私聊)
# @user_standard_response
# async def message_view(e_id: Optional[int] = None, ct_id: Optional[int] = None,
#                        user_information=Depends(oj_authorization)):
#     # 处理查看提问列表逻辑
#     m_from = user_information['userId']
#     data = {'e_id': e_id} if e_id is not None else {'ct_id': ct_id}
#     redis_message_list_value = []
#     redis_message_list_key = f"cache:messageLists:p:{data['e_id']}-{m_from}" if 'e_id' in data else f"cache:messageLists:ct-{data['ct_id']}-{m_from}"
#     all_data = redis_client.hgetall(redis_message_list_key)
#     if all_data:
#         for key, value in all_data.items():
#             value = json.loads(value)
#             redis_message_list_value.append(
#                 {'m_last_content': value['m_last_content'], 'm_to': key, 'm_gmt_create': value['m_gmt_create']})
#     else:
#         base = base_interface.model_validate(data)
#         redis_message_list_value = message_model.get_message_list(m_from, base)
#         for mes in redis_message_list_value:
#             redis_client.hset(redis_message_list_key, mes['m_to'], json.dumps(
#                 {"m_last_content": mes['m_last_content'], "m_gmt_create": mes['m_gmt_create']}))
#     return {'message': '查看信息成功', 'data': redis_message_list_value, 'code': 0}


# @message_router.get("/getManager")  # 查看某用户组组长信息
# @user_standard_response
# async def Manager_get():
#
