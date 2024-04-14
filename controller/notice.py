import asyncio
import json

from fastapi import APIRouter, Query
from fastapi import Request
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from model.websocket import ws_manager
from service.notice import NoticeModel
from type.notice import notice_add_interface, notice_update_interface, base_interface, notice_information_interface, \
    notice_delete_interface
from type.page import page
from utils.response import user_standard_response, makePageResult
from service.message import MessageModel

notice_router = APIRouter()

notice_model = NoticeModel()
message_model = MessageModel()


@notice_router.post("/deleteNotice")  # 删除公告
@user_standard_response
async def notice_delete(request: Request, n_id: notice_delete_interface):
    notice_model.delete_notice(n_id.n_id)
    return {'message': '删除成功', 'data': True, 'code': 0}


@notice_router.get("/getNoticeList")  # 查看已推送的公告列表
@user_standard_response
async def noticelist_get(request: Request, pageNow: int, pageSize: int, p_id: int = Query(None),
                         ct_id: int = Query(None)):
    Page = page(pageSize=pageSize, pageNow=pageNow)
    noticelist_get = base_interface(p_id=p_id, ct_id=ct_id)
    ans, counts = notice_model.get_notice_list_by_p_ct(Page, noticelist_get)
    result = makePageResult(Page, counts, ans)
    return {'message': '查看成功', 'data': result, 'code': 0}


@notice_router.get("/getNotice/{n_id}")  # 查看某一公告
@user_standard_response
async def notice_get(request: Request, n_id: int):
    ans = notice_model.get_notice_by_n_id(n_id)
    return {'message': '查看成功', 'data': ans, 'code': 0}
