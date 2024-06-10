from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc, or_, and_, case
from model.db import dbSession
from type.message import message_add_interface, message_get_interface
from type.notice import base_interface
from model.message import Message


class MessageModel(dbSession):

    def add_message(self, obj: message_add_interface):  # 添加一条消息
        obj_dict = jsonable_encoder(obj)
        obj_add = Message(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return obj_add.m_gmt_create, obj_add.m_id

    def get_message(self, m_from: int, message_get: message_get_interface):
        with self.get_db() as session:
            messages = session.query(Message).filter(
                or_(
                    and_(Message.p_id == message_get.p_id, message_get.p_id is not None),
                    and_(Message.ct_id == message_get.ct_id, message_get.ct_id is not None)
                ),
                or_(
                    and_(Message.m_from == m_from, Message.m_to == message_get.m_to),
                    and_(Message.m_from == message_get.m_to, Message.m_to == m_from)
                )
            ).order_by(Message.m_gmt_create).all()

            messages_json = []
            for msg in messages:
                msg_dict = {
                    'm_from': msg.m_from,
                    'm_content': msg.m_content,
                    'm_gmt_create': msg.m_gmt_create.strftime('%Y-%m-%d %H:%M:%S')
                }
                messages_json.append(msg_dict)

            session.commit()
            return messages_json

    def get_message_list(self, m_from: int, base: base_interface):
        with self.get_db() as session:
            messages = session.query(
                Message.m_to,
                func.max(Message.m_gmt_create).label("latest_time")
            ).filter(
                or_(
                    and_(Message.p_id == base.p_id, base.p_id is not None),
                    and_(Message.ct_id == base.ct_id, base.ct_id is not None)
                ),
                Message.m_from == m_from
            ).group_by(Message.m_to).all()
            messages_json = []
            for msg in messages:
                messages_json.append({'m_to': msg.m_to,
                                      'm_gmt_create': msg[1].strftime('%Y-%m-%d %H:%M:%S')})

                session.commit()
            return messages_json
