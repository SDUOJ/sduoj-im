from sqlalchemy import (
    Column,
    DateTime,
    VARCHAR,
    func, Boolean, BigInteger, UniqueConstraint, )

from model.db import Base


class Websocket(Base):
    __tablename__ = 'oj_websocket'
    w_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    username = Column(VARCHAR(63), nullable=False, index=True, comment='用户名')
    w_token = Column(VARCHAR(32), unique=True, nullable=False, index=True, comment='session唯一识别串')  # token，非空，唯一
    w_is_closed = Column(Boolean, nullable=False, default=False, index=True, comment='是否关闭, 0.正常工作, 1.已断开')
    w_gmt_create = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')
    w_gmt_modified = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(),
                            comment='修改时间')
    w_features = Column(VARCHAR(64), nullable=False, default='', comment='特性字段')


class Missed(Base):
    __tablename__ = 'oj_missed'
    ms_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    username = Column(VARCHAR(63), nullable=False, index=True, comment='用户名')
    ms_key = Column(VARCHAR(32), unique=True, nullable=False, index=True, comment='错过消息的索引eg:(notice-1或者message-1)')
    ms_read = Column(Boolean, nullable=False, default=False, index=True, comment='是否重新接收到')
    ms_gmt_create = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')
    ms_gmt_modified = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(),
                             comment='修改时间')
    ms_features = Column(VARCHAR(64), nullable=False, default='', comment='特性字段')
    __table_args__ = (
        UniqueConstraint('username', 'ms_key', name='ms_user'),)
