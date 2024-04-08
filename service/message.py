from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, join, update, desc
from model.db import dbSession
from type.message import message_add_interface
from model.message import Message



class MessageModel(dbSession):

    def add_message(self, obj: message_add_interface):  # 添加一条消息
        obj_dict = jsonable_encoder(obj)
        obj_add = Message(**obj_dict)
        with self.get_db() as session:
            session.add(obj_add)
            session.commit()
            return obj_add.id

