import copy
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import cover_header, is_admin, is_role_member, judge_in_groups
from model.redis_db import redis_client
from sduojApi import getUserId, getGroupMember
from service.websocket import ContestExamModel
from service.message import MessageModel, MessageGroupModel, MessageUserModel
from type.functions import get_message_group_members
from type.message import message_group_add_interface
from type.notice import base_interface
from utils.response import user_standard_response

message_router = APIRouter()
message_model = MessageModel()
message_group_model = MessageGroupModel()
message_user_model = MessageUserModel()
contest_exam_model = ContestExamModel()
messageNum = 20


@message_router.get("/getMessage")  # 查看群聊聊天记录
@user_standard_response
async def message_get(mg_id: int, last_m_id: Optional[int] = None, SDUOJUserInfo=Depends(cover_header)):
    # 处理查看消息逻辑
    message_information = message_group_model.get_mg_by_id(mg_id, 0)  # 找群组创建者，不存在即群不存在
    role_group_id = contest_exam_model.get_role_group(message_information.ct_id,
                                                      message_information.e_id)  # 判断用户是否在群聊组里
    if not message_information.username == SDUOJUserInfo["username"] and not is_admin(
            SDUOJUserInfo) and not is_role_member(role_group_id, SDUOJUserInfo["groups"]):  # 用户不在TA组内也不是发起答疑人也不是管理
        raise HTTPException(detail="Permission Denial", status_code=403)
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
            tempt = {"m_gmt_create": mes[3].strftime('%Y-%m-%d %H:%M:%S'), "username": mes[0],
                     "m_id": mes[1], "m_content": mes[2]}
            tempt_dcopy = copy.deepcopy(tempt)
            messages_json.append(tempt_dcopy)
            tempt['mg_id'] = mg_id
            redis_client.zadd(redis_message_key, {json.dumps(tempt): mes[1]})
            last_m_id = mes[1]
        redis_client.expire(redis_message_key, 1 * 24 * 3600)
    message_user_model.add_message_users(SDUOJUserInfo["username"], last_m_id)
    return {'message': '信息读取成功', 'data': messages_json, 'code': 0}


@message_router.get("/viewMessage")  # 查看自己的群聊（学生看自己的，TA和admin看所有的）
@user_standard_response
async def message_view(e_id: Optional[int] = None, ct_id: Optional[int] = None,
                       SDUOJUserInfo=Depends(cover_header)):
    # 处理查看提问列表逻辑
    role_group_id = contest_exam_model.get_role_group(ct_id, e_id)
    is_TA_admin = await judge_in_groups(ct_id, e_id, SDUOJUserInfo['groups'], SDUOJUserInfo,
                                        role_group_id)  # 鉴权(组里成员和admin和TA都可以)
    data = {'e_id': e_id} if e_id is not None else {'ct_id': ct_id}
    base = base_interface.model_validate(data)
    message_list_value = message_model.get_message_list(SDUOJUserInfo['username'], base, is_TA_admin)
    for message_list in message_list_value:
        members = await get_message_group_members(role_group_id, SDUOJUserInfo['username'], message_list['mg_id'])
        message_list['members'] = members
    return {'message': '查看信息成功', 'data': message_list_value, 'code': 0}


@message_router.post("/addMessageGroup")  # 创建群聊组(用户点击提问)
@user_standard_response
async def message_group_add(mg_add: base_interface,
                            SDUOJUserInfo=Depends(cover_header)):
    role_group_id = contest_exam_model.get_role_group(mg_add.ct_id, mg_add.e_id)
    await judge_in_groups(mg_add.ct_id, mg_add.e_id, SDUOJUserInfo['groups'], SDUOJUserInfo, role_group_id, 1)  # 鉴权,组里普通成员可以但是admin与TA不可以
    exist_mg_id = message_group_model.get_mg_id(mg_add)
    if exist_mg_id is not None:
        return {'message': '群聊组已存在', 'data': {'mg_id': exist_mg_id[0]}, 'code': 0}
    mg_id = message_group_model.add_message_group(
        message_group_add_interface(ct_id=mg_add.ct_id, username=SDUOJUserInfo["username"], e_id=mg_add.e_id))
    members = await get_message_group_members(role_group_id, SDUOJUserInfo["username"], mg_id)  # 获取全部成员
    result = {'mg_id': mg_id, 'members': members}
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
