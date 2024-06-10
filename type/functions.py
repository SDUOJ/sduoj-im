import asyncio
import time
from fastapi import WebSocket
import websockets
from model.redis_db import redis_client

import time

def num_in_nums(num, nums):
    nums_list = nums.split(",")
    return True if num in nums_list else False


async def send_heartbeat(websocket: WebSocket):
    heartbeat_interval = 10000
    try:
        while True:
            await asyncio.sleep(heartbeat_interval)  # 发送一次心跳时间
            await websocket.send_text("heartbeat")
    except Exception:
        # 发送心跳期间发生异常，可能是连接已断开
        pass


def get_redis_message_key(m_from, data):
    if m_from > data['m_to']:  # 固定格式为:p/ct_id - 小id - 大id
        m_small = data['m_to']
        m_big = m_from
    else:
        m_small = m_from
        m_big = data['m_to']
    return f"cache:messages:p:{data['p_id']}-{m_small}-{m_big}" if 'p_id' in data else f"cache:messages:ct-{data['ct_id']}-{m_small}-{m_big}"

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
# def get_latest_redis_value(p_id, m_from, m_to):
#     # 构造模糊查询的模式
#     pattern = f"p-{p_id}-{m_from}-{m_to}-*"
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
