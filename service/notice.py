from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc
from type.functions import num_in_nums
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
            return obj_add.n_id, obj_add.n_gmt_create

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

    def get_notice_list_id_by_p_ct(self, page, noticelist_get: base_interface):  # 根据p_id,ct_id查询notice的列表
        with self.get_db() as session:
            if noticelist_get.p_id is not None:
                ses = session.query(Notice.n_id).filter(
                    Notice.p_id == noticelist_get.p_id, Notice.n_is_deleted == 0)
            elif noticelist_get.ct_id is not None:
                ses = session.query(Notice.n_id).filter(
                    Notice.ct_id == noticelist_get.ct_id, Notice.n_is_deleted == 0)
            counts = ses.count()
            ses = ses.order_by(
                desc(Notice.n_gmt_modified)).all()
            ses = ses[page.offset():page.offset() + page.limit()]
            session.commit()
            notice_ids = [id_tuple[0] for id_tuple in ses]
            return notice_ids, counts

    def get_notice_list_by_ids(self, ids):  # 根据 id 查询 notice 的列表
        with self.get_db() as session:
            # 查询指定 id 的记录
            ses = session.query(Notice.n_id, Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id,
                                Notice.n_title, Notice.n_read_user).filter(
                Notice.n_is_deleted == 0,
                Notice.n_id.in_(ids)  # 过滤条件：n_id 在给定的 ids 列表中
            ).all()

            # 将查询结果转换为字典列表
            notice_json = []
            for record in ses:
                notice_json.append({
                    'n_id': record.n_id,
                    'n_gmt_create': record.n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                    'n_gmt_modified': record.n_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'u_id': record.u_id,
                    'n_title': record.n_title,
                    'n_read_user': record.n_read_user,
                })

            session.commit()
            return notice_json

    # def get_notice_list_by_p_ct(self, page, noticelist_get: base_interface):  # 根据p_id,ct_id查询notice的列表
    #     with self.get_db() as session:
    #         if noticelist_get.p_id is not None:
    #             ses = session.query(Notice.n_id, Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id,
    #                                 Notice.n_title,
    #                                 Notice.n_read_user).filter(
    #                 Notice.p_id == noticelist_get.p_id, Notice.n_is_deleted == 0)
    #         elif noticelist_get.ct_id is not None:
    #             ses = session.query(Notice.n_id, Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id,
    #                                 Notice.n_title,
    #                                 Notice.n_read_user).filter(
    #                 Notice.ct_id == noticelist_get.ct_id, Notice.n_is_deleted == 0)
    #         counts = ses.count()
    #         ses = ses.order_by(
    #             desc(Notice.n_gmt_modified)).all()
    #         ses = ses[page.offset():page.offset() + page.limit()]
    #         notice_json = []
    #         for ses in ses:
    #             notice_json.append({
    #                 'n_id': ses.n_id,
    #                 'n_gmt_create': ses.n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
    #                 'n_gmt_modified': ses.n_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
    #                 'u_id': ses.u_id,
    #                 'n_title': ses.n_title,
    #                 'n_read_user': ses.n_read_user,
    #             })
    #
    #         session.commit()
    #         return notice_json, counts

    def get_notice_by_n_id(self, n_id):  # 根据n_id查询notice的基本信息
        with self.get_db() as session:
            ses = session.query(Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id, Notice.n_title,
                                Notice.n_content, Notice.n_read_user).filter(
                Notice.n_id == n_id, Notice.n_is_deleted == 0).first()
            res = {
                'n_gmt_create': ses.n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                'n_gmt_modified': ses.n_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
                'u_id': ses.u_id,
                'n_title': ses.n_title,
                'n_content': ses.n_content,
                'n_read_user': ses.n_read_user
            }
            session.commit()
            return res

    def get_notice_content_by_n_id(self, n_id):  # 根据n_id查询notice的content
        with self.get_db() as session:
            content = session.query(Notice.n_content).filter(
                Notice.n_id == n_id, Notice.n_is_deleted == 0).first()
            session.commit()
            return content
