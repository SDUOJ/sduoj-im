from fastapi.encoders import jsonable_encoder
from model.db import dbSession
from model.notice import Notice
from type.notice import notice_add_interface, notice_update_interface, noticelist_get_interface
import datetime


class NoticeModel(dbSession):
    def add_notice(self, obj: notice_add_interface):  # 管理员发布公告
        obj_dict = jsonable_encoder(obj)
        obj_add = Notice(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.flush()
            session.commit()
            return obj_add.id

    def delete_notice(self, n_id: int):
        with self.get_db() as session:
            session_obj = session.query(Notice).filter_by(n_id == n_id).first()
            if session_obj:
                session.delete(session_obj)
                session.commit()
                return n_id
            else:
                return None

    def update_notice(self, notice_update: notice_update_interface):
        with self.get_db() as session:
            session.query(Notice).filter(Notice.n_id == notice_update.n_id).update(
                {"n_title": notice_update.n_title, "n_content": notice_update.n_content,
                 "n_gmt_modified": datetime.datetime.now().strftime(
                     "%Y-%m-%d %H:%M:%S")})
            session.commit()
            return notice_update.n_id

    def get_notice_list_by_p_ct(self, noticelist_get: noticelist_get_interface):  # 根据p_id,ct_id查询notice的列表
        with self.get_db as session:
            if noticelist_get.p_id != None:
                ses = session.query(Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id, Notice.n_title).filter(
                    Notice.p_id == noticelist_get.p_id).first()
            elif noticelist_get.ct_id != None:
                ses = session.query(Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id, Notice.n_title).filter(
                    Notice.ct_id == noticelist_get.ct_id).first()
            session.commit()
            return ses

    def get_notice_by_n_id(self, n_id):  # 根据n_id查询notice的基本信息
        with self.get_db as session:
            ses = session.query(Notice.n_content, Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id).filter(
                Notice.n_id == n_id).first()
            session.commit()
            return ses
