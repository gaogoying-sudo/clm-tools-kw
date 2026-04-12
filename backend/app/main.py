from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
import os
import logging

from .config import settings
from .routers import sessions, answers, admin
from .routers import search

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone=settings.PUSH_TIMEZONE)


def daily_sync_job():
    """每日定时同步任务：拉数据 + 创建会话"""
    from .database import SessionLocal
    from .sync_service import sync_today_tasks
    from .question_engine import detect_signals, select_flow_questions, should_send, build_trigger_summary
    from .models import DailySession, SessionTask

    logger.info("⏰ 定时同步任务开始执行")
    db = SessionLocal()
    try:
        today = date.today()
        tasks = sync_today_tasks(db, today)

        engineer_tasks = {}
        for t in tasks:
            engineer_tasks.setdefault(t.engineer_id, []).append(t)

        created = 0
        for eng_id, eng_tasks in engineer_tasks.items():
            existing = db.query(DailySession).filter(
                DailySession.engineer_id == eng_id,
                DailySession.session_date == today,
            ).first()
            if existing:
                continue

            signals = detect_signals(eng_tasks)
            if not should_send(signals):
                continue

            flow_nodes = select_flow_questions(db, signals, root_event_type=None)
            trigger_summary = build_trigger_summary(signals)
            summary_snapshot = [{"dish_name": t.dish_name, "recipe_id": t.recipe_id, "exec_count": t.exec_count, "status": t.status} for t in eng_tasks]

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
                db.add(SessionTask(session_id=session.id, sync_task_id=t.id))

            created += 1

        db.commit()
        logger.info(f"⏰ 定时同步完成: 创建了 {created} 个会话")
    except Exception as e:
        logger.error(f"⏰ 定时同步失败: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .init_db import init_db
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    hour, minute = settings.PUSH_TIME.split(":")
    scheduler.add_job(
        daily_sync_job, "cron",
        hour=int(hour), minute=int(minute),
        id="daily_sync", replace_existing=True,
    )
    scheduler.start()
    logger.info(f"⏰ 定时任务已启动: 每天 {settings.PUSH_TIME} 自动同步")

    yield

    scheduler.shutdown(wait=False)
    logger.info("⏰ 定时任务已停止")


app = FastAPI(
    title="CLM 录菜复盘助手",
    description="一线口味工程师经验回传工具 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions.router)
app.include_router(answers.router)
app.include_router(admin.router)
app.include_router(search.router)


@app.get("/")
def root():
    return {
        "name": "CLM 录菜复盘助手",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "mock_mode": settings.use_mock_data,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# 如果前端构建产物存在，挂载静态文件
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
