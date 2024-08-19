import json
from datetime import datetime

from fastapi import APIRouter, Query, Depends, HTTPException

from auth import cover_header, is_role_member, is_admin, judge_in_groups
from model.redis_db import redis_client
from sduojApi import getUserId, getUserInformation
from service.websocket import ContestExamModel
from service.message import MessageModel
from service.notice import NoticeModel, UserNoticeModel
from type.notice import base_interface, notice_delete_interface
from type.page import page
from utils.response import user_standard_response, makePageResult
from type.functions import dict_pop

notice_router = APIRouter()

notice_model = NoticeModel()
user_notice_model = UserNoticeModel()
message_model = MessageModel()
contest_exam_model = ContestExamModel()


@notice_router.post("/deleteNotice")  # 删除公告
@user_standard_response
async def notice_delete(nt_id: notice_delete_interface, SDUOJUserInfo=Depends(cover_header)):
    groups = SDUOJUserInfo["groups"]  # 查出用户所属组
    ids = notice_model.get_ct_e_id(nt_id.nt_id)
    role_group_id = contest_exam_model.get_role_group(ids.ct_id, ids.e_id)  # 判断用户是否在TA组里
    if not is_role_member(role_group_id, groups) and not is_admin(SDUOJUserInfo):  # 用户不在TA组内,无权限删除公告
        raise HTTPException(detail="Permission Denial", status_code=403)
    notice_model.delete_notice(nt_id.nt_id)
    redis_client.delete(f'cache:notices:{nt_id.nt_id}')
    return {'message': '删除成功', 'data': True, 'code': 0}


@notice_router.get("/getNoticeList")  # 查看已推送的公告列表
@user_standard_response
async def noticelist_get(pageNow: int, pageSize: int, e_id: int = Query(None),
                         ct_id: int = Query(None), SDUOJUserInfo=Depends(cover_header)):
    groups = SDUOJUserInfo['groups']  # 查出用户所属组
    role_group_id = contest_exam_model.get_role_group(ct_id, e_id)
    await judge_in_groups(ct_id, e_id, groups, SDUOJUserInfo, role_group_id, 0)  # 鉴权
    Page = page(pageSize=pageSize, pageNow=pageNow)
    noticelist_get = base_interface(e_id=e_id, ct_id=ct_id)
    notices_ids, counts = notice_model.get_notice_list_id_by_p_ct(Page, noticelist_get)
    notices = []
    none_notice_ids = []
    notice_read_key = f'cache:UserReadNotices:{SDUOJUserInfo["username"]}'
    for nt_id in notices_ids:  # 遍历所有要返回的Notice_id
        current_notice_information = redis_client.get(f'cache:notices:{nt_id}')
        if current_notice_information is not None:  # redis里有
            current_notice_information_json = json.loads(current_notice_information)
            current_notice_information_json['up_username'] = current_notice_information_json['up_username'].split(",")[
                -1]
            current_notice_information_json = dict_pop(current_notice_information_json,
                                                       ['nt_content', 'username', 'up_username'])
            if 'ct_id' in current_notice_information_json:
                current_notice_information_json.pop('ct_id')
            elif 'e_id' in current_notice_information_json:
                current_notice_information_json.pop('e_id')
            n_is_read = 1
            if not redis_client.sismember(notice_read_key, nt_id):
                if not user_notice_model.judge_exist_by_u_n(SDUOJUserInfo["username"], nt_id):
                    n_is_read = 0
            current_notice_information_json['n_is_read'] = n_is_read
            notices.append(current_notice_information_json)
        else:
            none_notice_ids.append(nt_id)
    if none_notice_ids:  # 存在不在redis中的notice
        new_notices = notice_model.get_notice_list_by_ids(none_notice_ids)
        for new_notice in new_notices:
            n_is_read = 1
            if not redis_client.sismember(notice_read_key, new_notice['nt_id']):
                if not user_notice_model.judge_exist_by_u_n(SDUOJUserInfo["username"], new_notice['nt_id']):
                    n_is_read = 0
            redis_client.set(f'cache:notices:{new_notice['nt_id']}', json.dumps(new_notice), 3 * 3600)
            new_notice['n_is_read'] = n_is_read
            new_notice = dict_pop(new_notice, ['nt_content', 'username', 'up_username'])
            if 'ct_id' in new_notice:
                new_notice.pop('ct_id')
            elif 'e_id' in new_notice:
                new_notice.pop('e_id')
            notices.append(new_notice)
    notices.sort(key=lambda x: datetime.strptime(x['nt_gmt_modified'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    result = makePageResult(Page, counts, notices)
    return {'message': '查看成功', 'data': result, 'code': 0}


@notice_router.get("/getNotice/{nt_id}")  # 查看某一公告
@user_standard_response
async def notice_get(nt_id: int, SDUOJUserInfo=Depends(cover_header)):
    ids = notice_model.get_ct_e_id(nt_id)
    groups = SDUOJUserInfo['groups']  # 查出用户所属组
    ct_id, e_id = notice_model.get_ct_e_id(nt_id)
    role_group_id = contest_exam_model.get_role_group(ct_id, e_id)
    await judge_in_groups(ids.ct_id, ids.e_id, groups, SDUOJUserInfo, role_group_id)  # 鉴权
    notice_key = f'cache:notices:{nt_id}'
    notice_read_key = f'cache:UserReadNotices:{SDUOJUserInfo["username"]}'
    redis_value = redis_client.get(notice_key)
    if redis_value is None:
        # 如果Redis中没有该公告的数据，则从数据库中获取数据
        ans = notice_model.get_notice_by_nt_id(nt_id)
        if ans is None:
            return {'message': '公告已删除', 'data': None, 'code': 1}
        redis_client.set(notice_key, json.dumps(ans), ex=1 * 24 * 3600)
        last_up_username = ans['up_username'].split(",")[-1]
        u_id = await getUserId(last_up_username)
        email = await getUserInformation(u_id, 1)['email']
        ans = {"nt_content": ans['nt_content'], "username": ans['username'], "up_username": last_up_username,
               "nt_gmt_create": ans['nt_gmt_create'], "nt_gmt_modified": ans["nt_gmt_modified"],
               'email': email['email']}
    else:
        redis_notice = json.loads(redis_value)
        last_up_username = redis_notice['up_username'].split(",")[-1]
        u_id = await getUserId(last_up_username)
        email = await getUserInformation(u_id, 1)
        ans = {"nt_content": redis_notice['nt_content'], "username": redis_notice['username'],
               "up_username": last_up_username,
               "nt_gmt_create": redis_notice['nt_gmt_create'], "nt_gmt_modified": redis_notice["nt_gmt_modified"],
               'email': email['email']}
    if not redis_client.sismember(notice_read_key, nt_id):
        if not user_notice_model.judge_exist_by_u_n(SDUOJUserInfo["username"], nt_id):
            redis_client.sadd(notice_read_key, 24 * 3600, nt_id)
            user_notice_model.add_user_notice(nt_id, SDUOJUserInfo["username"])
    return {'message': '公告内容如下:', 'data': ans, 'code': 0}
