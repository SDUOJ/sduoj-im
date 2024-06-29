from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    VARCHAR,
    ForeignKey, Date, Index, Float, event, func, Boolean, BigInteger,
)
from sqlalchemy.orm import relationship

from model.db import Base


class Message(Base):
    __tablename__ = 'oj_message'
    m_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="消息ID")
    m_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                          comment="创建时间")
    m_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                            comment="修改时间")
    p_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="问题ID")
    ct_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="比赛ID")
    m_from = Column(BigInteger, nullable=False, unique=False, index=True, comment="发件人ID")
    m_to = Column(BigInteger, nullable=False, unique=False, index=True, comment="收件人ID")
    m_content = Column(VARCHAR(200), nullable=False, unique=False, index=False, comment="消息内容")
    # p_id = Column(BigInteger, ForeignKey('oj_problem.p_id'), nullable=True, unique=False, index=True)
    # ct_id = Column(BigInteger, ForeignKey('oj_contest.ct_id'), nullable=True, unique=False, index=True)
    # m_from = Column(BigInteger, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)
    # m_to = Column(BigInteger, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)

# class MessageUnRead(Base):
#     __tablename__ = 'oj_messageunread'
#     mur_id = Column(BigInteger, primary_key=True, nullable=False, unique=True)
#     p_id = Column(BigInteger, nullable=True, unique=False, index=True)
#     ct_id = Column(BigInteger, nullable=True, unique=False, index=True)
#     m_from = Column(BigInteger, nullable=False, unique=False, index=True)
#     m_to = Column(BigInteger, nullable=False, unique=False, index=True)
#     # p_id = Column(Integer, ForeignKey('oj_problem.p_id'), nullable=True, unique=False, index=True)
#     # ct_id = Column(Integer, ForeignKey('oj_contest.ct_id'), nullable=True, unique=False, index=True)
#     # m_from = Column(Integer, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)
#     # m_to = Column(Integer, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)
#     last_read_message_id = Column(BigInteger)
#     count = Column(Integer)
