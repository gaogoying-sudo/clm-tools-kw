from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, datetime


# === Engineer ===
class EngineerOut(BaseModel):
    id: int
    name: str
    role: str
    region: str
    feishu_user_id: Optional[str] = None

    class Config:
        from_attributes = True


# === SyncTask ===
class SyncTaskOut(BaseModel):
    id: int
    task_date: date
    recipe_id: Optional[int] = None
    dish_name: str
    group_name: str
    recipe_version: int
    recipe_type: int
    pot_type: int
    cooking_time: int
    max_power: int
    picture: str
    customer_name: str
    device_id: str
    power_trace: List[Any]
    ingredients_timeline: List[Any]
    ingredient_notes: List[Any]
    exec_count: int
    status: str
    has_abnormal: bool
    modifications: List[str]
    exec_time: str

    class Config:
        from_attributes = True


# === Question ===
class QuestionOut(BaseModel):
    id: int
    question_key: str
    question_type: str
    title: str
    subtitle: str
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    is_triggered: bool
    trigger_rule: str
    trigger_context: Optional[str] = None
    sort_order: int
    is_active: bool = True

    class Config:
        from_attributes = True


# 问题流节点（含 node_type, related_event_type）
class FlowNodeOut(BaseModel):
    id: int
    question_key: str
    question_type: str
    title: str
    subtitle: str = ""
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    node_type: str = "branch"
    source_type: str = "branch"
    related_event_type: Optional[str] = None
    trigger_context: Optional[str] = None
    display_order: int = 0
    is_triggered: bool = False


class QuestionCreateRequest(BaseModel):
    question_key: str
    question_type: str
    title: str
    subtitle: str = ""
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    is_triggered: bool = False
    trigger_rule: str = ""
    trigger_priority: int = 0
    sort_order: int = 0
    is_active: bool = True
    node_type: str = "branch"
    source_type: str = "branch"
    related_event_type: Optional[str] = None
    display_order: int = 0


class QuestionUpdateRequest(BaseModel):
    question_type: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    is_triggered: Optional[bool] = None
    trigger_rule: Optional[str] = None
    trigger_priority: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    node_type: Optional[str] = None
    source_type: Optional[str] = None
    related_event_type: Optional[str] = None
    display_order: Optional[int] = None


# === Session ===
class SessionOut(BaseModel):
    id: int
    engineer_id: int
    session_date: date
    status: str
    question_count: int
    pushed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class SessionDetailOut(SessionOut):
    engineer: EngineerOut
    tasks: List[SyncTaskOut] = []
    questions: List[FlowNodeOut] = []
    answers: List["AnswerOut"] = []
    root_event_type: Optional[str] = None


# === Answer ===
class AnswerSubmit(BaseModel):
    question_key: str
    answer_type: str = "text"
    answer_text: Optional[str] = None
    answer_json: Optional[Any] = None
    related_task_id: Optional[int] = None


class AnswerOut(BaseModel):
    id: int
    question_id: int
    answer_type: str
    answer_text: Optional[str] = None
    answer_json: Optional[Any] = None
    related_task_id: Optional[int] = None
    answered_at: datetime

    class Config:
        from_attributes = True


class SubmitSessionRequest(BaseModel):
    answers: List[AnswerSubmit]
    duration_seconds: Optional[int] = None


# === ExperienceCandidate ===
class CandidateOut(BaseModel):
    id: int
    answer_id: int
    session_id: int
    category: str
    status: str
    summary: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateUpdateRequest(BaseModel):
    category: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None
    reviewed_by: Optional[str] = None


# === Admin Dashboard ===
class DashboardStats(BaseModel):
    total_engineers: int
    sessions_today: int
    submitted_today: int
    recovery_rate: float
    pending_candidates: int


class EngineerSessionSummary(BaseModel):
    engineer: EngineerOut
    task_count: int
    total_exec: int
    failed_count: int
    session_status: Optional[str] = None
    session_id: Optional[int] = None
