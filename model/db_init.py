from sqlalchemy import create_engine
from message import Message
from notice import Notice
from const import SQLALCHEMY_DATABASE_URL

create_table_list = [Notice, Message
                     ]

if __name__ == "__main__":
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    for tb in create_table_list:
        tb.__table__.create(bind=engine, checkfirst=True)
