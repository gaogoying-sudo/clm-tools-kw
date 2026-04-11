"""
回答提交 API
- 三层存储：原始输入 / 转写文本 / 结构化结果
- 按 root_event_type 与内容分类到基础池
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DailySession, Question, Answer, ExperienceCandidate, SessionTask
from ..schemas import SubmitSessionRequest, AnswerOut
from ..question_engine import ENTRY_OPTION_TO_EVENT, ROOT_EVENT_TO_POOL

router = APIRouter(prefix="/api/answers", tags=["answers"])


@router.post("/{session_id}/submit", summary="提交会话回答")
def submit_answers(session_id: int, req: SubmitSessionRequest, db: Session = Depends(get_db)):
    session = db.query(DailySession).filter(DailySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if session.status == "submitted":
        raise HTTPException(status_code=400, detail="该会话已提交过")

    root_event_type = None
    experience_text = None
    saved_answers = []

    for ans in req.answers:
        question = db.query(Question).filter(Question.question_key == ans.question_key).first()
        if not question:
            continue

        raw = ans.answer_text or ans.answer_json

        answer = Answer(
            session_id=session_id,
            question_id=question.id,
            related_task_id=ans.related_task_id,
            answer_type=ans.answer_type,
            answer_text=ans.answer_text,
            answer_json=ans.answer_json,
            raw_input={"text": ans.answer_text, "json": ans.answer_json},
            transcribed_text=ans.answer_text if ans.answer_type == "text" else None,
            structured_result=None,
        )
        db.add(answer)
        db.flush()
        saved_answers.append(answer)

        if question.question_key == "q_entry":
            raw_val = ans.answer_json if ans.answer_type == "single" else ans.answer_text
            if isinstance(raw_val, str):
                root_event_type = ENTRY_OPTION_TO_EVENT.get(raw_val)

        if question.question_key == "q_experience":
            experience_text = ans.answer_text

        if ans.question_key == "q_anchor" and ans.related_task_id:
            st = db.query(SessionTask).filter(
                SessionTask.session_id == session_id,
                SessionTask.sync_task_id == ans.related_task_id,
            ).first()
            if st:
                st.is_focus_task = True

    session.root_event_type = root_event_type
    session.status = "submitted"
    session.submitted_at = datetime.now()
    session.flow_status = "completed"
    if req.duration_seconds:
        session.duration_seconds = req.duration_seconds

    pool = ROOT_EVENT_TO_POOL.get(root_event_type, "daily_record")
    experience_answer_id = None
    for a in saved_answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        if q and q.question_key == "q_experience":
            experience_answer_id = a.id
            break

    if experience_text and experience_answer_id:
        candidate = ExperienceCandidate(
            answer_id=experience_answer_id,
            session_id=session_id,
            category=pool,
            status="draft",
            summary=experience_text,
        )
        db.add(candidate)

    db.commit()

    return {
        "success": True,
        "session_id": session_id,
        "answers_count": len(saved_answers),
        "root_event_type": root_event_type,
        "pool": pool,
    }
