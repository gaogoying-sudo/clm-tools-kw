from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, Date, DateTime,
    Float, JSON, ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship
from .database import Base
import enum


# === Enums ===
class SessionStatus(str, enum.Enum):
    pending = "pending"
    pushed = "pushed"
    submitted = "submitted"
    expired = "expired"


class CandidateCategory(str, enum.Enum):
    experience = "experience"       # 经验候选池
    failure_case = "failure_case"   # 异常/失败池
    tuning_record = "tuning_record" # 调优记录
    customer_pref = "customer_pref" # 需求/客户反馈池
    delivery_issue = "delivery_issue"  # 交付问题池
    rule_candidate = "rule_candidate"  # 规则候选
    template_patch = "template_patch"  # 模板补充
    daily_record = "daily_record"   # 普通记录池


class CandidateStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    verified = "verified"
    invalid = "invalid"


# === 1. 工程师表 ===
class Engineer(Base):
    __tablename__ = "engineers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feishu_user_id = Column(String(100), unique=True, nullable=True, comment="飞书用户ID")
    name = Column(String(50), nullable=False, comment="姓名")
    role = Column(String(50), default="口味工程师", comment="角色")
    region = Column(String(50), default="", comment="区域")
    is_active = Column(Boolean, default=True, comment="是否在职")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sessions = relationship("DailySession", back_populates="engineer")


# === 2. 同步任务表 (从公司后台拉取的当日录菜记录) ===
class SyncTask(Base):
    __tablename__ = "sync_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_date = Column(Date, nullable=False, comment="任务日期")
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    # 来自 main_recipe
    recipe_id = Column(BigInteger, comment="菜谱ID (对应main_recipe.id)")
    dish_name = Column(String(255), nullable=False, comment="菜名")
    group_name = Column(String(255), default="", comment="标准菜名")
    recipe_version = Column(Integer, default=0, comment="菜谱版本")
    recipe_type = Column(Integer, default=0, comment="菜谱类型 0小份 2大份 7定制")
    pot_type = Column(Integer, default=1, comment="锅型")
    cooking_time = Column(Integer, default=0, comment="烹饪总时长(秒)")
    max_power = Column(Integer, default=12000, comment="最大功率")
    picture = Column(String(500), default="", comment="菜品图片URL")
    # 业务上下文
    customer_name = Column(String(255), default="", comment="客户/门店")
    device_id = Column(String(100), default="", comment="设备编号")
    # cook_steps 解析结果
    power_trace = Column(JSON, default=list, comment="功率轨迹 [{time,power,cmd}]")
    ingredients_timeline = Column(JSON, default=list, comment="投料时序 [{time,type,auto,cmd,name,dosage,unit}]")
    ingredient_notes = Column(JSON, default=list, comment="备菜须知 [{index,desc,img}]")
    # 执行信号
    exec_count = Column(Integer, default=1, comment="执行次数")
    status = Column(String(20), default="passed", comment="passed/failed")
    has_abnormal = Column(Boolean, default=False, comment="是否有异常")
    modifications = Column(JSON, default=list, comment="调整记录")
    exec_time = Column(String(10), default="", comment="执行时间 HH:MM")
    # 来源追踪
    source_record_id = Column(String(100), default="", comment="原系统记录ID,防重复")
    synced_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_sync_date_eng", "task_date", "engineer_id"),
        Index("idx_sync_source", "source_record_id"),
    )


# === 3. 每日回传会话表 ===
class DailySession(Base):
    __tablename__ = "daily_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    session_date = Column(Date, nullable=False, comment="会话日期")
    status = Column(String(20), default=SessionStatus.pending.value, comment="pending/pushed/submitted/expired")
    question_count = Column(Integer, default=5, comment="发送题数")
    pushed_at = Column(DateTime, nullable=True, comment="推送时间")
    submitted_at = Column(DateTime, nullable=True, comment="提交时间")
    duration_seconds = Column(Integer, nullable=True, comment="填写耗时(秒)")
    created_at = Column(DateTime, default=datetime.now)

    # 问题流实例能力
    summary_snapshot = Column(JSON, nullable=True, comment="任务摘要快照")
    root_event_type = Column(String(50), nullable=True, comment="入口题选择的母类: iterative_debugging/customer_feedback/key_adjustment/abnormal_failure/reusable_method/normal_day")
    generated_flow_version = Column(String(20), default="v1", comment="问题流版本")
    trigger_summary = Column(Text, nullable=True, comment="触发信号摘要")
    flow_status = Column(String(20), default="active", comment="流程状态: active/completed")

    engineer = relationship("Engineer", back_populates="sessions")
    session_tasks = relationship("SessionTask", back_populates="session")
    answers = relationship("Answer", back_populates="session")

    __table_args__ = (
        Index("idx_session_date_eng", "session_date", "engineer_id", unique=True),
    )


# === 4. 会话关联任务表 ===
class SessionTask(Base):
    __tablename__ = "session_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("daily_sessions.id"), nullable=False)
    sync_task_id = Column(Integer, ForeignKey("sync_tasks.id"), nullable=False)
    is_focus_task = Column(Boolean, default=False, comment="工程师选中的焦点任务")

    session = relationship("DailySession", back_populates="session_tasks")


# === 5. 问题模板表 ===
class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_key = Column(String(50), unique=True, nullable=False, comment="唯一标识")
    question_type = Column(String(20), nullable=False, comment="single/multi/open/anchor")
    title = Column(String(500), nullable=False, comment="问题标题")
    subtitle = Column(String(200), default="", comment="副标题")
    options = Column(JSON, nullable=True, comment="选项列表")
    placeholder = Column(Text, nullable=True, comment="开放题占位提示")
    is_triggered = Column(Boolean, default=False, comment="是否为触发题")
    trigger_rule = Column(String(200), default="", comment="触发规则标识")
    trigger_priority = Column(Integer, default=0, comment="触发优先级")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 节点能力
    node_type = Column(String(20), default="branch", comment="entry/branch/trigger")
    source_type = Column(String(20), default="fixed", comment="fixed/branch/trigger")
    related_event_type = Column(String(50), nullable=True, comment="分支题关联的入口事件母类")
    visible_if = Column(JSON, nullable=True, comment="可见条件")
    next_rule = Column(String(200), nullable=True, comment="下一节点规则")
    context_bindings = Column(JSON, nullable=True, comment="上下文绑定")
    display_order = Column(Integer, default=0, comment="显示顺序")

    answers = relationship("Answer", back_populates="question")


# === 6. 回答表 ===
class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("daily_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    related_task_id = Column(Integer, ForeignKey("sync_tasks.id"), nullable=True, comment="锚定菜品题关联的任务")
    answer_type = Column(String(20), default="text", comment="text/single/multi/anchor")
    answer_text = Column(Text, nullable=True, comment="兼容: 文本/开放题回答")
    answer_json = Column(JSON, nullable=True, comment="兼容: 选择题/结构化回答")
    answered_at = Column(DateTime, default=datetime.now)

    # 三层存储
    raw_input = Column(JSON, nullable=True, comment="原始输入: 原始选项/原始文本/原始语音引用")
    transcribed_text = Column(Text, nullable=True, comment="中间层: 转写文本/清洗文本")
    structured_result = Column(JSON, nullable=True, comment="结构化层: 归一化答案/标签/分类结果")

    session = relationship("DailySession", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    candidates = relationship("ExperienceCandidate", back_populates="answer")

    __table_args__ = (
        Index("idx_answer_session", "session_id"),
    )


# === 7. 经验候选表 ===
class ExperienceCandidate(Base):
    __tablename__ = "experience_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("daily_sessions.id"), nullable=False)
    category = Column(String(30), default=CandidateCategory.daily_record.value, comment="经验分类")
    status = Column(String(20), default=CandidateStatus.draft.value, comment="draft/pending_review/verified/invalid")
    summary = Column(Text, nullable=True, comment="经验摘要")
    reviewed_by = Column(String(50), nullable=True, comment="审核人")
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    answer = relationship("Answer", back_populates="candidates")
