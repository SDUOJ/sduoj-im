import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Query, Depends, WebSocketException
from fastapi import Request
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from model.redis_db import redis_client
from model.websocket import ws_manager
from service.group import ContestExamModel
from service.notice import NoticeModel, UserNoticeModel
from type.functions import judge_in_groups
from type.notice import notice_add_interface, notice_update_interface, base_interface, notice_information_interface, \
    notice_delete_interface
from type.page import page
from utils.response import user_standard_response, makePageResult
from service.message import MessageModel
from utils.oj_authorization import oj_http_authorization

notice_router = APIRouter()

notice_model = NoticeModel()
user_notice_model = UserNoticeModel()
message_model = MessageModel()
contest_exam_model = ContestExamModel()


@notice_router.post("/deleteNotice")  # 删除公告
@user_standard_response
async def notice_delete(nt_id: notice_delete_interface, user_information=Depends(oj_http_authorization)):
    groups = user_information['groups']  # 查出用户所属组
    ids = notice_model.get_ct_e_id(nt_id.nt_id)
    role_group_id = contest_exam_model.get_role_group(ids.ct_id, ids.e_id)  # 判断用户是否在TA组里
    if not role_group_id in groups:  # 用户不在TA组内,无权限删除公告
        raise WebSocketException(code=403, reason="用户无权限")
    notice_model.delete_notice(nt_id.nt_id)
    redis_client.delete(f'cache:notices:{nt_id.nt_id}')
    return {'message': '删除成功', 'data': True, 'code': 0}


# , user_information=Depends(oj_authorization)
@notice_router.get("/getNoticeList")  # 查看已推送的公告列表
@user_standard_response
async def noticelist_get(pageNow: int, pageSize: int, e_id: int = Query(None),
                         ct_id: int = Query(None), user_information=Depends(oj_http_authorization)):
    # 鉴权(有权限的用户才可查看)
    u_id = user_information['userId']
    groups = user_information['groups']  # 查出用户所属组
    await judge_in_groups(ct_id, e_id, groups)  # 鉴权
    Page = page(pageSize=pageSize, pageNow=pageNow)
    noticelist_get = base_interface(e_id=e_id, ct_id=ct_id)
    notices_ids, counts = notice_model.get_notice_list_id_by_p_ct(Page, noticelist_get)
    notices = []
    none_notice_ids = []
    notice_read_key = f'cache:UserReadNotices:{u_id}'
    for nt_id in notices_ids:  # 遍历所有要返回的Notice_id
        current_notice_information = redis_client.get(f'cache:notices:{nt_id}')
        if current_notice_information is not None:  # redis里有
            current_notice_information_json = json.loads(current_notice_information)
            current_notice_information_json['nt_id'] = nt_id
            n_is_read = 1
            if not redis_client.sismember(notice_read_key, nt_id):
                if not user_notice_model.judge_exist_by_u_n(u_id, nt_id):
                    n_is_read = 0
            current_notice_information_json['n_is_read'] = n_is_read
            notices.append(current_notice_information_json)
        else:
            none_notice_ids.append(nt_id)
    if none_notice_ids:  # 存在不在redis中的notice
        new_notices = notice_model.get_notice_list_by_ids(none_notice_ids)
        for new_notice in new_notices:
            nt_id = new_notice['nt_id']
            new_notice.pop('nt_id')
            n_is_read = 1
            if not redis_client.sismember(notice_read_key, nt_id):
                if not user_notice_model.judge_exist_by_u_n(u_id, nt_id):
                    n_is_read = 0
            redis_client.set(f'cache:notices:{nt_id}', json.dumps(new_notice), 1 * 24 * 3600)
            new_notice['n_is_read'] = n_is_read
            new_notice['nt_id'] = nt_id
            notices.append(new_notice)
    notices.sort(key=lambda x: datetime.strptime(x['nt_gmt_create'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    result = makePageResult(Page, counts, notices)
    # notices, counts = notice_model.get_notice_list_by_p_ct(Page, noticelist_get)
    # for notice in notices:
    #     nt_id = notice['nt_id']
    #     notice.pop('nt_id')
    #     n_is_read = 1 if notice["n_read_user"] is not None and num_in_nums(str(u_id), notice["n_read_user"]) else 0
    #     redis_client.set(f'notice-{nt_id}', json.dumps(notice), 1 * 24 * 3600)
    #     notice.pop('n_read_user')
    #     notice['n_is_read'] = n_is_read
    #     notice['nt_id'] = nt_id
    return {'message': '查看成功', 'data': result, 'code': 0}


@notice_router.get("/getNotice/{nt_id}")  # 查看某一公告
@user_standard_response
async def notice_get(nt_id: int, user_information=Depends(oj_http_authorization)):
    # 鉴权(有权限的用户才可查看)
    u_id = user_information['userId']
    ids = notice_model.get_ct_e_id(nt_id)
    groups = user_information['groups']  # 查出用户所属组
    await judge_in_groups(ids.ct_id, ids.e_id, groups)  # 鉴权
    notice_key = f'cache:notices:{nt_id}'
    notice_read_key = f'cache:UserReadNotices:{u_id}'
    redis_value = redis_client.get(notice_key)
    if redis_value is None:
        # 如果Redis中没有该公告的数据，则从数据库中获取数据
        ans = notice_model.get_notice_by_nt_id(nt_id)
        if ans is None:
            return {'message': '公告已删除', 'data': None, 'code': 1}
        redis_client.set(notice_key, json.dumps(ans), ex=1 * 24 * 3600)
        ans = {"nt_content": ans['nt_content']}
    else:
        redis_notice = json.loads(redis_value)
        ans = {'nt_content': redis_notice['nt_content']}
    if not redis_client.sismember(notice_read_key, nt_id):
        if not user_notice_model.judge_exist_by_u_n(u_id, nt_id):
            redis_client.sadd(notice_read_key, nt_id)
            redis_client.expire(notice_read_key, 24 * 3600)
            user_notice_model.add_user_notice(nt_id, u_id)
    return {'message': '公告内容如下:', 'data': ans, 'code': 0}
