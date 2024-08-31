from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    VARCHAR,
    ForeignKey, Date, Index, Float, event, func, Boolean, BigInteger, Text, String, SmallInteger, LargeBinary,
)
from sqlalchemy.orm import relationship

from model.db import Base


class Contest(Base):
    __tablename__ = 'oj_contest'

    ct_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    ct_gmt_create = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    ct_gmt_modified = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(),
                             comment='修改时间')
    ct_features = Column(String(3072), nullable=False, default='', comment='特性字段')
    ct_is_deleted = Column(Boolean, nullable=False, default=False, comment='是否删除, 0.否, 1.是')
    ct_is_public = Column(Boolean, nullable=False, default=False, comment='比赛公开, 0否, 1是')
    ct_version = Column(Integer, nullable=False, default=0, comment='乐观锁字段')
    ct_title = Column(String(64), nullable=False, comment='比赛标题')
    u_id = Column(BigInteger, nullable=False, comment='创建者id')
    ct_gmt_start = Column(DateTime, nullable=False, comment='比赛开始时间')
    ct_gmt_end = Column(DateTime, nullable=False, comment='比赛结束时间')
    ct_password = Column(String(64), nullable=False, default='', comment='参加密码')
    ct_source = Column(String(64), nullable=False, default='', comment='比赛来源')
    ct_participant_num = Column(Integer, nullable=False, default=0, comment='参加人数')
    ct_markdown_description = Column(Text, nullable=True, comment='比赛描述')
    ct_problems = Column(Text, nullable=False, comment='比赛题目设置, 包含(p_id,pd_id,title,score)')
    ct_participants = Column(LargeBinary, nullable=True, comment='参加者id集合')
    ct_unofficial_participants = Column(LargeBinary, nullable=True, comment='挂星参加者id集合，是参加者的子集')
    g_id = Column(BigInteger, nullable=True, default=None, comment='权限用户组id')
    ct_clarification_template = Column(String(4096), nullable=True, default=None)

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
        'comment': '比赛表'
    }


class Exam(Base):
    __tablename__ = 'oj_exam'

    e_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    e_gmt_create = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    e_gmt_modified = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(),
                            comment='修改时间')
    e_is_deleted = Column(Boolean, nullable=False, default=False, comment='是否删除, 0.否, 1.是')
    e_version = Column(Integer, nullable=False, default=0, comment='乐观锁字段')
    e_features = Column(String(3072), nullable=False, default='', comment='特性字段')
    e_gmt_start = Column(DateTime, nullable=False, comment='考试开始时间')
    e_gmt_end = Column(DateTime, nullable=False, comment='考试结束时间')
    e_title = Column(String(64), nullable=False, comment='考试标题')
    e_markdown_description = Column(Text, nullable=True, comment='考试描述')
    e_problem = Column(Text, nullable=False, comment='考试题目中的题目')
    e_participants = Column(LargeBinary, nullable=True, comment='考试参加者的id')
    e_participant_num = Column(Integer, nullable=False, default=0, comment='参加人数')
    u_id = Column(BigInteger, nullable=False, comment='创建者id')
    g_id = Column(BigInteger, nullable=True, default=None, comment='权限用户组id')

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_0900_ai_ci',
        'comment': '考试表'
    }


class ProblemSet(Base):
    __tablename__ = 'problem_set'

    # 表字段定义
    psid = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(63), nullable=False, comment='名称')
    description = Column(Text, nullable=True, comment='描述')
    type = Column(Integer, nullable=False, comment='类型')
    groupInfo = Column(Text, nullable=False, comment='群组信息')
    config = Column(Text, nullable=False, comment='配置')
    global_score = Column(Float, nullable=True, default=None, comment='全局分数')
    tm_start = Column(DateTime, nullable=True, default=None, comment='开始时间')
    tm_end = Column(DateTime, nullable=True, default=None, comment='结束时间')
    username = Column(String(63), nullable=False, comment='用户名')
    manageGroupId = Column(Integer, nullable=True, default=None, comment='管理组ID')
    groupId = Column(Integer, nullable=False, comment='组ID')
    tag = Column(String(63), nullable=False, comment='标签')

    # 索引定义
    __table_args__ = (
        Index('ix_problem_set_groupId_tag_type', 'groupId', 'tag', 'type'),
    )