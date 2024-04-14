from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    VARCHAR,
    ForeignKey, Date, Index, Float, event, func, BigInteger, SmallInteger,
)
from sqlalchemy.orm import relationship

from model.db import Base


class Notice(Base):  # 通知表
    __tablename__ = 'oj_notice'
    n_id = Column(BigInteger, primary_key=True, nullable=False, unique=True)
    n_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now())
    n_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now())
    n_features = Column(VARCHAR(64), nullable=True, unique=False, index=False)
    n_is_deleted = Column(SmallInteger, nullable=False, unique=False, index=False, default=0)
    u_id = Column(BigInteger, nullable=False, unique=False, index=False)
    p_id = Column(BigInteger, nullable=True, unique=False, index=True)
    ct_id = Column(BigInteger, nullable=True, unique=False, index=True)
    # u_id = Column(Integer, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=False)
    # p_id = Column(Integer, ForeignKey('oj_problem.p_id'), nullable=True, unique=False, index=True)
    # ct_id = Column(Integer, ForeignKey('oj_contest.ct_id'), nullable=True, unique=False, index=True)
    n_title = Column(VARCHAR(100), nullable=False, unique=False, index=False)
    n_content = Column(VARCHAR(200), nullable=False, unique=False, index=False)
