"""
凡人修仙3w天 — 数据模型定义（唯一真相源）
所有表结构在此定义，其他模块不得重复定义
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, Date, DateTime,
    ForeignKey, Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ============ 用户配置 ============

class UserConfig(Base):
    """用户配置表 — 全局只有一行"""
    __tablename__ = "user_config"

    id = Column(Integer, primary_key=True)
    birth_year = Column(Integer, nullable=False)
    initial_blood = Column(Integer, nullable=False)       # 初始血量（分钟）
    current_blood = Column(Integer, nullable=False)        # 当前血量（分钟）
    current_spirit = Column(Integer, nullable=False, default=0)  # 当前心境值
    target_money = Column(Integer, nullable=False, default=5_000_000)  # 目标灵石
    tongyu_password = Column(String(256), nullable=True)   # 统御系统密码（加密）
    dark_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============ 心境系统 ============

class Task(Base):
    """任务表 — 心境系统的正面任务和心魔任务"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    task_type = Column(String(20), nullable=False)         # positive / demon
    spirit_effect = Column(Integer, nullable=False, default=0)
    blood_effect = Column(Integer, nullable=False, default=0)
    emoji = Column(String(10), default="⭐")
    submission_type = Column(String(20), default="daily_checkin")  # daily_checkin / repeatable
    enable_streak = Column(Boolean, default=False)         # 是否追踪连续打卡
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    records = relationship("TaskRecord", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_task_type", "task_type"),
        Index("idx_task_active", "is_active"),
    )


class TaskRecord(Base):
    """任务完成记录"""
    __tablename__ = "task_records"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    task_name = Column(String(100), nullable=False)        # 冗余存储，防止任务删除后丢失
    spirit_change = Column(Integer, nullable=False, default=0)
    blood_change = Column(Integer, nullable=False, default=0)
    is_undo = Column(Boolean, default=False)               # 是否已撤销
    is_makeup = Column(Boolean, default=False)              # 是否补记
    completed_at = Column(DateTime, default=datetime.now)
    notes = Column(Text, nullable=True)

    task = relationship("Task", back_populates="records")

    __table_args__ = (
        Index("idx_record_task", "task_id"),
        Index("idx_record_date", "completed_at"),
    )


class StreakRecord(Base):
    """连续打卡记录"""
    __tablename__ = "streak_records"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    current_streak = Column(Integer, default=0)            # 当前连续天数
    max_streak = Column(Integer, default=0)                # 最长连续天数
    last_completed_date = Column(Date, nullable=True)      # 最后完成日期
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============ 境界系统 ============

class Realm(Base):
    """境界表"""
    __tablename__ = "realms"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    realm_type = Column(String(20), default="main")        # main / dungeon
    completion_rate = Column(Integer, default=100)          # 完成条件百分比
    reward_spirit = Column(Integer, default=0)             # 奖励心境值
    reward_description = Column(Text, nullable=True)       # 奖励描述
    status = Column(String(20), default="active")          # active / completed / archived
    order_index = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    skills = relationship("Skill", back_populates="realm", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_realm_status", "status"),
        Index("idx_realm_type", "realm_type"),
    )


class Skill(Base):
    """技能/大任务表"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    realm_id = Column(Integer, ForeignKey("realms.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    realm = relationship("Realm", back_populates="skills")
    sub_tasks = relationship("SubTask", back_populates="skill", cascade="all, delete-orphan")


class SubTask(Base):
    """子任务表"""
    __tablename__ = "sub_tasks"

    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    name = Column(String(200), nullable=False)
    order_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    skill = relationship("Skill", back_populates="sub_tasks")


# ============ 灵石系统 ============

class Transaction(Base):
    """收支记录表"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)              # income / expense
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    transaction_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_transaction_type", "type"),
        Index("idx_transaction_date", "transaction_date"),
        Index("idx_transaction_category", "category"),
    )


class RecurringTransaction(Base):
    """固定收支表（月工资、房租等）"""
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)              # income / expense
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    frequency = Column(String(20), default="monthly")      # monthly / weekly
    day_of_month = Column(Integer, nullable=True)          # 每月几号
    is_active = Column(Boolean, default=True)
    last_applied_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Debt(Base):
    """负债表"""
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)             # 房贷、车贷等
    total_amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    monthly_payment = Column(Float, nullable=False)
    interest_rate = Column(Float, default=0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    repayments = relationship("DebtRepayment", back_populates="debt", cascade="all, delete-orphan")


class DebtRepayment(Base):
    """还款记录"""
    __tablename__ = "debt_repayments"

    id = Column(Integer, primary_key=True)
    debt_id = Column(Integer, ForeignKey("debts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    repayment_date = Column(Date, default=date.today)
    notes = Column(Text, nullable=True)

    debt = relationship("Debt", back_populates="repayments")


class Budget(Base):
    """预算表"""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    category = Column(String(50), nullable=False)          # 分类或 "total"
    amount = Column(Float, nullable=False)
    month = Column(String(7), nullable=False)              # "2026-02" 格式
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_budget_month", "month"),
    )


class Milestone(Base):
    """灵石里程碑"""
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    is_reached = Column(Boolean, default=False)
    reached_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


# ============ 统御系统 ============

class Person(Base):
    """人物档案表"""
    __tablename__ = "people"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    met_date = Column(Date, nullable=True)
    birthday = Column(Date, nullable=True)
    contact_info = Column(Text, nullable=True)             # 加密存储
    preferences = Column(Text, nullable=True)              # JSON: 喜好偏好
    notes = Column(Text, nullable=True)                    # 相处要点（手动）
    ai_report = Column(Text, nullable=True)                # AI 生成的相处模板
    avatar_emoji = Column(String(10), default="👤")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    personality_tags = relationship("PersonalityTag", back_populates="person", cascade="all, delete-orphan")
    events = relationship("RelationshipEvent", back_populates="person", cascade="all, delete-orphan")


class PersonalityTag(Base):
    """性格标签表"""
    __tablename__ = "personality_tags"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    category = Column(String(50), nullable=False)          # dimension / communication / custom
    tag_name = Column(String(100), nullable=False)
    tag_value = Column(Integer, nullable=True)             # 滑块值 0-100（dimension 类型用）

    person = relationship("Person", back_populates="personality_tags")


class RelationshipEvent(Base):
    """人际事件记录"""
    __tablename__ = "relationship_events"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    event_date = Column(Date, nullable=False)
    location = Column(String(200), nullable=True)
    event_description = Column(Text, nullable=False)
    impression_tags = Column(Text, nullable=True)          # JSON 列表
    their_emotion = Column(Text, nullable=True)            # JSON 列表
    topics = Column(Text, nullable=True)                   # JSON 列表
    key_info = Column(Text, nullable=True)
    my_feeling = Column(Text, nullable=True)
    next_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    person = relationship("Person", back_populates="events")

    __table_args__ = (
        Index("idx_event_person", "person_id"),
        Index("idx_event_date", "event_date"),
    )


# ============ AI 配置 ============

class AIConfig(Base):
    """AI 提供商配置"""
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False)          # openai / qianwen / wenxin / chatglm / custom
    api_key = Column(Text, nullable=True)                  # 加密存储
    api_base = Column(String(500), nullable=True)
    model = Column(String(100), nullable=True)
    proxy = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


# ============ 建表函数 ============

def create_all_tables(engine):
    """创建所有表"""
    Base.metadata.create_all(engine)
