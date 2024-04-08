from fastapi import APIRouter
from fastapi import Request

from service.notice import NoticeModel
from type.notice import notice_add_interface, notice_update_interface, noticelist_get_interface
from utils.response import user_standard_response

notice_router = APIRouter()

notice_model = NoticeModel()


@notice_router.post("/publishNotice")  # 发布公告
@user_standard_response
async def notice_publish(request: Request, notice_add: notice_add_interface):
    notice_model.add_notice(notice_add)
    return {'message': '发布成功', 'data': True, 'code': 0}


@notice_router.post("/deleteNotice")  # 删除公告
@user_standard_response
async def notice_delete(request: Request, n_id: int):
    notice_model.delete_notice(n_id)
    return {'message': '删除成功', 'data': True, 'code': 0}


@notice_router.post("/updateNotice")  # 修改公告
@user_standard_response
async def notice_update(request: Request, notice_update: notice_update_interface):
    notice_model.update_notice(notice_update)
    return {'message': '修改成功', 'data': True, 'code': 0}


@notice_router.get("/getNoticeList")  # 查看已推送的公告列表
@user_standard_response
async def noticelist_get(request: Request, noticelist_get: noticelist_get_interface):
    ans = notice_model.get_notice_list_by_p_ct(noticelist_get)
    return {'message': '查看成功', 'data': ans, 'code': 0}


@notice_router.get("/getNotice")  # 查看某一公告
@user_standard_response
async def notice_get(request: Request, n_id: int):
    ans = notice_model.get_notice_by_n_id(n_id)
    return {'message': '查看成功', 'data': True, 'code': 0}
