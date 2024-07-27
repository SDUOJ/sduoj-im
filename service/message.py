from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc, or_, and_, case, not_
from model.db import dbSession
from type.message import message_add_interface, message_group_add_interface
from type.notice import base_interface
from model.message import Message, MessageGroup


class MessageModel(dbSession):

    def add_message(self, obj: message_add_interface):  # 添加一条消息
        obj_dict = jsonable_encoder(obj)
        obj_add = Message(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return obj_add.m_gmt_create, obj_add.m_id

    def get_message(self, mg_id: int, messageNum: int, last_m_id: int = None):
        with self.get_db() as session:
            messages = session.query(Message.u_id, Message.m_id, Message.m_content, Message.m_gmt_create).filter(
                Message.mg_id == mg_id
            )
            if last_m_id is not None:
                messages = messages.filter(Message.m_id > last_m_id)
            messages = messages.order_by(Message.m_gmt_create).all()
            messages = messages[:messageNum]
            session.commit()
            return messages

    # def get_message(self, m_from: int, messageNum: int, message_get: message_get_interface, last_m_id: int = None):
    #     with self.get_db() as session:
    #         messages = session.query(Message.m_from, Message.m_id, Message.m_content, Message.m_gmt_create).filter(
    #             or_(
    #                 and_(Message.e_id == message_get.e_id, message_get.e_id is not None),
    #                 and_(Message.ct_id == message_get.ct_id, message_get.ct_id is not None)
    #             ),
    #             or_(
    #                 and_(Message.m_from == m_from, Message.m_to == message_get.m_to),
    #                 and_(Message.m_from == message_get.m_to, Message.m_to == m_from)
    #             )
    #         )
    #         if last_m_id is not None:
    #             messages = messages.filter(Message.m_id > last_m_id)
    #         messages = messages.order_by(Message.m_gmt_create).all()
    #         messages = messages[:messageNum]
    #         session.commit()
    #         return messages

    def get_message_list(self, m_from: int, base: base_interface):
        with self.get_db() as session:
            messages = session.query(
                Message.m_content,
                Message.mg_id,
                func.max(Message.m_gmt_create).label("latest_time")
            ).outerjoin(MessageGroup, Message.mg_id == MessageGroup.mg_id).filter(
                or_(
                    and_(MessageGroup.e_id == base.e_id, base.e_id is not None),
                    and_(MessageGroup.ct_id == base.ct_id, base.ct_id is not None)
                ),
                Message.u_id == m_from
            ).group_by(Message.mg_id, Message.m_content).all()
            messages_json = []
            for msg in messages:
                messages_json.append({'mg_id': msg.mg_id, 'm_last_content': msg.m_content,
                                      'm_gmt_create': msg[2].strftime('%Y-%m-%d %H:%M:%S')})

                session.commit()
            return messages_json

    def get_message_by_id(self, m_id: int):
        with self.get_db() as session:
            message = session.query(Message.u_id, Message.m_content, Message.m_gmt_create, Message.mg_id).filter(
                Message.m_id == m_id
            ).first()
            message_get = {'m_from': message.u_id, 'm_content': message.m_content,
                           'm_gmt_create': message.m_gmt_create.strftime('%Y-%m-%d %H:%M:%S'), 'mg_id': message.mg_id}
            session.commit()
            return message_get


class MessageGroupModel(dbSession):
    def add_message_group(self, obj: message_group_add_interface):  # 添加一个聊天组
        obj_dict = jsonable_encoder(obj)
        obj_add = MessageGroup(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return obj_add.mg_id

    def get_mg_by_id(self, mg_id: int):
        with self.get_db() as session:
            result = session.query(MessageGroup.u_id, MessageGroup.ct_id, MessageGroup.e_id).filter(
                MessageGroup.mg_id == mg_id
            ).first()
            session.commit()
            return result

    def get_mg_id(self, base: base_interface):
        with self.get_db() as session:
            mg_id = session.query(
                MessageGroup.mg_id
            ).filter(
                or_(
                    and_(MessageGroup.e_id == base.e_id, base.e_id is not None),
                    and_(MessageGroup.ct_id == base.ct_id, base.ct_id is not None)
                )
            ).first()
            return mg_id
