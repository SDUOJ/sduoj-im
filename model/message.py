from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    VARCHAR,
    ForeignKey, Date, Index, Float, event, func, Boolean,
)

from model.db import Base

class Message(Base):
    __tablename__ = 'oj_message'
    m_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    m_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now())
    m_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now())
    p_id = Column(Integer, ForeignKey('oj_problem.p_id'), nullable=True, unique=False, index=True)
    ct_id = Column(Integer, ForeignKey('oj_contest.ct_id'), nullable=True, unique=False, index=True)
    m_from = Column(Integer, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)
    m_to = Column(Integer, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=True)
    m_content = Column(VARCHAR(200), nullable=False, unique=False, index=False)
    m_is_read = Column(Boolean, nullable=False, unique=False, index=False, default=0)
