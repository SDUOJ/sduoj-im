from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc

from model.db import dbSession
from model.notice import Notice
from type.notice import notice_add_interface, notice_update_interface, base_interface
import datetime


class NoticeModel(dbSession):
    def add_notice(self, obj: notice_add_interface):  # 管理员发布公告
        obj_dict = jsonable_encoder(obj)
        obj_add = Notice(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.flush()
            session.commit()
            return 'ok'

    def delete_notice(self, n_id: int):
        with self.get_db() as session:
            session.query(Notice).filter(Notice.n_id == n_id).update(
                {"n_is_deleted": 1})
            session.commit()

    def update_notice(self, notice_update: notice_update_interface):
        with self.get_db() as session:
            session.query(Notice).filter(Notice.n_id == notice_update.n_id, Notice.n_is_deleted == 0).update(
                {"n_title": notice_update.n_title, "n_content": notice_update.n_content,
                 "n_gmt_modified": datetime.datetime.now().strftime(
                     "%Y-%m-%d %H:%M:%S")})
            session.commit()
            return notice_update.n_id

    def get_notice_list_by_p_ct(self, page, noticelist_get: base_interface):  # 根据p_id,ct_id查询notice的列表
        with self.get_db() as session:
            if noticelist_get.p_id != None:
                ses = session.query(Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id, Notice.n_title).filter(
                    Notice.p_id == noticelist_get.p_id, Notice.n_is_deleted == 0)
            elif noticelist_get.ct_id != None:
                ses = session.query(Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id, Notice.n_title).filter(
                    Notice.ct_id == noticelist_get.ct_id, Notice.n_is_deleted == 0)
            counts = ses.count()
            ses = ses.order_by(
                desc(Notice.n_gmt_modified)).all()
            ses = ses[page.offset():page.offset() + page.limit()]
            notice_json = [
                {
                    'n_gmt_create': ses.n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                    'n_gmt_modified': ses.n_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'u_id': ses.u_id,
                    'n_title': ses.n_title
                } for ses in ses
            ]
            session.commit()
            return notice_json, counts

    def get_notice_by_n_id(self, n_id):  # 根据n_id查询notice的基本信息
        with self.get_db() as session:
            ses = session.query(Notice.n_content, Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id,
                                Notice.n_title).filter(
                Notice.n_id == n_id, Notice.n_is_deleted == 0).first()
            res = {'n_content': ses[0], 'n_gmt_create': ses[1].strftime('%Y-%m-%d %H:%M:%S'),
                   'n_gmt_modified': ses[2].strftime('%Y-%m-%d %H:%M:%S'), 'u_id': ses[3], 'n_title': ses[4]}
            session.commit()
            return res
