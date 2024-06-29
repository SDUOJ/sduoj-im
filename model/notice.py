from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import Column, BigInteger, DateTime, func, VARCHAR, SmallInteger, JSON, String, ForeignKey, Index

from model.db import Base


class Notice(Base):  # 通知表
    __tablename__ = 'oj_notification'
    n_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="通知ID")
    n_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                          comment="创建时间")
    n_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                            comment="修改时间")
    n_features = Column(VARCHAR(64), nullable=True, unique=False, index=False, comment="通知特性")
    n_is_deleted = Column(SmallInteger, nullable=False, unique=False, index=False, default=0, comment="是否已删除")
    u_id = Column(BigInteger, nullable=False, unique=False, index=False, comment="用户ID")
    p_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="问题ID")
    ct_id = Column(BigInteger, nullable=True, unique=False, index=True, comment="比赛ID")
    # u_id = Column(BigInteger, ForeignKey('oj_user.u_id'), nullable=False, unique=False, index=False)
    # p_id = Column(BigInteger, ForeignKey('oj_problem.p_id'), nullable=True, unique=False, index=True)
    # ct_id = Column(BigInteger, ForeignKey('oj_contest.ct_id'), nullable=True, unique=False, index=True)
    n_title = Column(VARCHAR(100), nullable=False, unique=False, index=False, comment="通知标题")
    n_content = Column(VARCHAR(200), nullable=False, unique=False, index=False, comment="通知内容")

class UserNotice(Base):
    __tablename__ = 'oj_notification_user'
    __table_args__ = (
        Index('ix_u_id_n_id', "u_id", "n_id"),  # 非唯一的联合索引
    )
    nu_id = Column(BigInteger, primary_key=True, nullable=False, unique=True, comment="用户通知ID")
    nu_gmt_create = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                           comment="创建时间")
    nu_gmt_modified = Column(DateTime, nullable=False, unique=False, index=False, default=func.now(),
                             comment="修改时间")
    u_id = Column(BigInteger, nullable=False, unique=False, index=False, comment="用户ID")
    n_id = Column(BigInteger, ForeignKey('oj_notification.n_id'), nullable=False, unique=False, comment="通知ID")
    nu_is_read = Column(SmallInteger, nullable=False, unique=False, index=False, default=1, comment="是否已读")

# def insert_data():
#     pass

# 创建定时任务
# scheduler = BlockingScheduler()
#
# # 添加定时任务，每晚1点运行插入数据函数
# scheduler.add_job(insert_data, 'cron', hour=1)
#
# # 运行定时任务
# scheduler.start()
