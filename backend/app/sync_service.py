"""
数据同步服务

第一版：基于 mock_data_generator 生成近 30 天的真实感数据
后续版本：从公司 MySQL 后台拉取 main_recipe + recipe_detail + cook_steps
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .models import Engineer, SyncTask
from .config import settings


def sync_today_tasks(db: Session, target_date: date = None) -> List[SyncTask]:
    """同步当天录菜任务到 sync_tasks 表"""
    target_date = target_date or date.today()

    if settings.use_mock_data:
        return _generate_mock_tasks(db, target_date)
    else:
        return _pull_from_source(db, target_date)


def sync_history_tasks(db: Session, days_back: int = 30) -> int:
    """同步历史数据（近 N 天）"""
    if not settings.use_mock_data:
        return 0

    from .mock_data_generator import generate_tasks_for_engineer_date

    engineers = db.query(Engineer).filter(Engineer.is_active == True).all()
    today = date.today()
    total_tasks = 0

    for eng in engineers:
        for day_offset in range(1, days_back + 1):
            task_date = today - timedelta(days=day_offset)
            tasks = generate_tasks_for_engineer_date(eng.id, task_date)
            for td in tasks:
                existing = db.query(SyncTask).filter(
                    SyncTask.task_date == td["task_date"],
                    SyncTask.engineer_id == td["engineer_id"],
                    SyncTask.recipe_id == td["recipe_id"],
                ).first()
                if not existing:
                    task = SyncTask(**td)
                    db.add(task)
                    total_tasks += 1

    db.commit()
    return total_tasks


def _pull_from_source(db: Session, target_date: date) -> List[SyncTask]:
    """
    从公司后台 MySQL 拉取数据
    TODO: 对接真实数据库后实现
    查询逻辑：
    - 从 main_recipe + recipe_detail 按 update_time 筛选当天的记录
    - 解析 cook_steps JSON 提取功率轨迹和投料时序
    - 关联 base_ingredients 把 ingredient_id 翻译成食材名称
    - 写入 sync_tasks 表
    """
    raise NotImplementedError("真实数据源对接待开发，当前请使用模拟数据模式")


def _generate_mock_tasks(db: Session, target_date: date) -> List[SyncTask]:
    """基于 mock_data_generator 生成当天的任务数据"""
    # 检查是否已同步过
    existing = db.query(SyncTask).filter(SyncTask.task_date == target_date).count()
    if existing > 0:
        return db.query(SyncTask).filter(SyncTask.task_date == target_date).all()

    from .mock_data_generator import generate_tasks_for_engineer_date

    engineers = db.query(Engineer).filter(Engineer.is_active == True).all()
    if not engineers:
        return []

    all_tasks = []
    for eng in engineers:
        tasks = generate_tasks_for_engineer_date(eng.id, target_date)
        for td in tasks:
            task = SyncTask(**td)
            db.add(task)
            all_tasks.append(task)

    db.commit()
    for t in all_tasks:
        db.refresh(t)

    return all_tasks
