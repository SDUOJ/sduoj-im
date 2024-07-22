from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import Column, BigInteger, DateTime, func, VARCHAR, SmallInteger, JSON, String, ForeignKey, Index

from model.db import Base


class Notice(Base):  # 通知表
    __tablename__ = 'oj_notification'
    nt_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="通知ID")
    nt_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                          comment="创建时间")
    nt_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                            comment="修改时间")
    nt_features = Column(VARCHAR(64), nullable=True, unique=False, index=False, comment="通知特性")
    nt_is_deleted = Column(SmallInteger, nullable=False, unique=False, index=False, default=0, comment="是否已删除")
    u_id = Column(BigInteger, nullable=False, unique=False, index=False, comment="用户ID")
    e_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="问题ID")
    ct_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="比赛ID")
    # u_id = Column(BigInteger, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=False)
    # e_id = Column(BigInteger, ForeignKey('oj_problem.e_id'), nullable=True, unique=False, index=True)
    # ct_id = Column(BigInteger, ForeignKey('oj_contest.ct_id'), nullable=True, unique=False, index=True)
    nt_title = Column(VARCHAR(100), nullable=False, unique=False, index=False, comment="通知标题")
    nt_content = Column(VARCHAR(200), nullable=False, unique=False, index=False, comment="通知内容")

class UserNotice(Base):
    __tablename__ = 'oj_notification_user'
    __table_args__ = (
        Index('ix_u_id_nt_id', "u_id", "nt_id"),  # 非唯一的联合索引
    )
    nu_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="用户通知ID")
    nu_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                           comment="创建时间")
    nu_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                             comment="修改时间")
    u_id = Column(BigInteger, nullable=False, unique=False, index=False, comment="用户ID")
    nt_id = Column(BigInteger, ForeignKey('oj_notification.nt_id'), nullable=False, unique=False, comment="通知ID")
    nu_is_read = Column(SmallInteger, nullable=False, unique=False, index=False, default=1, comment="是否已读")

