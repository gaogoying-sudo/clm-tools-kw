"""
管理后台 API
- 仪表盘统计
- 回收记录查看
- 经验候选管理
- 问题模板管理
- 数据导出
"""
import csv
import io
from datetime import date, datetime
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from ..config import settings
from ..database import get_db
from ..models import (
    Engineer, SyncTask, DailySession, SessionTask,
    Answer, Question, ExperienceCandidate
)
from ..schemas import (
    DashboardStats, EngineerOut, CandidateOut, CandidateUpdateRequest,
    QuestionOut, QuestionCreateRequest, QuestionUpdateRequest
)

def require_admin(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    """
    Optional admin auth guard.
    When settings.ADMIN_TOKEN is set, /api/admin/* requires matching X-Admin-Token header.
    """
    if not settings.ADMIN_TOKEN:
        return
    if not x_admin_token or x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ============================================================
# Dashboard
# ============================================================

@router.get("/dashboard", response_model=DashboardStats, summary="仪表盘统计")
def get_dashboard(target_date: Optional[str] = None, db: Session = Depends(get_db)):
    d = date.fromisoformat(target_date) if target_date else date.today()

    total_engineers = db.query(Engineer).filter(Engineer.is_active == True).count()
    sessions = db.query(DailySession).filter(DailySession.session_date == d).all()
    sessions_today = len(sessions)
    submitted = sum(1 for s in sessions if s.status == "submitted")
    rate = (submitted / sessions_today * 100) if sessions_today > 0 else 0.0
    pending_candidates = db.query(ExperienceCandidate).filter(
        ExperienceCandidate.status.in_(["draft", "pending_review"])
    ).count()

    return DashboardStats(
        total_engineers=total_engineers,
        sessions_today=sessions_today,
        submitted_today=submitted,
        recovery_rate=round(rate, 1),
        pending_candidates=pending_candidates,
    )


# ============================================================
# Engineers
# ============================================================

@router.get("/engineers", summary="工程师列表及当日状态")
def list_engineers(target_date: Optional[str] = None, db: Session = Depends(get_db)):
    d = date.fromisoformat(target_date) if target_date else date.today()
    engineers = db.query(Engineer).filter(Engineer.is_active == True).all()

    result = []
    for eng in engineers:
        tasks = db.query(SyncTask).filter(
            SyncTask.task_date == d,
            SyncTask.engineer_id == eng.id,
        ).all()

        session = db.query(DailySession).filter(
            DailySession.session_date == d,
            DailySession.engineer_id == eng.id,
        ).first()

        result.append({
            "engineer": EngineerOut.model_validate(eng),
            "task_count": len(tasks),
            "total_exec": sum(t.exec_count for t in tasks),
            "failed_count": sum(1 for t in tasks if t.status == "failed"),
            "session_status": session.status if session else None,
            "session_id": session.id if session else None,
        })

    return result


# ============================================================
# Session answers
# ============================================================

@router.get("/sessions/{session_id}/answers", summary="查看某个会话的完整问答")
def get_session_answers(session_id: int, db: Session = Depends(get_db)):
    session = db.query(DailySession).filter(DailySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    engineer = db.query(Engineer).filter(Engineer.id == session.engineer_id).first()
    answers = db.query(Answer).filter(Answer.session_id == session_id).all()

    qa_list = []
    for a in answers:
        question = db.query(Question).filter(Question.id == a.question_id).first()
        qa_list.append({
            "question_key": question.question_key if question else "?",
            "question_title": question.title if question else "?",
            "question_type": question.question_type if question else "?",
            "is_triggered": question.is_triggered if question else False,
            "answer_type": a.answer_type,
            "answer_text": a.answer_text,
            "answer_json": a.answer_json,
            "related_task_id": a.related_task_id,
            "answered_at": a.answered_at.isoformat() if a.answered_at else None,
        })

    from ..question_engine import ROOT_EVENT_TO_POOL
    pool = ROOT_EVENT_TO_POOL.get(session.root_event_type or "", "daily_record")

    return {
        "session_id": session_id,
        "engineer_name": engineer.name if engineer else "?",
        "session_date": session.session_date.isoformat(),
        "status": session.status,
        "submitted_at": session.submitted_at.isoformat() if session.submitted_at else None,
        "duration_seconds": session.duration_seconds,
        "summary_snapshot": session.summary_snapshot or [],
        "root_event_type": session.root_event_type,
        "pool": pool,
        "qa_list": qa_list,
    }


# ============================================================
# Experience candidates
# ============================================================

@router.get("/candidates", summary="经验候选列表")
def list_candidates(
    status: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(ExperienceCandidate)
    if status:
        q = q.filter(ExperienceCandidate.status == status)
    if category:
        q = q.filter(ExperienceCandidate.category == category)

    total = q.count()
    items = q.order_by(ExperienceCandidate.created_at.desc()).offset((page - 1) * size).limit(size).all()

    result = []
    for c in items:
        answer = db.query(Answer).filter(Answer.id == c.answer_id).first()
        session = db.query(DailySession).filter(DailySession.id == c.session_id).first()
        engineer = db.query(Engineer).filter(Engineer.id == session.engineer_id).first() if session else None

        result.append({
            "id": c.id,
            "category": c.category,
            "status": c.status,
            "summary": c.summary,
            "engineer_name": engineer.name if engineer else "?",
            "session_date": session.session_date.isoformat() if session else None,
            "reviewed_by": c.reviewed_by,
            "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"total": total, "page": page, "size": size, "items": result}


@router.patch("/candidates/{candidate_id}", summary="更新经验候选状态")
def update_candidate(candidate_id: int, req: CandidateUpdateRequest, db: Session = Depends(get_db)):
    c = db.query(ExperienceCandidate).filter(ExperienceCandidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="候选不存在")

    if req.category is not None:
        c.category = req.category
    if req.status is not None:
        c.status = req.status
    if req.summary is not None:
        c.summary = req.summary
    if req.reviewed_by is not None:
        c.reviewed_by = req.reviewed_by
        c.reviewed_at = datetime.now()

    db.commit()
    db.refresh(c)
    return {"success": True, "id": c.id, "status": c.status}


# ============================================================
# Question template management
# ============================================================

@router.get("/questions", summary="获取所有问题模板")
def list_questions(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.sort_order).all()
    return [QuestionOut.model_validate(q) for q in questions]


@router.post("/questions", summary="创建问题模板")
def create_question(req: QuestionCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(Question).filter(Question.question_key == req.question_key).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"question_key '{req.question_key}' 已存在")

    q = Question(
        question_key=req.question_key,
        question_type=req.question_type,
        title=req.title,
        subtitle=req.subtitle,
        options=req.options,
        placeholder=req.placeholder,
        is_triggered=req.is_triggered,
        trigger_rule=req.trigger_rule,
        trigger_priority=req.trigger_priority,
        sort_order=req.sort_order,
        is_active=req.is_active,
        node_type=req.node_type,
        source_type=req.source_type,
        related_event_type=req.related_event_type,
        display_order=req.display_order,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return QuestionOut.model_validate(q)


@router.put("/questions/{question_id}", summary="更新问题模板")
def update_question(question_id: int, req: QuestionUpdateRequest, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="问题不存在")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(q, field, value)

    q.updated_at = datetime.now()
    db.commit()
    db.refresh(q)
    return QuestionOut.model_validate(q)


@router.delete("/questions/{question_id}", summary="删除问题模板")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="问题不存在")

    has_answers = db.query(Answer).filter(Answer.question_id == question_id).count() > 0
    if has_answers:
        q.is_active = False
        q.updated_at = datetime.now()
        db.commit()
        return {"success": True, "action": "deactivated", "reason": "已有回答数据，改为禁用"}

    db.delete(q)
    db.commit()
    return {"success": True, "action": "deleted"}


# ============================================================
# Data export
# ============================================================

@router.get("/export", summary="导出回收数据为CSV")
def export_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    d_start = date.fromisoformat(start_date) if start_date else date.today()
    d_end = date.fromisoformat(end_date) if end_date else d_start

    sessions = db.query(DailySession).filter(
        DailySession.session_date >= d_start,
        DailySession.session_date <= d_end,
        DailySession.status == "submitted",
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "日期", "工程师", "区域", "会话状态", "填写耗时(秒)",
        "问题编号", "问题类型", "问题标题", "是否触发题",
        "回答类型", "回答文本", "回答选项", "关联菜品ID",
    ])

    for s in sessions:
        engineer = db.query(Engineer).filter(Engineer.id == s.engineer_id).first()
        answers = db.query(Answer).filter(Answer.session_id == s.id).all()

        for a in answers:
            question = db.query(Question).filter(Question.id == a.question_id).first()
            answer_display = a.answer_text or ""
            if a.answer_json:
                if isinstance(a.answer_json, list):
                    answer_display = " | ".join(str(x) for x in a.answer_json)
                elif isinstance(a.answer_json, dict):
                    parts = [f"{k}={v}" for k, v in a.answer_json.items()]
                    answer_display = " | ".join(parts)
                else:
                    answer_display = str(a.answer_json)

            writer.writerow([
                s.session_date.isoformat(),
                engineer.name if engineer else "?",
                engineer.region if engineer else "",
                s.status,
                s.duration_seconds or "",
                question.question_key if question else "?",
                question.question_type if question else "?",
                question.title if question else "?",
                "是" if (question and question.is_triggered) else "否",
                a.answer_type,
                a.answer_text or "",
                answer_display if a.answer_json else "",
                a.related_task_id or "",
            ])

    output.seek(0)
    filename = f"clm_review_{d_start}_{d_end}.csv"

    return StreamingResponse(
        iter(["\ufeff" + output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============================================================
# History — list sessions by date range
# ============================================================

@router.get("/history", summary="按日期范围查看历史会话")
def list_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    d_start = date.fromisoformat(start_date) if start_date else date.today()
    d_end = date.fromisoformat(end_date) if end_date else d_start

    sessions = db.query(DailySession).filter(
        DailySession.session_date >= d_start,
        DailySession.session_date <= d_end,
    ).order_by(DailySession.session_date.desc()).all()

    result = []
    for s in sessions:
        engineer = db.query(Engineer).filter(Engineer.id == s.engineer_id).first()
        task_ids = [st.sync_task_id for st in s.session_tasks]
        tasks = db.query(SyncTask).filter(SyncTask.id.in_(task_ids)).all() if task_ids else []

        result.append({
            "session_id": s.id,
            "session_date": s.session_date.isoformat(),
            "engineer": EngineerOut.model_validate(engineer) if engineer else None,
            "status": s.status,
            "task_count": len(tasks),
            "total_exec": sum(t.exec_count for t in tasks),
            "failed_count": sum(1 for t in tasks if t.status == "failed"),
            "question_count": s.question_count,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "duration_seconds": s.duration_seconds,
        })

    return result
