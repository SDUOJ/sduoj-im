import asyncio
import json

from fastapi import APIRouter, WebSocketException, Depends
from fastapi import WebSocket

from auth import is_role_member, cover_header, is_admin
from model.redis_db import redis_client
from model.websocket import ws_manager
from sduojApi import getUserId
from service.group import ContestExamModel
from service.message import MessageModel, MessageGroupModel
from service.notice import NoticeModel
from type.functions import send_heartbeat, get_group_student, get_message_group_members
from type.message import message_add_interface, message_receive_interface
from type.notice import notice_add_interface, notice_update_interface


class WebSocketCustomException(Exception):
    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason


ws_router = APIRouter()
message_model = MessageModel()
message_group_model = MessageGroupModel()
notice_model = NoticeModel()
contest_exam_model = ContestExamModel()


@ws_router.websocket("/buildConnect")  # 建立websocket连接(注释掉的部分为判断已读未读)
async def connect_build(websocket: WebSocket, SDUOJUserInfo=Depends(cover_header)):
    m_username = SDUOJUserInfo["username"]
    try:
        if m_username not in ws_manager.active_connections:  # 发送者刚上线
            await ws_manager.connect(websocket, m_username)
            m_from = await getUserId(m_username)
            redis_user_key = f'cache:unreadUsers:{m_from}'
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
                        missed_notice_id = missed.split('-')[1]
                        notice_information = json.loads(redis_client.get(f'cache:notices:{missed_notice_id}'))
                        # notice_information.pop('nt_content')
                        notice_information['nt_id'] = missed_notice_id
                        send_thing = notice_information
                    else:
                        missed_message = missed.split('-')
                        unsend_message = redis_client.zrangebyscore('cache:messageGroup:1', 33, 33, 0, 1)
                        if unsend_message:
                            send_thing = json.loads(unsend_message[0])
                            send_thing.pop('m_id')
                        else:
                            send_thing = message_model.get_message_by_id(int(missed_message[1]))
                    await ws_manager.send_personal_message(
                        json.dumps(send_thing),
                        ws_manager.active_connections[m_from])
                    redis_client.lpop(redis_user_key)
                redis_set.clear()

        asyncio.create_task(send_heartbeat(websocket))
        while True:
            m_from = await getUserId(m_username)
            data = await asyncio.wait_for(websocket.receive_json(), timeout=10000)  # websocket过期时间
            mode = data['mode']  # 1为向他人发送消息; 2为发布公告; 3为修改公告
            data.pop('mode')
            # 鉴权
            message_information = message_group_model.get_mg_by_id(data['mg_id'])  # 找群组创建者，不存在即群不存在
            if message_information is None:
                raise WebSocketCustomException(code=404, reason="Not find")
            else:
                groups = SDUOJUserInfo['groups']  # 查出用户所属组
                role_group_id = contest_exam_model.get_role_group(message_information.ct_id,
                                                                  message_information.e_id)  # 判断用户是否在群聊组里
                if not is_role_member(role_group_id,
                                      groups) and not message_information.build_u_id == m_from and not is_admin(
                    SDUOJUserInfo):  # 用户不在TA组内也不是发起答疑人
                    raise WebSocketException(code=403, reason="Permission Denial")
            if mode == 1:
                # 处理消息发送逻辑
                message_add = message_receive_interface(**data)
                current_time, m_id = message_model.add_message(
                    message_add_interface(m_content=message_add.m_content, u_id=m_from, mg_id=message_add.mg_id))
                current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
                data["m_gmt_create"] = current_time
                data['m_from'] = m_from
                data['m_id'] = m_id
                redis_message_key = f"cache:messageGroup:{data['mg_id']}"
                redis_client.zadd(redis_message_key, {json.dumps(data): m_id})
                redis_client.ltimeset(redis_message_key, 3 * 3600)
                data.pop('m_id')
                members = await get_message_group_members(role_group_id, message_information.u_id,
                                                          data['mg_id'],
                                                          is_role_member(role_group_id, groups))  # 获取全部成员
                await ws_manager.broadcast(0, json.dumps(data), members, m_id, m_from, data['mg_id'])

            elif mode == 2:
                # 处理发布公告逻辑
                if not is_role_member(role_group_id,groups) and not is_admin(SDUOJUserInfo):  # 用户不在TA组内,无权限发布公告
                    raise WebSocketException(code=403, reason="用户无权限")
                student_list = await get_group_student(data['ct_id'], data['e_id'])
                nt_content = data['nt_content']
                data['u_id'] = m_from
                notice_add = notice_add_interface(**data)
                nt_id, nt_gmt_create = notice_model.add_notice(notice_add)
                nt_gmt_create = nt_gmt_create.strftime('%Y-%m-%d %H:%M:%S')
                data['nt_id'] = nt_id
                data['nt_gmt_create'] = nt_gmt_create
                data['nt_gmt_modified'] = nt_gmt_create
                # data.pop('nt_content')
                await ws_manager.broadcast(1, data, student_list, nt_id)
                notice_read_key = f'cache:notices:{nt_id}'
                key_value = {'e_id': data['e_id']} if 'e_id' in data else {
                    'ct_id': data['ct_id']}
                notice_information = {'nt_gmt_create': nt_gmt_create,
                                      'nt_gmt_modified': nt_gmt_create,
                                      'u_id': m_from,
                                      'nt_title': notice_add.nt_title,
                                      'nt_content': nt_content}
                notice_information.update(key_value)
                redis_client.set(notice_read_key, json.dumps(notice_information), 1 * 24 * 3600)
            elif mode == 3:
                if not is_role_member(role_group_id,groups) and not is_admin(SDUOJUserInfo):  # 用户不在TA组内,无权限发布公告
                    raise WebSocketException(code=403, reason="用户无权限")
                student_list = await get_group_student(data['ct_id'], data['e_id'])
                # 处理修改公告逻辑
                notice_update = notice_update_interface(**data)
                timenow = notice_model.update_notice(notice_update)
                # data.pop('nt_id')
                notice_key = f'cache:notices:{data['nt_id']}'
                redis_value = redis_client.get(notice_key)
                if redis_value is not None:
                    redis_notice = json.loads(redis_value)
                    redis_notice['nt_gmt_modified'] = timenow
                    redis_notice['nt_content'] = data['nt_content']
                    redis_notice['nt_title'] = data['nt_title']
                    redis_notice['nt_id'] = data['nt_id']
                    redis_client.set(notice_key, json.dumps(redis_notice), ex=1 * 24 * 3600)
                else:
                    redis_notice = notice_model.get_notice_by_nt_id(data['nt_id'])
                    redis_client.set(notice_key, json.dumps(redis_notice), ex=1 * 24 * 3600)
                # redis_notice.pop('nt_content')
                await ws_manager.broadcast(1, json.dumps(redis_notice), student_list, data['nt_id'])
    except WebSocketCustomException as e:  # 自定义抛出异常
        error_message = json.dumps({"code": e.code, "reason": e.reason})
        await websocket.send_text(f"Error: {error_message}")
    except Exception as e:  # 所有异常
        ws_manager.disconnect(m_username)

    # except asyncio.TimeoutError:  # 无动作超时
    #     ws_manager.disconnect(m_from)
    # except WebSocketDisconnect:  # 意外断开
    #     ws_manager.disconnect(m_from)
    # except websockets.exceptions.ConnectionClosedOK:  # 主动断开
    #     ws_manager.disconnect(m_from)

#   私聊逻辑
# @ws_router.websocket("/buildConnect")  # 建立websocket连接(注释掉的部分为判断已读未读)
# async def connect_build(websocket: WebSocket, user_information=Depends(oj_websocket_authorization)):
#     m_from = user_information['userId']
#     try:
#
#         if m_from not in ws_manager.active_connections:  # 发送者刚上线
#             await ws_manager.connect(websocket, m_from)
#             redis_user_key = f'cache:unreadUsers:{m_from}'
#             missed_msg_notice = redis_client.lrange(redis_user_key, 0, -1)
#             redis_set = set()  # 用来去重
#             if missed_msg_notice:  # 是否有错过的消息
#                 for missed in missed_msg_notice:
#                     if missed in redis_set:
#                         redis_client.lpop(redis_user_key)
#                         continue
#                     else:
#                         redis_set.add(missed)
#                     if missed.startswith('n'):
#                         missed_notice_id = missed.split('-')[1]
#                         notice_information = json.loads(redis_client.get(f'cache:notices:{missed_notice_id}'))
#                         notice_information.pop('nt_content')
#                         notice_information['nt_id'] = missed_notice_id
#                         send_thing = notice_information
#                     else:
#                         missed_message = missed.split('%')
#                         unsend_message = redis_client.zrange(missed_message[0], int(missed_message[1]),
#                                                              int(missed_message[1]))
#                         if unsend_message:  # 似乎多余
#                             send_thing = json.loads(unsend_message[0])
#                         else:
#                             send_thing = message_model.get_message_by_id(int(missed_message[1]))
#                     await ws_manager.send_personal_message(
#                         json.dumps(send_thing),
#                         ws_manager.active_connections[m_from])
#                     redis_client.lpop(redis_user_key)
#                 redis_set.clear()
#
#         asyncio.create_task(send_heartbeat(websocket))
#         while True:
#             data = await asyncio.wait_for(websocket.receive_json(), timeout=1000)  # websocket过期时间
#             mode = data['mode']  # 1为向他人发送消息; 2为发布公告; 3为修改公告
#             data.pop('mode')
#             if mode == 0:  # 建立连接
#                 pass
#             elif mode == 1:
#                 # 处理消息发送逻辑
#                 # this_page = data["this_page"]  # 接收者是否在当前页查看消息
#                 # data.pop('this_page')
#                 redis_message_key = get_redis_message_key(m_from, data)
#                 data['m_from'] = m_from
#                 message_add = message_add_interface(**data)
#                 current_time, m_id = message_model.add_message(message_add)
#                 current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
#                 data["m_gmt_create"] = current_time
#                 m_to = data['m_to']
#                 data.pop('m_to')
#                 if message_add.m_to in ws_manager.active_connections:  # 如果接收者在线
#                     await ws_manager.send_personal_message(
#                         data,
#                         ws_manager.active_connections[message_add.m_to])
#                     # if this_page:
#                     #     unread_key = f"p-{data['e_id']}-{m_from}-{data['m_to']}-{current_timestamp}" if 'e_id' in data else f"ct-{data['ct_id']}-{m_from}-{data['m_to']}-{current_timestamp}"
#                     #     if 'e_id' not in data:
#                     #         await ws_manager.send_personal_message(
#                     #             json.dumps(
#                     #                 {"mode": 0, "time": current_timestamp, "m_to": data['m_to'], "ct_id": data['ct_id']}),
#                     #             websocket)
#                     #     else:
#                     #         await ws_manager.send_personal_message(
#                     #             json.dumps(
#                     #                 {"mode": 0, "time": current_timestamp, "m_to": data['m_to'], "e_id": data['e_id']}),
#                     #             websocket)
#                     #     redis_client.set(unread_key, 1, 1 * 24 * 3600)
#                 else:  # 接收者不在线
#                     redis_message_key = redis_message_key + '%' + str(m_id)
#                     redis_client.rpush(f'cache:unreadUsers:{m_to}', redis_message_key)
#                     redis_client.ltimeset(f'cache:unreadUsers:{m_to}', 1 * 24 * 3600)
#                     # unread_key = f"p-{data['e_id']}-{m_from}-{data['m_to']}-{current_timestamp}" if 'e_id' in data else f"ct-{data['ct_id']}-{m_from}-{data['m_to']}-{current_timestamp}"
#                     # unread_count = redis_client.get(unread_key)  # 查找未读消息数量
#                     # if unread_count is None:
#                     #     redis_client.set(unread_key, 1, 7 * 24 * 3600)
#                     # else:
#                     #     redis_client.set(unread_key, int(unread_count) + 1, 7 * 24 * 3600)
#                 # redis_client.rpush(redis_message_key, json.dumps(data))
#                 # redis_client.ltimeset(redis_message_key, 1 * 24 * 3600)
#                 # redis_message_list_key = f"cache:messageLists:p:{data['e_id']}-{m_from}" if 'e_id' in data else f"cache:messageLists:ct-{data['ct_id']}-{m_from}"
#                 # redis_client.hset(redis_message_list_key, m_to, json.dumps({"m_gmt_create": current_time}))
#             elif mode == 2:
#                 # 处理发布公告逻辑
#                 student_list = [2]
#                 nt_content = data['nt_content']
#                 data['u_id'] = m_from
#                 notice_add = notice_add_interface(**data)
#                 nt_id, nt_gmt_create = notice_model.add_notice(notice_add)
#                 nt_gmt_create = nt_gmt_create.strftime('%Y-%m-%d %H:%M:%S')
#                 data['nt_id'] = nt_id
#                 data['nt_gmt_create'] = nt_gmt_create
#                 data['nt_gmt_modified'] = nt_gmt_create
#                 data.pop('nt_content')
#                 await ws_manager.broadcast(data, student_list, nt_id)
#                 notice_read_key = f'cache:notices:{nt_id}'
#                 key_value = {'e_id': data['e_id']} if 'e_id' in data else {
#                     'ct_id': data['ct_id']}
#                 notice_information = {'nt_gmt_create': nt_gmt_create,
#                                       'nt_gmt_modified': nt_gmt_create,
#                                       'u_id': m_from,
#                                       'nt_title': notice_add.nt_title,
#                                       'nt_content': nt_content}
#                 notice_information.update(key_value)
#                 redis_client.set(notice_read_key, json.dumps(notice_information), 1 * 24 * 3600)
#             elif mode == 3:
#                 student_list = [2]
#                 # 处理修改公告逻辑
#                 notice_update = notice_update_interface(**data)
#                 timenow = notice_model.update_notice(notice_update)
#                 nt_id = data['nt_id']
#                 data.pop('nt_id')
#                 notice_key = f'cache:notices:{nt_id}'
#                 redis_value = redis_client.get(notice_key)
#                 if redis_value is not None:
#                     redis_notice = json.loads(redis_value)
#                     redis_notice['nt_gmt_modified'] = timenow
#                     redis_notice['nt_content'] = data['nt_content']
#                     redis_notice['nt_title'] = data['nt_title']
#                     redis_client.set(notice_key, json.dumps(redis_notice), ex=1 * 24 * 3600)
#                 else:
#                     redis_notice = notice_model.get_notice_by_nt_id(nt_id)
#                     redis_client.set(notice_key, json.dumps(redis_notice), ex=1 * 24 * 3600)
#                 redis_notice.pop('nt_content')
#                 await ws_manager.broadcast(json.dumps(redis_notice), student_list, nt_id)
#     except Exception as e:  # 所有异常
#         ws_manager.disconnect(m_from)
#     # except asyncio.TimeoutError:  # 无动作超时
#     #     ws_manager.disconnect(m_from)
#     # except WebSocketDisconnect:  # 意外断开
#     #     ws_manager.disconnect(m_from)
#     # except websockets.exceptions.ConnectionClosedOK:  # 主动断开
#     #     ws_manager.disconnect(m_from)
