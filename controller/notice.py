import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Query, Depends
from fastapi import Request
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from type.functions import num_in_nums
from model.redis_db import redis_client
from model.websocket import ws_manager
from service.notice import NoticeModel, UserNoticeModel
from type.notice import notice_add_interface, notice_update_interface, base_interface, notice_information_interface, \
    notice_delete_interface
from type.page import page
from utils.response import user_standard_response, makePageResult
from service.message import MessageModel
from utils.oj_authorization import oj_authorization

notice_router = APIRouter()

notice_model = NoticeModel()
user_notice_model = UserNoticeModel()
message_model = MessageModel()


@notice_router.post("/deleteNotice")  # 删除公告
@user_standard_response
async def notice_delete(n_id: notice_delete_interface):
    notice_model.delete_notice(n_id.n_id)
    redis_client.delete(f'cache:notices:{n_id.n_id}')
    return {'message': '删除成功', 'data': True, 'code': 0}


@notice_router.get("/getNoticeList")  # 查看已推送的公告列表
@user_standard_response
async def noticelist_get(pageNow: int, pageSize: int, p_id: int = Query(None),
                         ct_id: int = Query(None), user_information=Depends(oj_authorization)):
    # 鉴权(有权限的用户才可查看)
    u_id = user_information['userId']
    Page = page(pageSize=pageSize, pageNow=pageNow)
    noticelist_get = base_interface(p_id=p_id, ct_id=ct_id)
    notices_ids, counts = notice_model.get_notice_list_id_by_p_ct(Page, noticelist_get)
    notices = []
    none_notice_ids = []
    notice_read_key = f'cache:UserReadNotices:{u_id}'
    for n_id in notices_ids:  # 遍历所有要返回的Notice_id
        current_notice_information = redis_client.get(f'cache:notices:{n_id}')
        if current_notice_information is not None:  # redis里有
            current_notice_information_json = json.loads(current_notice_information)
            current_notice_information_json['n_id'] = n_id
            n_is_read = 1
            if not redis_client.sismember(notice_read_key, n_id):
                if not user_notice_model.judge_exist_by_u_n(u_id, n_id):
                    n_is_read = 0
            current_notice_information_json['n_is_read'] = n_is_read
            notices.append(current_notice_information_json)
        else:
            none_notice_ids.append(n_id)
    if none_notice_ids:  # 存在不在redis中的notice
        new_notices = notice_model.get_notice_list_by_ids(none_notice_ids)
        for new_notice in new_notices:
            n_id = new_notice['n_id']
            new_notice.pop('n_id')
            n_is_read = 1
            if not redis_client.sismember(notice_read_key, n_id):
                if not user_notice_model.judge_exist_by_u_n(u_id, n_id):
                    n_is_read = 0
            redis_client.set(f'cache:notices:{n_id}', json.dumps(new_notice), 1 * 24 * 3600)
            new_notice['n_is_read'] = n_is_read
            new_notice['n_id'] = n_id
            notices.append(new_notice)
    notices.sort(key=lambda x: datetime.strptime(x['n_gmt_create'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    result = makePageResult(Page, counts, notices)
    # notices, counts = notice_model.get_notice_list_by_p_ct(Page, noticelist_get)
    # for notice in notices:
    #     n_id = notice['n_id']
    #     notice.pop('n_id')
    #     n_is_read = 1 if notice["n_read_user"] is not None and num_in_nums(str(u_id), notice["n_read_user"]) else 0
    #     redis_client.set(f'notice-{n_id}', json.dumps(notice), 1 * 24 * 3600)
    #     notice.pop('n_read_user')
    #     notice['n_is_read'] = n_is_read
    #     notice['n_id'] = n_id
    return {'message': '查看成功', 'data': result, 'code': 0}


@notice_router.get("/getNotice/{n_id}")  # 查看某一公告
@user_standard_response
async def notice_get(n_id: int, user_information=Depends(oj_authorization)):
    # 鉴权(有权限的用户才可查看)
    u_id = user_information['userId']
    notice_key = f'cache:notices:{n_id}'
    notice_read_key = f'cache:UserReadNotices:{u_id}'
    redis_value = redis_client.get(notice_key)
    if redis_value is None:
        # 如果Redis中没有该公告的数据，则从数据库中获取数据
        ans = notice_model.get_notice_by_n_id(n_id)
        if ans is None:
            return {'message': '公告已删除', 'data': None, 'code': 1}
        redis_client.set(notice_key, json.dumps(ans), ex=1 * 24 * 3600)
        ans = {"n_content": ans['n_content']}
    else:
        redis_notice = json.loads(redis_value)
        ans = {'n_content': redis_notice['n_content']}
    if not redis_client.sismember(notice_read_key, n_id):
        if not user_notice_model.judge_exist_by_u_n(u_id, n_id):
            redis_client.sadd(notice_read_key, n_id)
            redis_client.expire(notice_read_key, 24 * 3600)
            user_notice_model.add_user_notice(n_id, u_id)
    return {'message': '公告内容如下:', 'data': ans, 'code': 0}
