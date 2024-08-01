import asyncio
import json
import time
from typing import Union

import requests
from fastapi import WebSocket, HTTPException
import websockets
from model.redis_db import redis_client

import time

from sduojApi import contestIdToGroupIdList, examIdToGroupIdList, getGroupMember, getUserInformation


async def send_heartbeat(websocket: WebSocket):
    heartbeat_interval = 300000
    try:
        while True:
            await asyncio.sleep(heartbeat_interval)  # 发送一次心跳时间
            await websocket.send_text("heartbeat")
    except Exception:
        # 发送心跳期间发生异常，可能是连接已断开
        pass


async def get_group_student(ct_id, e_id):
    if ct_id is not None:
        current_group = await contestIdToGroupIdList(ct_id)
    elif e_id is not None:
        current_group = await examIdToGroupIdList(e_id)
    return await getGroupMember(int(current_group[0]))


async def get_message_group_members(role_group_id, u_id, mg_id, is_admin):
    redis_members = redis_client.get(f"cache:messageGroupMember:{mg_id}")
    if redis_members is not None:
        members = json.loads(redis_members)
    else:
        members = await getGroupMember(role_group_id)
        build_member = await getUserInformation(u_id)
        members.append(build_member)
        members.append({'build_username': build_member['username']})
        members.append({'is_admin': is_admin})
        redis_client.set(f"cache:messageGroupMember:{mg_id}", json.dumps(members), ex=9000)
    return members

# def get_redis_message_key(m_from, data):  # 私聊情况
#     if m_from > data['m_to']:  # 固定格式为:p/ct_id - 小id - 大id
#         m_small = data['m_to']
#         m_big = m_from
#     else:
#         m_small = m_from
#         m_big = data['m_to']
#     return f"cache:messages:p:{data['e_id']}-{m_small}-{m_big}" if 'e_id' in data else f"cache:messages:ct-{data['ct_id']}-{m_small}-{m_big}"
#


# def check_keys_absent_in_redis(keys_list):
#     # 检查每个键是否存在于 Redis 中
#     for key_suffix in keys_list:
#         redis_key = f'notice-{key_suffix[0]}'
#         if redis_client.key_exists(redis_key):
#             return True  # 如果任何一个键存在，则返回True
#     return False  # 如果所有键都不存在，则返回 False


# def send_read_receipt(sender_id, receiver_id):
#     read_receipt_key = f"{sender_id}-{receiver_id}-readTime"
#     redis_client.set(read_receipt_key, str(time.time()))
#
#
# def get_unread_messages(user_id):
#     unread_messages = []
#     for key in redis_client.scan_iter(f"{user_id}-*-unread"):
#         _, peer_id, _ = key.split("-")
#         unread_messages.extend(redis_client.lrange(key, 0, -1))
#     return unread_messages
#
#
# def get_read_receipts(user_id, redis_client):
#     read_receipts = {}
#     for key in redis_client.scan_iter(f"{user_id}-*-readTime"):
#         sender_id, receiver_id, _ = key.split("-")
#         read_receipt_time = float(redis_client.get(key))
#         read_receipts[receiver_id] = read_receipt_time
#     return read_receipts
#
#
# def get_latest_redis_value(e_id, m_from, m_to):
#     # 构造模糊查询的模式
#     pattern = f"p-{e_id}-{m_from}-{m_to}-*"
#     redis_client.set(1, 1)
#     # 使用 KEYS 命令进行模糊查询
#     keys = redis_client.keys(pattern)
#     # 找出最新的时间戳
#     latest_timestamp = 0
#     latest_key = None
#     for key in keys:
#         _, _, _, _, timestamp = key.split("-")
#         timestamp = float(timestamp)
#         if timestamp > latest_timestamp:
#             latest_timestamp = timestamp
#             latest_key = key
#     # 如果找到了最新的键,则获取对应的值
#     if latest_key:
#         return redis_client.get(latest_key)
#     else:
#         return None
