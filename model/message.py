from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    VARCHAR,
    ForeignKey, Date, Index, Float, event, func, Boolean, BigInteger, UniqueConstraint, SmallInteger,
)
from sqlalchemy.orm import relationship

from model.db import Base


class Message(Base):
    __tablename__ = 'oj_message'
    m_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="消息ID")
    m_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, server_default=func.now(),
                          comment="创建时间")
    m_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, server_default=func.now(),
                            onupdate=func.now(), comment="修改时间")
    m_features = Column(VARCHAR(64), nullable=False, default='', comment='特性字段')
    m_is_deleted = Column(Boolean, nullable=False, default=False, comment='是否删除, 0.否, 1.是')
    username = Column(VARCHAR(63), nullable=False, comment='用户名')
    m_content = Column(VARCHAR(512), nullable=False, unique=False, index=False, comment="消息内容")
    mg_id = Column(BigInteger, ForeignKey('oj_message_group.mg_id'), nullable=False, unique=False, index=True,
                   comment="群聊组ID")


class MessageGroup(Base):
    __tablename__ = 'oj_message_group'
    mg_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="群聊组ID")
    mg_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, server_default=func.now(),
                           comment="创建时间")
    mg_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, server_default=func.now(),
                             onupdate=func.now(), comment="修改时间")
    mg_is_deleted = Column(Boolean, nullable=False, default=False, comment='是否删除, 0.否, 1.是')
    ct_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="用户组考试ID")
    e_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="用户组比赛ID")
    psid = Column(BigInteger, nullable=True, unique=False, index=True, comment="用户组题单ID")
    username = Column(VARCHAR(63), nullable=False, comment='用户名')
    __table_args__ = (
        UniqueConstraint('ct_id', 'username', name='ct_u_uc'), UniqueConstraint('e_id', 'username', name='e_u_uc'))


class UserMessage(Base):
    __tablename__ = 'oj_message_user'
    mu_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="用户消息ID")
    mu_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, server_default=func.now(),
                           comment="创建时间")
    username = Column(VARCHAR(63), nullable=False, index=True, comment='用户名')
    m_id = Column(BigInteger, ForeignKey('oj_message.m_id'), index=True, nullable=False, unique=False, comment="消息ID")
    mu_is_read = Column(SmallInteger, nullable=False, unique=False, index=False, default=1, comment="是否已读")
    __table_args__ = (
        UniqueConstraint('username', 'm_id', name='u_m'),)

# class MessageUnRead(Base):
#     __tablename__ = 'oj_messageunread'
#     mur_id = Column(BigInteger, primary_key=True, nullable=False, unique=True)
#     e_id = Column(BigInteger, nullable=True, unique=False, index=True)
#     ct_id = Column(BigInteger, nullable=True, unique=False, index=True)
#     m_from = Column(BigInteger, nullable=False, unique=False, index=True)
#     m_to = Column(BigInteger, nullable=False, unique=False, index=True)
#     # e_id = Column(Integer, ForeignKey('oj_problem.e_id'), nullable=True, unique=False, index=True)
#     # ct_id = Column(Integer, ForeignKey('oj_contest.ct_id'), nullable=True, unique=False, index=True)
#     # m_from = Column(Integer, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)
#     # m_to = Column(Integer, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)
#     last_read_messae_id = Column(BigInteger)
#     count = Column(Integer)


# 私聊表
# class Message(Base):
#     __tablename__ = 'oj_message'
#     m_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="消息ID")
#     m_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
#                           comment="创建时间")
#     m_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
#                             comment="修改时间")
#     m_from = Column(BigInteger, nullable=False, unique=False, index=True, comment="发件人ID")
#     m_to = Column(BigInteger, nullable=False, unique=False, index=True, comment="收件人ID")
#     m_content = Column(VARCHAR(200), nullable=False, unique=False, index=False, comment="消息内容")
#     mg_id = Column(BigInteger, ForeignKey('oj_message_group.gm_id'), nullable=True, unique=False, index=True,
