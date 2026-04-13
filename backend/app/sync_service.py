"""
数据同步服务

第一版：基于 mock_data_generator 生成近 30 天的真实感数据
后续版本：从公司 MySQL 后台拉取 main_recipe + recipe_detail + cook_steps
"""
import json
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import Engineer, SyncTask
from .config import settings

logger = logging.getLogger(__name__)


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
    
    查询逻辑：
    - 从 main_recipe + recipe_detail + cook_steps 按 update_time 筛选当天的记录
    - 解析 cook_steps JSON 提取功率轨迹和投料时序
    - 关联 base_ingredients 把 ingredient_id 翻译成食材名称
    - 写入 sync_tasks 表
    
    依赖 data_sync 模块提供数据库连接和工程师映射
    """
    from .data_sync.config import resolve_source_db_config
    from .data_sync.db import connect_source_db, fetch_account_pool
    from .data_sync.engineers import select_engineers
    from .data_sync.mapper import match_accounts, normalize_text
    
    # 检查是否已同步过
    existing = db.query(SyncTask).filter(SyncTask.task_date == target_date).count()
    if existing > 0:
        return db.query(SyncTask).filter(SyncTask.task_date == target_date).all()
    
    # 获取源数据库配置
    try:
        config = resolve_source_db_config()
    except RuntimeError as e:
        logger.error(f"源数据库配置缺失：{e}")
        raise HTTPException(
            status_code=503,
            detail=f"源数据库未配置：{str(e)}。请设置 SOURCE_DB_HOST, SOURCE_DB_USER, SOURCE_DB_PASSWORD 环境变量",
        )
    
    # 获取工程师列表
    engineers = db.query(Engineer).filter(Engineer.is_active == True).all()
    engineer_roster = select_engineers(None)
    
    # 连接源数据库
    conn = connect_source_db(config)
    try:
        pool = fetch_account_pool(conn)
        
        # 构建工程师名字 -> admin_id 映射
        name_to_admin = {}
        for eng_roster in engineer_roster:
            matched = match_accounts(eng_roster, pool)
            if matched:
                # 取第一个匹配结果
                admin_id = matched[0].get('admin_id') or matched[0].get('account_id')
                if admin_id:
                    name_to_admin[normalize_text(eng_roster['name'])] = admin_id
        
        # 查询当天的菜谱数据
        with conn.cursor() as cur:
            # 查询当天更新的 main_recipe 记录
            cur.execute("""
                SELECT 
                    mr.id as recipe_id,
                    mr.dish_name,
                    mr.main_ingredient,
                    mr.status,
                    mr.update_time,
                    mr.admin_id as creator_admin_id,
                    rd.id as detail_id,
                    rd.power_profile,
                    rd.ingredient_sequence,
                    rd.cook_steps_json,
                    rd.exec_count,
                    rd.status as exec_status,
                    rd.exec_time
                FROM btyc.main_recipe mr
                LEFT JOIN btyc.recipe_detail rd ON rd.recipe_id = mr.id
                WHERE DATE(mr.update_time) = %s
                ORDER BY mr.update_time DESC
            """, (target_date.isoformat(),))
            
            recipes = cur.fetchall()
            
            # 转换并插入到 sync_tasks
            all_tasks = []
            for recipe in recipes:
                # 根据 admin_id 查找对应的工程师
                creator_id = recipe.get('creator_admin_id')
                engineer_id = None
                
                for eng in engineers:
                    eng_name_norm = normalize_text(eng.name)
                    if name_to_admin.get(eng_name_norm) == str(creator_id):
                        engineer_id = eng.id
                        break
                
                if not engineer_id:
                    # 未找到匹配的工程师，跳过或标记为未知
                    continue
                
                # 解析 cook_steps JSON
                cook_steps = []
                if recipe.get('cook_steps_json'):
                    try:
                        cook_steps = json.loads(recipe['cook_steps_json'])
                    except (json.JSONDecodeError, TypeError):
                        cook_steps = []
                
                # 创建 SyncTask
                task_data = {
                    "task_date": target_date,
                    "engineer_id": engineer_id,
                    "recipe_id": recipe['recipe_id'],
                    "dish_name": recipe['dish_name'] or "",
                    "main_ingredient": recipe['main_ingredient'] or "",
                    "power_profile": recipe.get('power_profile', '[]'),
                    "ingredient_sequence": recipe.get('ingredient_sequence', '[]'),
                    "cook_steps": json.dumps(cook_steps, ensure_ascii=False) if cook_steps else '[]',
                    "exec_count": recipe.get('exec_count', 1),
                    "status": recipe.get('exec_status', 'success'),
                    "exec_time": recipe.get('exec_time'),
                    "source_data": json.dumps(dict(recipe), ensure_ascii=False, default=str),
                }
                
                task = SyncTask(**task_data)
                db.add(task)
                all_tasks.append(task)
            
            db.commit()
            logger.info(f"从源数据库拉取 {len(all_tasks)} 条任务数据")
            return all_tasks
            
    finally:
        conn.close()


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
