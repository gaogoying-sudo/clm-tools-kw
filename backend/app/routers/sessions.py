"""
会话管理 API
- 同步当天数据并创建会话
- 获取工程师的待填写会话（节点式问题流）
- 推送飞书消息
"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Engineer, SyncTask, DailySession, SessionTask, Question, Answer, ExperienceCandidate
from ..schemas import SessionOut, SessionDetailOut, SyncTaskOut, FlowNodeOut, AnswerOut, EngineerOut
from ..sync_service import sync_today_tasks
from ..question_engine import (
    detect_signals,
    select_flow_questions,
    select_questions,
    should_send,
    build_trigger_summary,
    ENTRY_OPTION_TO_EVENT,
)
from ..config import settings
from ..feishu import build_task_summary_card, send_feishu_card, send_feishu_card_to_chat

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/today/list", summary="获取今天所有会话")
def list_today_sessions(db: Session = Depends(get_db)):
    today = date.today()
    sessions = db.query(DailySession).filter(DailySession.session_date == today).all()

    result = []
    for s in sessions:
        engineer = db.query(Engineer).filter(Engineer.id == s.engineer_id).first()
        task_ids = [st.sync_task_id for st in s.session_tasks]
        tasks = db.query(SyncTask).filter(SyncTask.id.in_(task_ids)).all()
        result.append({
            "session_id": s.id,
            "engineer": EngineerOut.model_validate(engineer) if engineer else None,
            "status": s.status,
            "task_count": len(tasks),
            "total_exec": sum(t.exec_count for t in tasks),
            "failed_count": sum(1 for t in tasks if t.status == "failed"),
            "question_count": s.question_count,
        })

    return result


@router.post("/sync-today", summary="同步今天的录菜数据并创建会话")
def sync_and_create_sessions(db: Session = Depends(get_db)):
    """
    1. 从后台拉取/生成当天录菜数据
    2. 为每个工程师检测信号
    3. 创建会话并关联任务和问题
    """
    today = date.today()

    # Step 1: 同步任务数据
    tasks = sync_today_tasks(db, today)

    # Step 2: 按工程师分组
    engineer_tasks = {}
    for t in tasks:
        engineer_tasks.setdefault(t.engineer_id, []).append(t)

    results = []
    for eng_id, eng_tasks in engineer_tasks.items():
        # 检查是否已有会话
        existing = db.query(DailySession).filter(
            DailySession.engineer_id == eng_id,
            DailySession.session_date == today,
        ).first()
        if existing:
            results.append({"engineer_id": eng_id, "session_id": existing.id, "status": "already_exists"})
            continue

        # 信号检测
        signals = detect_signals(eng_tasks)
        if not should_send(signals):
            results.append({"engineer_id": eng_id, "status": "no_tasks_skip"})
            continue

        flow_nodes = select_flow_questions(db, signals, root_event_type=None)
        trigger_summary = build_trigger_summary(signals)

        # 任务摘要快照
        summary_snapshot = [
            {"dish_name": t.dish_name, "recipe_id": t.recipe_id, "exec_count": t.exec_count, "status": t.status}
            for t in eng_tasks
        ]

        session = DailySession(
            engineer_id=eng_id,
            session_date=today,
            status="pending",
            question_count=len(flow_nodes),
            summary_snapshot=summary_snapshot,
            generated_flow_version="v1",
            trigger_summary=trigger_summary,
            flow_status="active",
        )
        db.add(session)
        db.flush()

        for t in eng_tasks:
            st = SessionTask(session_id=session.id, sync_task_id=t.id)
            db.add(st)

        db.commit()
        db.refresh(session)
        results.append({"engineer_id": eng_id, "session_id": session.id, "status": "created", "question_count": len(flow_nodes)})

    return {"date": str(today), "sessions": results}

@router.post("/dev/reset-today", summary="（开发用）清空今天会话/回答，便于重复验收")
def dev_reset_today(db: Session = Depends(get_db)):
    """
    开发/演示辅助：清空“今天”的会话与回答，让前端可以从头再走一遍。

    安全边界：
    - 仅允许在 DEBUG=true 且使用 mock 数据时执行（避免误删真实环境数据）
    """
    if not settings.DEBUG or not settings.use_mock_data:
        raise HTTPException(status_code=403, detail="dev reset disabled")

    today = date.today()
    sessions = db.query(DailySession).filter(DailySession.session_date == today).all()
    session_ids = [s.id for s in sessions]
    if not session_ids:
        return {"success": True, "deleted_sessions": 0, "deleted_answers": 0, "deleted_candidates": 0}

    deleted_candidates = db.query(ExperienceCandidate).filter(
        ExperienceCandidate.session_id.in_(session_ids)
    ).delete(synchronize_session=False)

    deleted_answers = db.query(Answer).filter(
        Answer.session_id.in_(session_ids)
    ).delete(synchronize_session=False)

    db.query(SessionTask).filter(
        SessionTask.session_id.in_(session_ids)
    ).delete(synchronize_session=False)

    deleted_sessions = db.query(DailySession).filter(
        DailySession.id.in_(session_ids)
    ).delete(synchronize_session=False)

    db.commit()
    return {
        "success": True,
        "date": str(today),
        "deleted_sessions": deleted_sessions,
        "deleted_answers": deleted_answers,
        "deleted_candidates": deleted_candidates,
    }


@router.get("/{session_id}", response_model=SessionDetailOut, summary="获取会话详情(含任务+问题流)")
def get_session_detail(
    session_id: int,
    root_event_type: Optional[str] = Query(None, description="入口题答案对应事件类型，用于过滤分支题"),
    db: Session = Depends(get_db),
):
    session = db.query(DailySession).filter(DailySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    engineer = db.query(Engineer).filter(Engineer.id == session.engineer_id).first()
    task_ids = [st.sync_task_id for st in session.session_tasks]
    tasks = db.query(SyncTask).filter(SyncTask.id.in_(task_ids)).all() if task_ids else []
    signals = detect_signals(tasks)

    # 优先用 session 已存的 root_event_type，其次从入口题回答推断
    rt = root_event_type or session.root_event_type
    if not rt:
        for a in db.query(Answer).filter(Answer.session_id == session_id).all():
            q = db.query(Question).filter(Question.id == a.question_id).first()
            if q and q.question_key == "q_entry":
                raw = a.raw_input or a.answer_json or a.answer_text
                if isinstance(raw, str):
                    rt = ENTRY_OPTION_TO_EVENT.get(raw)
                break

    flow_nodes = select_flow_questions(db, signals, root_event_type=rt)
    questions_out = [FlowNodeOut.model_validate(n) for n in flow_nodes]

    answers = db.query(Answer).filter(Answer.session_id == session_id).all()

    return SessionDetailOut(
        id=session.id,
        engineer_id=session.engineer_id,
        session_date=session.session_date,
        status=session.status,
        question_count=len(questions_out),
        pushed_at=session.pushed_at,
        submitted_at=session.submitted_at,
        duration_seconds=session.duration_seconds,
        engineer=EngineerOut.model_validate(engineer),
        tasks=[SyncTaskOut.model_validate(t) for t in tasks],
        questions=questions_out,
        answers=[AnswerOut.model_validate(a) for a in answers],
        root_event_type=rt,
    )


@router.post("/{session_id}/push", summary="推送飞书消息")
async def push_session(
    session_id: int,
    db: Session = Depends(get_db),
    dry_run: bool = Query(True, description="是否仅模拟发送（默认 true）"),
):
    """推送飞书消息
    
    Args:
        session_id: 会话 ID
        dry_run: 是否仅模拟发送（默认 true，安全保护）
    
    安全保护：
    - 默认 dry_run=true，不实际发送消息
    - 需要配置 FEISHU_TEST_WHITELIST 才能发送真实消息
    - 非白名单 user_id 直接拒绝
    """
    session = db.query(DailySession).filter(DailySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    engineer = db.query(Engineer).filter(Engineer.id == session.engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="工程师不存在")
    
    task_ids = [st.sync_task_id for st in session.session_tasks]
    tasks = db.query(SyncTask).filter(SyncTask.id.in_(task_ids)).all()

    # 构造卡片
    tasks_dict = [{"dish_name": t.dish_name, "recipe_id": t.recipe_id, "recipe_type": t.recipe_type,
                    "exec_count": t.exec_count, "cooking_time": t.cooking_time,
                    "customer_name": t.customer_name, "status": t.status} for t in tasks]
    card = build_task_summary_card(engineer.name, tasks_dict)

    # 发送
    fill_url = f"/fill/{session_id}"  # 前端填写页地址
    result = await send_feishu_card(engineer.feishu_user_id, card, fill_url, dry_run=dry_run)

    # 仅在真实发送成功时更新状态
    if result.get("success") and not result.get("dry_run"):
        session.status = "pushed"
        session.pushed_at = datetime.now()
        db.commit()

    return {
        "success": result.get("success", False),
        "session_id": session_id,
        "dry_run": result.get("dry_run", True),
        "message": result.get("message", ""),
        "blocked": result.get("blocked", False),
        "payload": result.get("payload") if result.get("dry_run") else None,
        "api_endpoint": result.get("api_endpoint") if result.get("dry_run") else None,
        "fill_url": result.get("fill_url") if result.get("dry_run") else None,
    }


@router.post("/{session_id}/push-to-test-group", summary="推送飞书消息到测试群（安全模式）")
async def push_to_test_group(
    session_id: int,
    db: Session = Depends(get_db),
    dry_run: bool = Query(True, description="是否仅模拟发送（默认 true）"),
):
    """推送飞书消息到测试群（公司环境安全模式）
    
    Args:
        session_id: 会话 ID
        dry_run: 是否仅模拟发送（默认 true，安全保护）
    
    安全保护：
    - 仅发送到 FEISHU_TEST_CHAT_ID 配置的群聊
    - 默认 dry_run=true，不实际发送消息
    - 测试群模式开启时，禁止向个人 user_id 发送
    """
    if not settings.FEISHU_TEST_CHAT_ID:
        raise HTTPException(
            status_code=400,
            detail="未配置 FEISHU_TEST_CHAT_ID，无法使用测试群发送模式"
        )
    
    session = db.query(DailySession).filter(DailySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    task_ids = [st.sync_task_id for st in session.session_tasks]
    tasks = db.query(SyncTask).filter(SyncTask.id.in_(task_ids)).all()
    
    # 构造简化卡片（测试群消息）
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "🧪 CLM 录菜复盘助手 · 测试消息"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**测试消息**：这是 session_id={session_id} 的测试推送。"
                }
            },
            {
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "打开填写页"},
                    "type": "primary",
                    "url": "{{fill_url}}"
                }]
            }
        ]
    }
    
    # 发送到测试群
    fill_url = f"/fill/{session_id}"
    result = await send_feishu_card_to_chat(settings.FEISHU_TEST_CHAT_ID, card, fill_url, dry_run=dry_run)
    
    return {
        "success": result.get("success", False),
        "session_id": session_id,
        "dry_run": result.get("dry_run", True),
        "message": result.get("message", ""),
        "blocked": result.get("blocked", False),
        "payload": result.get("payload") if result.get("dry_run") else None,
        "api_endpoint": result.get("api_endpoint") if result.get("dry_run") else None,
        "fill_url": result.get("fill_url") if result.get("dry_run") else None,
        "target_chat_id": settings.FEISHU_TEST_CHAT_ID,
        "target_type": "chat"
    }
