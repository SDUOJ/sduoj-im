from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc, or_, and_, case, not_
from model.db import dbSession
from model.group import Contest, Exam, ProblemSet
from model.websocket import Websocket, Missed
from type.websocket import websocket_add_interface, missed_add_interface


class ContestExamModel(dbSession):
    def get_role_group(self, ct_id: int = None, e_id: int = None, psid: int = None):
        with self.get_db() as session:
            if ct_id is not None:
                role_group_id = session.query(Contest.g_id).filter(
                    Contest.ct_id == ct_id
                ).first()
            elif e_id is not None:
                role_group_id = session.query(Exam.g_id).filter(
                    Exam.e_id == e_id
                ).first()
            elif psid is not None:
                role_group_id = session.query(ProblemSet.manageGroupId).filter(
                    ProblemSet.psid == psid
                ).first()

            session.commit()
            if psid is not None:
                return role_group_id
            return role_group_id[0]

    def get_ps_groups(self, psid):
        with self.get_db() as session:
            group_ids = session.query(ProblemSet.groupId).filter(
                ProblemSet.psid == psid
            ).all()
            session.commit()
            return group_ids


class WebsocketModel(dbSession):
    def build_ws_connect(self, obj: websocket_add_interface):  # 建立一条连接
        obj_dict = jsonable_encoder(obj)
        obj_add = Websocket(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return True

    def close_by_token(self, token: str):
        with self.get_db() as session:
            session.query(Websocket).filter(
                Websocket.w_token == token
            ).update({"w_is_closed": True})
            session.commit()
            return True

    def get_token_by_username_browser(self, username: str, browser_id):  # 根据username, browser_id获取token
        with self.get_db() as session:
            token = session.query(Websocket.w_token).filter(
                Websocket.username == username, Websocket.w_browser == browser_id, Websocket.w_is_closed == 0).first()
            session.commit()
            return token

    def get_username_by_token(self, token: str):  # 根据token获取username
        with self.get_db() as session:
            username = session.query(Websocket.username).filter(
                Websocket.w_token == token, Websocket.w_is_closed == 0).first()
            session.commit()
            return username


class MissedModel(dbSession):
    def add_missed(self, obj: missed_add_interface):
        obj_dict = jsonable_encoder(obj)
        obj_add = Missed(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return obj_add.ms_id

    def update_read(self, ms_id):
        with self.get_db() as session:
            session.query(Missed).filter(
                Missed.ms_id == ms_id
            ).update({"ms_read": True})
            session.commit()
            return True

    def get_key_by_username(self, username: str):
        with self.get_db() as session:
            ms_keys = session.query(Missed.ms_key, Missed.ms_id).filter(
                Missed.ms_read == 0, Missed.username == username).all()
            session.commit()
            return ms_keys
