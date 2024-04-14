from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc, or_, and_, case
from model.db import dbSession
from type.message import message_add_interface, message_get_interface
from type.notice import base_interface
from model.message import Message


class MessageModel(dbSession):
    def __init__(self, m_from=None, m_content=None, m_is_read=None, m_gmt_create=None):
        super().__init__()
        self.m_from = m_from
        self.m_content = m_content
        self.m_is_read = m_is_read
        self.m_gmt_create = m_gmt_create

    def add_message(self, obj: message_add_interface):  # 添加一条消息
        obj_dict = jsonable_encoder(obj)
        obj_add = Message(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return 'ok'

    def get_message(self, m_from: int, message_get: message_get_interface):
        with self.get_db() as session:
            if message_get.p_id is not None:
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
                    if msg.m_to == m_from and msg.m_is_read == 0:
                        msg.m_is_read = True
                    msg_dict = {
                        'm_from': msg.m_from,
                        'm_content': msg.m_content,
                        'm_is_read': msg.m_is_read,
                        'm_gmt_create': msg.m_gmt_create.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    messages_json.append(msg_dict)

                session.commit()
                return messages_json

    def get_message_list(self, m_to: int, base: base_interface):
        with self.get_db() as session:
            subquery = (session.query(
                Message.m_from,
                func.sum(case((Message.m_is_read == 0, 1), else_=0)).label('m_not_read_count'),
                func.max(Message.m_gmt_create).label("latest_time")
            ) .filter(
                    or_(
                        and_(Message.p_id == base.p_id, base.p_id is not None),
                        and_(Message.ct_id == base.ct_id, base.ct_id is not None)
                    ),
                    Message.m_to == m_to
                ).group_by(Message.m_from).subquery())


            messages = session.query(
                Message.m_from,
                subquery.c.m_not_read_count,
                subquery.c.latest_time
            ).join(subquery,
                   and_(Message.m_from == subquery.c.m_from, Message.m_gmt_create == subquery.c.latest_time)).group_by(
                Message.m_from).all()

            messages_json = [
                {
                    'm_to': msg.m_from,
                    'm_not_read_count': int(msg.m_not_read_count),
                    'm_gmt_create': msg[2].strftime('%Y-%m-%d %H:%M:%S')
                } for msg in messages
            ]

            session.commit()
            return messages_json
