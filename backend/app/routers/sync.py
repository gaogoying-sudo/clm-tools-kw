"""
数据同步 API
- 手动触发同步
- 查看同步状态
- 配置源数据库连接
"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from ..config import settings
from ..database import get_db
from ..models import Engineer, SyncTask, DailySession
from ..sync_service import sync_today_tasks, sync_history_tasks

router = APIRouter(prefix="/api/admin/sync", tags=["sync"])


@router.get("/status", summary="查看数据同步状态")
def get_sync_status(db: Session = Depends(get_db)):
    """返回当前同步状态统计"""
    today = date.today()
    
    # 当天任务数
    today_tasks = db.query(SyncTask).filter(SyncTask.task_date == today).count()
    
    # 历史任务总数
    total_tasks = db.query(SyncTask).count()
    
    # 会话数
    today_sessions = db.query(DailySession).filter(DailySession.session_date == today).count()
    
    # 工程师数
    total_engineers = db.query(Engineer).filter(Engineer.is_active == True).count()
    
    # 最近同步时间
    latest_task = db.query(SyncTask).order_by(SyncTask.synced_at.desc()).first()
    
    return {
        "today_tasks": today_tasks,
        "total_tasks": total_tasks,
        "today_sessions": today_sessions,
        "total_engineers": total_engineers,
        "latest_sync_at": latest_task.synced_at.isoformat() if latest_task else None,
        "use_mock_data": settings.use_mock_data,
        "source_db_configured": bool(
            settings.SOURCE_DB_HOST and 
            settings.SOURCE_DB_USER and 
            settings.SOURCE_DB_PASSWORD
        ),
    }


@router.post("/trigger/today", summary="手动触发当天数据同步")
def trigger_sync_today(
    force: bool = Query(False, description="是否强制重新同步（覆盖已有数据）"),
    db: Session = Depends(get_db),
):
    """
    手动触发当天数据同步
    
    - 如果 use_mock_data=true，生成模拟数据
    - 如果 use_mock_data=false 且源数据库已配置，从真实数据源拉取
    """
    if force:
        # 删除当天已有数据
        db.query(SyncTask).filter(SyncTask.task_date == date.today()).delete()
        db.query(DailySession).filter(DailySession.session_date == date.today()).delete()
        db.commit()
    
    tasks = sync_today_tasks(db)
    
    return {
        "success": True,
        "synced_tasks": len(tasks),
        "sync_date": date.today().isoformat(),
        "mode": "mock" if settings.use_mock_data else "real",
    }


@router.post("/trigger/history", summary="手动触发历史数据同步")
def trigger_sync_history(
    days: int = Query(30, ge=1, le=365, description="同步最近 N 天的数据"),
    db: Session = Depends(get_db),
):
    """
    手动触发历史数据同步（仅 mock 模式支持）
    
    注意：真实数据源同步需要配置 SOURCE_DB_* 环境变量
    """
    if settings.use_mock_data:
        total = sync_history_tasks(db, days_back=days)
        return {
            "success": True,
            "synced_tasks": total,
            "days": days,
            "mode": "mock",
        }
    else:
        raise HTTPException(
            status_code=501,
            detail="真实数据源的历史同步尚未实现，请先使用 mock 模式",
        )


@router.get("/config", summary="查看数据源配置状态")
def get_source_config():
    """返回源数据库配置状态（不返回敏感信息）"""
    return {
        "use_mock_data": settings.use_mock_data,
        "source_db_host": settings.SOURCE_DB_HOST or "(未配置)",
        "source_db_port": settings.SOURCE_DB_PORT or 3306,
        "source_db_user": settings.SOURCE_DB_USER or "(未配置)",
        "configured": bool(
            settings.SOURCE_DB_HOST and 
            settings.SOURCE_DB_USER and 
            settings.SOURCE_DB_PASSWORD
        ),
        "hint": "配置 SOURCE_DB_HOST, SOURCE_DB_PORT, SOURCE_DB_USER, SOURCE_DB_PASSWORD 环境变量以启用真实数据同步",
    }
