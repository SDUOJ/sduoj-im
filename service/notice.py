from typing import List

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc
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
            return obj_add.nt_id, obj_add.nt_gmt_create.strftime('%Y-%m-%d %H:%M:%S')

    def delete_notice(self, nt_id: int):
        with self.get_db() as session:
            session.query(Notice).filter(Notice.nt_id == nt_id).update(
                {"nt_is_deleted": 1})
            session.commit()

    def update_notice(self, notice_update: notice_update_interface):
        with self.get_db() as session:
            timenow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            up_username = session.query(Notice.up_username).filter(Notice.nt_id == notice_update.nt_id,
                                                                   Notice.nt_is_deleted == 0).first()
            if up_username:
                session.query(Notice).filter(Notice.nt_id == notice_update.nt_id).update(
                    {
                        "nt_title": notice_update.nt_title,
                        "nt_content": notice_update.nt_content,
                        "up_username": up_username.up_username + f',{notice_update.up_username}',
                        "nt_gmt_modified": timenow
                    }
                )
                session.commit()
                return timenow, up_username.up_username + f',{notice_update.up_username}'

    def get_notice_list_id_by_p_ct(self, page, noticelist_get: base_interface):  # 根据e_id,ct_id查询notice的列表
        with self.get_db() as session:
            if noticelist_get.e_id is not None:
                ses = session.query(Notice.nt_id).filter(
                    Notice.e_id == noticelist_get.e_id, Notice.nt_is_deleted == 0)
            elif noticelist_get.ct_id is not None:
                ses = session.query(Notice.nt_id).filter(
                    Notice.ct_id == noticelist_get.ct_id, Notice.nt_is_deleted == 0)
            elif noticelist_get.psid is not None:
                ses = session.query(Notice.nt_id).filter(
                    Notice.psid == noticelist_get.psid, Notice.nt_is_deleted == 0)
            counts = ses.count()
            ses = ses.order_by(
                desc(Notice.nt_gmt_modified)).all()
            ses = ses[page.offset():page.offset() + page.limit()]
            session.commit()
            notice_ids = [id_tuple[0] for id_tuple in ses]
            return notice_ids, counts

    def get_ct_e_id(self, nt_id):
        with self.get_db() as session:
            res = session.query(Notice.ct_id, Notice.e_id, Notice.psid).filter(
                Notice.nt_id == nt_id, Notice.nt_is_deleted == 0).first()
            session.commit()
            if res is None:
                raise HTTPException(detail="Notice Not Found", status_code=404)
            return res

    def get_notice_list_by_ids(self, ids):  # 根据 id 查询 notice 的列表
        with self.get_db() as session:
            # 查询指定 id 的记录
            ses = session.query(Notice.nt_id, Notice.nt_gmt_create, Notice.nt_gmt_modified, Notice.username,
                                Notice.up_username,
                                Notice.nt_content,
                                Notice.nt_title, Notice.e_id, Notice.ct_id, Notice.psid).filter(
                Notice.nt_is_deleted == 0,
                Notice.nt_id.in_(ids)  # 过滤条件：nt_id 在给定的 ids 列表中
            ).all()

            # 将查询结果转换为字典列表
            notice_json = []
            for record in ses:
                temp_dict = {
                    'nt_id': record.nt_id,
                    'nt_gmt_create': record.nt_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                    'nt_gmt_modified': record.nt_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'username': record.username,
                    'up_username': record.up_username,
                    'nt_content': record.nt_content,
                    'nt_title': record.nt_title
                }
                if record.e_id is not None:  # 如果 e_id 不为空，则添加到结果字典
                    temp_dict['e_id'] = record.e_id

                if record.ct_id is not None:  # 如果 ct_id 不为空，则添加到结果字典
                    temp_dict['ct_id'] = record.ct_id

                if record.psid is not None:  # 如果 ps_id 不为空，则添加到结果字典
                    temp_dict['psid'] = record.psid
                notice_json.append(temp_dict)

            session.commit()
            return notice_json

    # def get_notice_list_by_p_ct(self, page, noticelist_get: base_interface):  # 根据e_id,ct_id查询notice的列表
    #     with self.get_db() as session:
    #         if noticelist_get.e_id is not None:
    #             ses = session.query(Notice.nt_id, Notice.nt_gmt_create, Notice.nt_gmt_modified, Notice.u_id,
    #                                 Notice.nt_title,
    #                                 Notice.n_read_user).filter(
    #                 Notice.e_id == noticelist_get.e_id, Notice.nt_is_deleted == 0)
    #         elif noticelist_get.ct_id is not None:
    #             ses = session.query(Notice.nt_id, Notice.nt_gmt_create, Notice.nt_gmt_modified, Notice.u_id,
    #                                 Notice.nt_title,
    #                                 Notice.n_read_user).filter(
    #                 Notice.ct_id == noticelist_get.ct_id, Notice.nt_is_deleted == 0)
    #         counts = ses.count()
    #         ses = ses.order_by(
    #             desc(Notice.nt_gmt_modified)).all()
    #         ses = ses[page.offset():page.offset() + page.limit()]
    #         notice_json = []
    #         for ses in ses:
    #             notice_json.append({
    #                 'nt_id': ses.nt_id,
    #                 'nt_gmt_create': ses.nt_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
    #                 'nt_gmt_modified': ses.nt_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
    #                 'u_id': ses.u_id,
    #                 'nt_title': ses.nt_title,
    #                 'n_read_user': ses.n_read_user,
    #             })
    #
    #         session.commit()
    #         return notice_json, counts

    def get_notice_by_nt_id(self, nt_id):  # 根据nt_id查询notice的基本信息
        with self.get_db() as session:

            ses = session.query(Notice.nt_gmt_create, Notice.nt_gmt_modified, Notice.username, Notice.up_username,
                                Notice.nt_title,
                                Notice.nt_content, Notice.e_id, Notice.ct_id, Notice.psid).filter(
                Notice.nt_id == nt_id, Notice.nt_is_deleted == 0).first()
            res = None
            if ses is not None:
                res = {
                    'nt_gmt_create': ses.nt_gmt_create.strftime('%Y-%m-%d %H:%M:%S'),
                    'nt_gmt_modified': ses.nt_gmt_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'username': ses.username,
                    'up_username': ses.up_username,
                    'nt_title': ses.nt_title,
                    'nt_content': ses.nt_content,
                    'nt_id': nt_id
                }
                if ses.e_id is not None:  # 如果 e_id 不为空，则添加到结果字典
                    res['e_id'] = ses.e_id

                if ses.ct_id is not None:  # 如果 ct_id 不为空，则添加到结果字典
                    res['ct_id'] = ses.ct_id

                if ses.psid is not None:  # 如果 psid 不为空，则添加到结果字典
                    res['psid'] = ses.psid
            session.commit()
            return res

    def get_notice_content_by_nt_id(self, nt_id):  # 根据nt_id查询notice的content
        with self.get_db() as session:
            content = session.query(Notice.nt_content).filter(
                Notice.nt_id == nt_id, Notice.nt_is_deleted == 0).first()
            session.commit()
            return content


class UserNoticeModel(dbSession):
    def add_user_notice(self, nt_id: int, username: str):  # 添加已读记录
        obj = notice_user_add_interface(nt_id=nt_id, username=username)
        obj_dict = jsonable_encoder(obj)
        obj_add = UserNotice(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.flush()
            session.commit()
            return obj_add.nu_id

    def judge_exist_by_u_n(self, username: str, nt_id: int):  # 根据username,nt_id查是否已读
        with self.get_db() as session:
            nu_is_read = session.query(UserNotice.nu_is_read).filter(
                UserNotice.nt_id == nt_id, UserNotice.username == username).first()
            session.commit()
            return 1 if nu_is_read is not None else 0
