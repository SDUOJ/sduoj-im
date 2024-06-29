from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc
from type.functions import num_in_nums
from model.db import dbSession
from model.notice import Notice, UserNotice
from type.notice import notice_add_interface, notice_update_interface, base_interface, notice_user_add_interface
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
            timenow = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
            session.query(Notice).filter(Notice.n_id == notice_update.n_id, Notice.n_is_deleted == 0).update(
                {"n_title": notice_update.n_title, "n_content": notice_update.n_content,
                 "n_gmt_modified": timenow})
            session.commit()
            return timenow

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
            ses = session.query(Notice.n_id, Notice.n_gmt_create, Notice.n_gmt_modified, Notice.u_id, Notice.n_content,
                                Notice.n_title, Notice.p_id, Notice.ct_id).filter(
                Notice.n_is_deleted == 0,
                Notice.n_id.in_(ids)  # 过滤条件：n_id 在给定的 ids 列表中
            ).all()

            # 将查询结果转换为字典列表
            notice_json = []
            for record in ses:
                temp_dict = {
                    'n_id': record.n_id,
                    'n_gmt_create': record.n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                    'n_gmt_modified': record.n_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'u_id': record.u_id,
                    'n_content': record.n_content,
                    'n_title': record.n_title
                }
                if record.p_id is not None:  # 如果 p_id 不为空，则添加到结果字典
                    temp_dict['p_id'] = record.p_id

                if record.ct_id is not None:  # 如果 ctp_id 不为空，则添加到结果字典
                    temp_dict['ct_id'] = record.ct_id
                notice_json.append(temp_dict)

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
                                Notice.n_content, Notice.p_id, Notice.ct_id).filter(
                Notice.n_id == n_id, Notice.n_is_deleted == 0).first()
            res = None
            if ses is not None:
                res = {
                    'n_gmt_create': ses.n_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                    'n_gmt_modified': ses.n_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'u_id': ses.u_id,
                    'n_title': ses.n_title,
                    'n_content': ses.n_content
                }
                if ses.p_id is not None:  # 如果 p_id 不为空，则添加到结果字典
                    res['p_id'] = ses.p_id

                if ses.ct_id is not None:  # 如果 ctp_id 不为空，则添加到结果字典
                    res['ct_id'] = ses.ct_id
            session.commit()
            return res

    def get_notice_content_by_n_id(self, n_id):  # 根据n_id查询notice的content
        with self.get_db() as session:
            content = session.query(Notice.n_content).filter(
                Notice.n_id == n_id, Notice.n_is_deleted == 0).first()
            session.commit()
            return content


class UserNoticeModel(dbSession):
    def add_user_notice(self, n_id: int, u_id: int):  # 添加已读记录
        obj = notice_user_add_interface(n_id=n_id, u_id=u_id)
        obj_dict = jsonable_encoder(obj)
        obj_add = UserNotice(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.flush()
            session.commit()
            return obj_add.nu_id

    def judge_exist_by_u_n(self, u_id: int, n_id: int):  # 根据u_id,n_id查是否已读
        with self.get_db() as session:
            nu_is_read = session.query(UserNotice.nu_is_read).filter(
                UserNotice.n_id == n_id, UserNotice.u_id == u_id).first()
            session.commit()
            return 1 if nu_is_read is not None else 0
