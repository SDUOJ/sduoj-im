import asyncio
import json
import uuid
from typing import Dict

from fastapi import APIRouter, WebSocketException, Depends
from fastapi import WebSocket

from auth import is_role_member, cover_header, is_admin, judge_in_groups
from model.redis_db import redis_client
from sduojApi import getUserId, getUserInformation
from service.websocket import ContestExamModel, WebsocketModel, MissedModel
from service.message import MessageModel, MessageGroupModel, MessageUserModel
from service.notice import NoticeModel
from type.functions import send_heartbeat, get_group_student, get_message_group_members, dict_pop
from type.message import message_add_interface, message_receive_interface
from type.notice import notice_add_interface, notice_update_interface
from utils.response import user_standard_response
from type.websocket import websocket_add_interface, missed_add_interface

ws_router = APIRouter()
message_model = MessageModel()
message_group_model = MessageGroupModel()
message_user_model = MessageUserModel()
notice_model = NoticeModel()
contest_exam_model = ContestExamModel()
websocket_model = WebsocketModel()
missed_model = MissedModel()


class WSConnectionManager:
    def __init__(self):
        # 存放激活的ws连接对象
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, username: str):
        # 等待连接
        await ws.accept()
        # 存储ws连接对象
        self.active_connections[username] = ws

    def disconnect(self, username: str):
        # 关闭时 移除ws对象
        if username in self.active_connections:
            del self.active_connections[username]

    @staticmethod
    async def send_personal_message(message, ws: WebSocket):
        # 发送个人消息
        if type(message) != str:
            await ws.send_json(message)
        else:
            await ws.send_text(message)

    async def broadcast(self, mode: int, message, u_list: list, project_id: int = None, m_username: str = None,
                        mg_id: int = None, group_build: int = 0):
        # 广播通知
        for user in u_list:
            if 'build_username' in user:
                continue
            username = user['username']
            if username == m_username:
                continue
            if username in ws_manager.active_connections:
                if type(message) == str:
                    await self.active_connections[username].send_text(message)
                else:
                    await self.active_connections[username].send_json(message)
            else:
                if group_build == 0:
                    try:
                        if mode == 0:
                            ms_id = missed_model.add_missed(
                                missed_add_interface(username=username, ms_key=f'message-{mg_id}-{project_id}'))
                            redis_client.rpush(f'cache:unreadUsers:{username}', 3 * 3600,
                                               f'message-{mg_id}-{project_id}-{ms_id}')

                        elif mode == 1:
                            ms_id = missed_model.add_missed(
                                missed_add_interface(username=username, ms_key=f'notice-{project_id}'))
                            redis_client.rpush(f'cache:unreadUsers:{username}', 3 * 3600, f'notice-{project_id}-{ms_id}')

                    except Exception as e:
                        pass


ws_manager = WSConnectionManager()


class WebSocketCustomException(Exception):
    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason


async def resend_msg(missed_msg, mode, m_username):
    redis_user_key = f'cache:unreadUsers:{m_username}'
    for missed in missed_msg:
        if mode == 1:
            ms_key_split = missed[0].split('-')
            ms_id = missed[1]
        elif mode == 0:
            ms_key_split = missed.split('-')
        if ms_key_split[0].startswith('n'):  # notice重新发送
            missed_notice_id = ms_key_split[1]
            if mode == 0:
                ms_id = ms_key_split[2]
            notice_information = redis_client.get(f'cache:notices:{missed_notice_id}')
            if notice_information is None:  # 从数据库读
                redis_notice = notice_model.get_notice_by_nt_id(missed_notice_id)
                redis_client.set(f'cache:notices:{missed_notice_id}', json.dumps(redis_notice), ex=3 * 3600)
                redis_notice.pop('nt_content')
                redis_notice['up_username'] = redis_notice['up_username'].split(",")[-1]
                notice_information = redis_notice
            else:  # 从缓存读
                notice_information = json.loads(notice_information)
                notice_information['up_username'] = notice_information['up_username'].split(",")[-1]
                notice_information.pop('nt_content')
            send_thing = notice_information
        else:  # 处理message重发逻辑
            unsend_message = redis_client.zrangebyscore(f'cache:messageGroup:{ms_key_split[1]}', int(ms_key_split[2]),
                                                        int(ms_key_split[2]), 0, 1)
            if mode == 0:
                ms_id = ms_key_split[3]
            if unsend_message:
                send_thing = json.loads(unsend_message[0])
            else:
                send_thing = message_model.get_message_by_id(int(ms_key_split[2]))
        await ws_manager.send_personal_message(
            json.dumps(send_thing),
            ws_manager.active_connections[m_username])
        if mode == 0:
            redis_client.lpop(redis_user_key)
        missed_model.update_read(int(ms_id))


@ws_router.post("/auth")  # websocket建立前的权限认证与token生成
@user_standard_response
async def ws_auth(SDUOJUserInfo=Depends(cover_header)):
    exist_token = websocket_model.get_token_by_username(SDUOJUserInfo['username'])
    if exist_token is not None:
        return {'message': '连接已存在', 'data': {'token': exist_token[0]}, 'code': 0}
    token = str(uuid.uuid4().hex)
    websocket_model.build_ws_connect(websocket_add_interface(username=SDUOJUserInfo['username'], w_token=token))
    return {'message': '连接建立成功', 'data': {'token': token}, 'code': 0}


@ws_router.websocket("/handle/{token}")  # 建立websocket连接(注释掉的部分为判断已读未读)
async def ws_handle(websocket: WebSocket, token: str):
    try:
        m_username = websocket_model.get_username_by_token(token)
        # if m_username is None:
        #     raise WebSocketCustomException(code=403, reason='Permission Denial')
        m_username = m_username.username
        # 发送者刚上线，消息重新推送逻辑
        if m_username not in ws_manager.active_connections:
            await ws_manager.connect(websocket, m_username)
            redis_user_key = f'cache:unreadUsers:{m_username}'
            missed_msg = redis_client.lrange(redis_user_key, 0, -1)
            if missed_msg:  # 是否有错过的消息
                await resend_msg(missed_msg, 0, m_username)
            else:
                ms_keys = missed_model.get_key_by_username(m_username)
                if ms_keys:
                    await resend_msg(ms_keys, 1, m_username)
        # 发送心跳
        # asyncio.create_task(send_heartbeat(websocket))
        # 主循环
        while True:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=10000)  # websocket过期时间
            m_from = await getUserId(m_username)
            SDUOJUserInfo = await getUserInformation(m_from, 0)
            mode = data['mode']  # 1为向他人发送消息; 2为发布公告; 3为修改公告
            data.pop('mode')
            groups = SDUOJUserInfo['groups']  # 查出用户所属组
            if 'nt_id' in data:
                ct_id, e_id, psid = notice_model.get_ct_e_id(data['nt_id'])
            elif 'mg_id' in data:
                ct_id, e_id, psid = message_group_model.get_ct_e_id(data['mg_id'])
            elif 'm_id' in data:
                ct_id, e_id, psid = message_group_model.get_ct_e_id_by_m(data['m_id'])
            else:
                ct_id = data['ct_id'] if 'ct_id' in data else None
                e_id = data['e_id'] if 'e_id' in data else None
                psid = data['psid'] if 'psid' in data else None
            role_group_id = contest_exam_model.get_role_group(ct_id, e_id, psid)  # 判断用户是否在群聊组里
            judge_admin, judge_TA = await judge_in_groups(ct_id, e_id, psid, groups, SDUOJUserInfo, role_group_id, 0)
            if mode == 1:
                # 处理消息发送逻辑
                if judge_TA == 0 and judge_admin == 1:  # admin但不是TA不能发消息
                    raise WebSocketCustomException(code=403, reason="Permission Denial")
                message_information = message_group_model.get_mg_by_id(data['mg_id'], 1)  # 找群组创建者，不存在即群不存在
                if message_information is None:
                    raise WebSocketCustomException(code=404, reason="Not Found")
                message_add = message_receive_interface(**data)
                current_time, m_id = message_model.add_message(
                    message_add_interface(m_content=message_add.m_content, username=m_username,
                                          mg_id=message_add.mg_id))
                data["m_gmt_create"] = current_time
                data['username'] = m_username
                data['m_id'] = m_id
                redis_message_key = f"cache:messageGroup:{data['mg_id']}"
                redis_client.zadd(redis_message_key, 3 * 3600, {json.dumps(data): m_id})
                members = await get_message_group_members(role_group_id, message_information.username,
                                                          data['mg_id'])  # 获取全部成员
                await ws_manager.broadcast(0, json.dumps(data), members, m_id, m_username, data['mg_id'])
                try:
                    message_user_model.add_message_users(SDUOJUserInfo["username"], m_id)
                except Exception as e:
                    pass

            elif mode == 2:
                # 处理发布公告逻辑
                if judge_admin == 1 or judge_TA == 1:
                    student_list = await get_group_student(ct_id, e_id, psid)
                    data['username'] = m_username
                    data['up_username'] = m_username
                    nt_id, nt_gmt_create = notice_model.add_notice(notice_add_interface(**data))
                    data['nt_id'] = nt_id
                    data['nt_gmt_create'] = nt_gmt_create
                    data['nt_gmt_modified'] = nt_gmt_create
                    notice_read_key = f'cache:notices:{nt_id}'
                    redis_client.set(notice_read_key, json.dumps(data), 3 * 3600)
                    data.pop('nt_content')
                    await ws_manager.broadcast(1, json.dumps(data), student_list, nt_id, m_username)

            elif mode == 3:
                # 处理修改公告逻辑
                if judge_admin == 1 or judge_TA == 1:
                    student_list = await get_group_student(ct_id, e_id, psid)
                    data['up_username'] = m_username
                    timenow, up_username = notice_model.update_notice(notice_update_interface(**data))
                    notice_key = f'cache:notices:{data['nt_id']}'
                    redis_value = redis_client.get(notice_key)
                    if redis_value is not None:
                        redis_notice = json.loads(redis_value)
                        redis_notice['nt_gmt_modified'] = timenow
                        redis_notice['nt_content'] = data['nt_content']
                        redis_notice['nt_title'] = data['nt_title']
                        redis_notice['up_username'] = up_username
                        redis_client.set(notice_key, json.dumps(redis_notice), ex=3 * 3600)
                    else:
                        redis_notice = notice_model.get_notice_by_nt_id(data['nt_id'])
                        redis_client.set(notice_key, json.dumps(redis_notice), ex=3 * 3600)
                    redis_notice.pop('nt_content')
                    redis_notice['up_username'] = redis_notice['up_username'].split(",")[-1]
                    await ws_manager.broadcast(1, json.dumps(redis_notice), student_list, data['nt_id'], m_username)

            elif mode == 4:
                # 处理聊天组接收到新消息给后端反馈在浏览当前页面的用户，以处理消息已读状态逻辑
                message_user_model.add_message_users(data['username'], data['m_id'])

    except WebSocketCustomException as e:  # 自定义抛出异常
        error_message = json.dumps({"code": e.code, "reason": e.reason})
        await websocket.send_text(f"Error: {error_message}")

    except Exception as e:  # 所有异常
        print(e)
        ws_manager.disconnect(m_username)
        websocket_model.close_by_username(m_username)

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
