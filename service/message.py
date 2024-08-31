from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc, or_, and_, case, not_
from model.db import dbSession
from type.message import message_add_interface, message_group_add_interface
from type.notice import base_interface
from model.message import Message, MessageGroup, UserMessage
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import aliased


class MessageModel(dbSession):

    def add_message(self, obj: message_add_interface):  # 添加一条消息
        obj_dict = jsonable_encoder(obj)
        obj_add = Message(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return obj_add.m_gmt_create.strftime('%Y-%m-%d %H:%M:%S'), obj_add.m_id

    def get_message(self, mg_id: int, messageNum: int, last_m_id: int = None):
        with self.get_db() as session:
            messages = session.query(Message.username, Message.m_id, Message.m_content, Message.m_gmt_create).filter(
                Message.mg_id == mg_id
            )
            if last_m_id is not None:
                messages = messages.filter(Message.m_id < last_m_id)
            messages = messages.order_by(desc(Message.m_gmt_create)).all()
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

    def get_message_list(self, username: str, base: base_interface, is_TA_admin):
        with self.get_db() as session:
            # 子查询：获取每个用户组的最新消息的ID
            subquery = session.query(
                Message.mg_id,
                func.max(Message.m_id).label("latest_id")
            ).group_by(Message.mg_id).subquery()

            # 主查询：联接消息表和子查询以获取最新消息的内容和时间
            MessageAlias = aliased(Message)  # 使用别名以避免冲突
            query = session.query(
                MessageGroup.mg_id,
                MessageAlias.m_content,
                MessageAlias.m_id,
                MessageAlias.m_gmt_create.label("latest_time")
            ).join(subquery, MessageAlias.m_id == subquery.c.latest_id) \
                .join(MessageGroup, MessageGroup.mg_id == MessageAlias.mg_id)

            # 添加过滤条件
            if is_TA_admin == 1:
                query = query.filter(
                    or_(
                        and_(MessageGroup.e_id == base.e_id, base.e_id is not None),
                        and_(MessageGroup.ct_id == base.ct_id, base.ct_id is not None),
                        and_(MessageGroup.psid == base.psid, base.psid is not None)
                    )
                )
            else:
                query = query.filter(
                    or_(
                        and_(MessageGroup.e_id == base.e_id, base.e_id is not None),
                        and_(MessageGroup.ct_id == base.ct_id, base.ct_id is not None),
                        and_(MessageGroup.psid == base.psid, base.psid is not None)
                    ),
                    MessageGroup.username == username
                )

            messages = query.all()

            # 生成JSON响应
            messages_json = []
            for msg in messages:
                messages_json.append({
                    'm_id': msg.m_id,
                    'mg_id': msg.mg_id,
                    'm_last_content': msg.m_content,
                    'm_gmt_create': msg.latest_time.strftime('%Y-%m-%d %H:%M:%S') if msg.latest_time else None
                })

            session.commit()
            return messages_json

    def get_message_by_id(self, m_id: int):
        with self.get_db() as session:
            message = session.query(Message.username, Message.m_content, Message.m_gmt_create, Message.mg_id).filter(
                Message.m_id == m_id
            ).first()
            message_get = {'username': message.username, 'm_content': message.m_content,
                           'm_gmt_create': message.m_gmt_create.strftime('%Y-%m-%d %H:%M:%S'), 'mg_id': message.mg_id,
                           'm_id': m_id}
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

    def get_mg_by_id(self, mg_id: int, mode: int):
        with self.get_db() as session:
            result = session.query(MessageGroup.username, MessageGroup.ct_id, MessageGroup.e_id, MessageGroup.psid).filter(
                MessageGroup.mg_id == mg_id
            ).first()
            session.commit()
            if result is None:
                if mode == 0:
                    raise HTTPException(status_code=404, detail='群聊组不存在')
            return result

    def get_username_by_mg_id(self, mg_id: int):
        with self.get_db() as session:
            result = session.query(MessageGroup.username).filter(
                MessageGroup.mg_id == mg_id
            ).first()
            session.commit()
            if result is None:
                raise HTTPException(status_code=404, detail='群聊组不存在')
            return result[0]

    def get_ct_e_id(self, mg_id):
        with self.get_db() as session:
            res = session.query(MessageGroup.ct_id, MessageGroup.e_id, MessageGroup.psid).filter(
                MessageGroup.mg_id == mg_id).first()
            session.commit()
            return res

    def get_ct_e_id_by_m(self, m_id):
        with self.get_db() as session:
            res = session.query(MessageGroup.ct_id, MessageGroup.e_id, MessageGroup.psid).outerjoin(Message,
                                                                                 MessageGroup.mg_id == Message.mg_id).filter(
                Message.m_id == m_id).first()
            session.commit()
            return res

    def get_mg_id(self, base: base_interface, username: str):
        with self.get_db() as session:
            mg_id = session.query(
                MessageGroup.mg_id
            ).filter(
                or_(
                    and_(base.e_id is not None, MessageGroup.e_id == base.e_id),
                    and_(base.ct_id is not None, MessageGroup.ct_id == base.ct_id),
                    and_(base.psid is not None, MessageGroup.psid == base.psid)
                ),
                MessageGroup.username == username
            ).first()
            return mg_id


class MessageUserModel(dbSession):
    def add_message_all_users(self, inpage_users: list, m_id: int):  # 添加很多用户消息记录
        objects = [UserMessage(**jsonable_encoder({'username': inpage_users[i]['username'], 'm_id': m_id})) for i in
                   range(len(inpage_users))]
        with self.get_db() as session:
            session.add_all(objects)
            session.commit()
            return True

    def add_message_users(self, username: str, m_id: int):  # 添加一个用户消息记录
        object = UserMessage(**jsonable_encoder({'username': username, 'm_id': m_id}))
        with self.get_db() as session:
            session.add(object)
            session.commit()
            return True

    def judge_read(self, m_id, username):
        with self.get_db() as session:
            res = session.query(UserMessage.mu_is_read).filter(
                UserMessage.m_id == m_id, UserMessage.username == username).first()
            session.commit()
            return res
