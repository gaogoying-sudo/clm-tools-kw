"""
数据检索 API - 多条件搜索 + 本地缓存
"""
import json
import hashlib
from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..config import settings
from ..database import get_db
from ..models import Engineer, SyncTask, DailySession, SessionTask, Answer, Question
from ..schemas import EngineerOut

router = APIRouter(prefix="/api/admin", tags=["search"])

# Simple in-memory cache
_cache = {}
_CACHE_TTL = 300  # 5 minutes
_CACHE_STATS = {"hits": 0, "misses": 0}


def _cache_key(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cached(key: str):
    if key in _cache:
        data, ts = _cache[key]
        if (datetime.now() - ts).total_seconds() < _CACHE_TTL:
            return data
    return None


def _set_cache(key: str, data):
    _cache[key] = (data, datetime.now())


@router.get("/cache/stats", summary="查看缓存统计")
def get_cache_stats():
    """
    查看缓存命中率、缓存条目数等信息
    """
    total = _CACHE_STATS["hits"] + _CACHE_STATS["misses"]
    hit_rate = (_CACHE_STATS["hits"] / total * 100) if total > 0 else 0
    
    return {
        "cache_entries": len(_cache),
        "hits": _CACHE_STATS["hits"],
        "misses": _CACHE_STATS["misses"],
        "hit_rate_percent": round(hit_rate, 2),
        "ttl_seconds": _CACHE_TTL,
    }


@router.post("/cache/clear", summary="清除所有缓存")
def clear_cache():
    """
    手动清除所有缓存数据
    """
    global _cache
    _cache = {}
    return {"message": "缓存已清除", "cleared_entries": len(_cache)}


@router.get("/search", summary="多条件数据检索")
def search_data(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    engineer_id: Optional[int] = Query(None),
    engineer_name: Optional[str] = Query(None),
    dish_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    has_abnormal: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    多条件检索：
    - 先查本地缓存
    - 当天数据标记"进行中"，不直接用
    - 历史已检索数据本地直接返回
    """
    today = date.today()
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "engineer_id": engineer_id,
        "engineer_name": engineer_name,
        "dish_name": dish_name,
        "status": status,
        "has_abnormal": has_abnormal,
        "page": page,
        "size": size,
    }

    # Check if searching today's data
    is_today_search = (start_date == str(today) or end_date == str(today) or
                       (start_date is None and end_date is None))

    # Try cache (not for today's data)
    if not is_today_search:
        ck = _cache_key(params)
        cached = _get_cached(ck)
        if cached:
            _CACHE_STATS["hits"] += 1
            return {"from_cache": True, **cached}
        _CACHE_STATS["misses"] += 1

    # Build query
    d_start = date.fromisoformat(start_date) if start_date else today - timedelta(days=30)
    d_end = date.fromisoformat(end_date) if end_date else today

    q = db.query(DailySession).filter(
        DailySession.session_date >= d_start,
        DailySession.session_date <= d_end,
    )

    if engineer_id:
        q = q.filter(DailySession.engineer_id == engineer_id)

    if status:
        q = q.filter(DailySession.status == status)

    # Count total
    total = q.count()

    # Get sessions
    sessions = q.order_by(DailySession.session_date.desc()).offset((page - 1) * size).limit(size).all()

    results = []
    for s in sessions:
        engineer = db.query(Engineer).filter(Engineer.id == s.engineer_id).first()

        # Get tasks
        task_ids = [st.sync_task_id for st in s.session_tasks]
        tasks = db.query(SyncTask).filter(SyncTask.id.in_(task_ids)).all() if task_ids else []

        # Apply filters
        if engineer_name and engineer and engineer_name not in engineer.name:
            continue
        if dish_name and not any(dish_name in t.dish_name for t in tasks):
            continue
        if has_abnormal is not None and not any(t.has_abnormal == has_abnormal for t in tasks):
            continue

        results.append({
            "session_id": s.id,
            "session_date": s.session_date.isoformat(),
            "engineer": {
                "id": engineer.id,
                "name": engineer.name,
                "role": engineer.role,
                "region": engineer.region,
            } if engineer else None,
            "status": s.status,
            "task_count": len(tasks),
            "total_exec": sum(t.exec_count for t in tasks),
            "failed_count": sum(1 for t in tasks if t.status == "failed"),
            "question_count": s.question_count,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "duration_seconds": s.duration_seconds,
            "root_event_type": s.root_event_type,
            "tasks": [
                {
                    "id": t.id,
                    "dish_name": t.dish_name,
                    "recipe_id": t.recipe_id,
                    "exec_count": t.exec_count,
                    "status": t.status,
                    "has_abnormal": t.has_abnormal,
                    "customer_name": t.customer_name,
                    "device_id": t.device_id,
                    "exec_time": t.exec_time,
                    "modifications": t.modifications,
                    # 详细数据
                    "power_trace": t.power_trace or [],
                    "ingredients_timeline": t.ingredients_timeline or [],
                    "ingredient_notes": t.ingredient_notes or [],
                    "cook_steps": t.cook_steps or [],
                    "cooking_time": t.cooking_time,
                    "max_power": t.max_power,
                    "recipe_version": t.recipe_version,
                    "recipe_type": t.recipe_type,
                    "pot_type": t.pot_type,
                }
                for t in tasks
            ],
        })

    result = {
        "from_cache": False,
        "is_today_data": is_today_search,
        "total": len(results),
        "total_all": total,
        "page": page,
        "size": size,
        "items": results,
    }

    # Cache (not for today)
    if not is_today_search:
        ck = _cache_key(params)
        _set_cache(ck, result)

    return result


@router.get("/qa-records", summary="原始问答数据查询")
def get_qa_records(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    engineer_id: Optional[int] = Query(None),
    question_key: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    查询原始问答数据（三层：raw_input / transcribed_text / structured_result）
    支持全文搜索关键词
    """
    today = date.today()
    d_start = date.fromisoformat(start_date) if start_date else today - timedelta(days=7)
    d_end = date.fromisoformat(end_date) if end_date else today

    # Join sessions -> answers -> questions
    q = db.query(Answer).join(DailySession, Answer.session_id == DailySession.id).join(
        Question, Answer.question_id == Question.id
    ).filter(
        DailySession.session_date >= d_start,
        DailySession.session_date <= d_end,
    )

    if engineer_id:
        q = q.filter(DailySession.engineer_id == engineer_id)

    if question_key:
        q = q.filter(Question.question_key == question_key)

    if keyword:
        # Search in raw_input, transcribed_text, structured_result
        kw = f"%{keyword}%"
        q = q.filter(
            db.or_(
                Answer.transcribed_text.like(kw),
                Answer.answer_text.like(kw),
            )
        )

    total = q.count()
    answers = q.order_by(Answer.answered_at.desc()).offset((page - 1) * size).limit(size).all()

    records = []
    for a in answers:
        session = db.query(DailySession).filter(DailySession.id == a.session_id).first()
        engineer = db.query(Engineer).filter(Engineer.id == session.engineer_id).first() if session else None
        question = db.query(Question).filter(Question.id == a.question_id).first()

        # Find related task
        related_task = None
        if a.related_task_id:
            related_task = db.query(SyncTask).filter(SyncTask.id == a.related_task_id).first()

        records.append({
            "id": a.id,
            "session_id": a.session_id,
            "session_date": session.session_date.isoformat() if session else None,
            "engineer": {
                "id": engineer.id,
                "name": engineer.name,
            } if engineer else None,
            "question": {
                "key": question.question_key,
                "title": question.title,
                "type": question.question_type,
                "is_triggered": question.is_triggered,
            } if question else None,
            "related_task": {
                "dish_name": related_task.dish_name,
                "recipe_id": related_task.recipe_id,
            } if related_task else None,
            # Three-layer storage
            "raw_input": a.raw_input,
            "transcribed_text": a.transcribed_text,
            "structured_result": a.structured_result,
            "answer_text": a.answer_text,
            "answer_json": a.answer_json,
            "answered_at": a.answered_at.isoformat() if a.answered_at else None,
        })

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": records,
    }


from datetime import timedelta
