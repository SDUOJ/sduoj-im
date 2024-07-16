from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc, or_, and_, case, not_
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

    def get_message(self, m_from: int, messageNum: int, message_get: message_get_interface, last_m_id: int = None):
        with self.get_db() as session:
            messages = session.query(Message.m_from, Message.m_id, Message.m_content, Message.m_gmt_create).filter(
                or_(
                    and_(Message.p_id == message_get.p_id, message_get.p_id is not None),
                    and_(Message.ct_id == message_get.ct_id, message_get.ct_id is not None)
                ),
                or_(
                    and_(Message.m_from == m_from, Message.m_to == message_get.m_to),
                    and_(Message.m_from == message_get.m_to, Message.m_to == m_from)
                )
            )
            if last_m_id is not None:
                messages = messages.filter(Message.m_id > last_m_id)
            messages = messages.order_by(Message.m_gmt_create).all()
            messages = messages[:messageNum]
            session.commit()
            return messages

    def get_message_list(self, m_from: int, base: base_interface):
        with self.get_db() as session:
            messages = session.query(
                Message.m_to,
                Message.m_content,
                func.max(Message.m_gmt_create).label("latest_time")
            ).filter(
                or_(
                    and_(Message.p_id == base.p_id, base.p_id is not None),
                    and_(Message.ct_id == base.ct_id, base.ct_id is not None)
                ),
                Message.m_from == m_from
            ).group_by(Message.m_to, Message.m_content).all()
            messages_json = []
            for msg in messages:
                messages_json.append({'m_to': msg.m_to, 'm_last_content': msg.m_content,
                                      'm_gmt_create': msg[2].strftime('%Y-%m-%d %H:%M:%S')})

                session.commit()
            return messages_json

    def get_message_by_id(self, m_id: int):
        with self.get_db() as session:
            message = session.query(Message.m_from, Message.m_content, Message.m_gmt_create, Message.p_id,
                                    Message.ct_id).filter(
                Message.m_id == m_id
            ).first()
            message_get = {'m_from': message.m_from, 'm_content': message.m_content,
                           'm_gmt_create': message.m_gmt_create.strftime('%Y-%m-%d %H:%M:%S')}
            if message.p_id is not None:  # 如果 p_id 不为空，则添加到结果字典
                message_get['p_id'] = message.p_id
            if message.ct_id is not None:  # 如果 ctp_id 不为空，则添加到结果字典
                message_get['ct_id'] = message.ct_id
            session.commit()
            return message_get
