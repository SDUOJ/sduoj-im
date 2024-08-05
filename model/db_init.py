from sqlalchemy import create_engine
from message import Message, MessageGroup, UserMessage
from notice import Notice, UserNotice
from const import SQLALCHEMY_DATABASE_URL
from websocket import Websocket, Missed
create_table_list = [MessageGroup, Message, Notice, UserNotice, Websocket, Missed, UserMessage
                     ]

if __name__ == "__main__":
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    for tb in create_table_list:
        tb.__table__.create(bind=engine, checkfirst=True)
