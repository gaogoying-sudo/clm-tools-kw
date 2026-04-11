"""
数据同步服务

第一版：生成基于真实表结构的模拟数据
后续版本：从公司 MySQL 后台拉取 main_recipe + recipe_detail + cook_steps
"""
from datetime import date, datetime
from typing import List
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
    """基于真实辣椒炒肉工艺包结构生成模拟数据"""

    # 检查是否已同步过
    existing = db.query(SyncTask).filter(SyncTask.task_date == target_date).count()
    if existing > 0:
        return db.query(SyncTask).filter(SyncTask.task_date == target_date).all()

    engineers = db.query(Engineer).filter(Engineer.is_active == True).all()
    if not engineers:
        return []

    eng1 = engineers[0]
    tasks_data = [
        # 任务1：小份辣椒炒肉 - 通过，做了3次
        {
            "engineer_id": eng1.id,
            "recipe_id": 138,
            "dish_name": "辣椒炒肉",
            "group_name": "辣椒炒肉",
            "recipe_version": 5,
            "recipe_type": 0,
            "pot_type": 1,
            "cooking_time": 175,
            "max_power": 12000,
            "picture": "https://chbtv2-1305920492.cos.ap-shanghai.myqcloud.com/sop/recipe/lajiaochaorou.jpg",
            "customer_name": "鲜尚客·杭州西湖店",
            "device_id": "CK-3000 #A2187",
            "power_trace": [
                {"time": 0, "power": 8000, "cmd": "开始烹饪"},
                {"time": 30, "power": 5000, "cmd": "设置功率5000W"},
                {"time": 155, "power": 6000, "cmd": "设置功率6000W"},
            ],
            "ingredients_timeline": [
                {"time": 41, "type": 1, "auto": False, "cmd": "手动投放猪油50克", "name": "猪油", "dosage": "50", "unit": "克"},
                {"time": 49, "type": 1, "auto": False, "cmd": "手动投放拍蒜20克", "name": "拍蒜", "dosage": "20", "unit": "克"},
                {"time": 61, "type": 1, "auto": False, "cmd": "手动投放螺丝椒200克", "name": "螺丝椒", "dosage": "200", "unit": "克"},
                {"time": 113, "type": 2, "auto": True, "cmd": "自动投放精盐2.3克", "name": "精盐", "dosage": "2.3", "unit": "克"},
                {"time": 128, "type": 1, "auto": False, "cmd": "手动投放瘦肉片150克", "name": "瘦肉片", "dosage": "150", "unit": "克"},
                {"time": 128, "type": 1, "auto": False, "cmd": "手动投放兔耳菌50克", "name": "兔耳菌", "dosage": "50", "unit": "克"},
                {"time": 144, "type": 2, "auto": True, "cmd": "自动投放蚝油8克+生抽6克+老抽2克", "name": "蚝油+生抽+老抽", "dosage": "8+6+2", "unit": "克"},
                {"time": 154, "type": 2, "auto": True, "cmd": "自动投放鸡精3克", "name": "鸡精", "dosage": "3", "unit": "克"},
                {"time": 157, "type": 1, "auto": False, "cmd": "手动投放味精1.8克", "name": "味精", "dosage": "1.8", "unit": "克"},
            ],
            "ingredient_notes": [
                {"index": 1, "desc": "螺丝椒滚刀切块长5mm×宽2cm"},
                {"index": 2, "desc": "蒜米用刀拍扁"},
                {"index": 3, "desc": "猪瘦肉切片长4cm×宽2cm×2mm厚"},
                {"index": 4, "desc": "猪肉片放蚝油6克、老抽4克腌制"},
                {"index": 5, "desc": "烧热油160度炸熟约8秒"},
                {"index": 6, "desc": "兔耳菌用开水泡30分钟一开二切开"},
            ],
            "exec_count": 3,
            "status": "passed",
            "has_abnormal": False,
            "modifications": ["第2次将精盐从2.3克调至3克", "第3次恢复为2.3克"],
            "exec_time": "14:35",
            "source_record_id": f"mock_138_{target_date}",
        },
        # 任务2：大份辣椒炒肉 - 通过
        {
            "engineer_id": eng1.id,
            "recipe_id": 141,
            "dish_name": "辣椒炒肉",
            "group_name": "辣椒炒肉",
            "recipe_version": 5,
            "recipe_type": 2,
            "pot_type": 1,
            "cooking_time": 215,
            "max_power": 12000,
            "picture": "https://chbtv2-1305920492.cos.ap-shanghai.myqcloud.com/sop/recipe/lajiaochaorou.jpg",
            "customer_name": "鲜尚客·杭州西湖店",
            "device_id": "CK-3000 #A2187",
            "power_trace": [
                {"time": 0, "power": 8000, "cmd": "开始烹饪"},
                {"time": 37, "power": 8000, "cmd": "转到炒菜位"},
                {"time": 190, "power": 6000, "cmd": "设置6000W收尾"},
            ],
            "ingredients_timeline": [
                {"time": 41, "type": 2, "auto": True, "cmd": "自动投放花生油120克", "name": "花生油", "dosage": "120", "unit": "克"},
                {"time": 55, "type": 1, "auto": False, "cmd": "手动投放蒜米50克", "name": "蒜米", "dosage": "50", "unit": "克"},
                {"time": 73, "type": 1, "auto": False, "cmd": "手动投放螺丝椒600克", "name": "螺丝椒", "dosage": "600", "unit": "克"},
                {"time": 90, "type": 2, "auto": True, "cmd": "自动投放精盐7克", "name": "精盐", "dosage": "7", "unit": "克"},
                {"time": 120, "type": 1, "auto": False, "cmd": "手动投放兔儿菌150克", "name": "兔儿菌", "dosage": "150", "unit": "克"},
                {"time": 143, "type": 1, "auto": False, "cmd": "手动投放瘦肉片500克", "name": "瘦肉片", "dosage": "500", "unit": "克"},
                {"time": 167, "type": 2, "auto": True, "cmd": "自动投放鸡精8克+白砂糖8克", "name": "鸡精+白砂糖", "dosage": "8+8", "unit": "克"},
                {"time": 180, "type": 2, "auto": True, "cmd": "自动投放生抽18克+蚝油26克", "name": "生抽+蚝油", "dosage": "18+26", "unit": "克"},
                {"time": 204, "type": 2, "auto": True, "cmd": "自动投放老抽8克", "name": "老抽", "dosage": "8", "unit": "克"},
            ],
            "ingredient_notes": [
                {"index": 1, "desc": "螺丝椒滚刀切块长5mm×宽2cm"},
                {"index": 2, "desc": "蒜米用刀拍扁"},
                {"index": 3, "desc": "猪瘦肉切片长4cm×宽2cm×2mm厚"},
            ],
            "exec_count": 1,
            "status": "passed",
            "has_abnormal": False,
            "modifications": [],
            "exec_time": "16:20",
            "source_record_id": f"mock_141_{target_date}",
        },
        # 任务3：大份加豆豉版 - 失败，5次
        {
            "engineer_id": eng1.id,
            "recipe_id": 144,
            "dish_name": "辣椒炒肉大份加豆豉版",
            "group_name": "辣椒炒肉",
            "recipe_version": 5,
            "recipe_type": 7,
            "pot_type": 1,
            "cooking_time": 215,
            "max_power": 12000,
            "picture": "https://chbtv2-1305920492.cos.ap-shanghai.myqcloud.com/sop/recipe/lajiaochaorou.jpg",
            "customer_name": "鲜尚客·杭州西湖店",
            "device_id": "CK-3000 #A2187",
            "power_trace": [
                {"time": 0, "power": 8000, "cmd": "开始烹饪"},
                {"time": 37, "power": 8000, "cmd": "转到炒菜位"},
                {"time": 190, "power": 6000, "cmd": "设置6000W收尾"},
            ],
            "ingredients_timeline": [
                {"time": 41, "type": 2, "auto": True, "cmd": "自动投放花生油120克", "name": "花生油", "dosage": "120", "unit": "克"},
                {"time": 55, "type": 1, "auto": False, "cmd": "手动投放蒜米50克", "name": "蒜米", "dosage": "50", "unit": "克"},
                {"time": 69, "type": 1, "auto": False, "cmd": "手动投放豆豉20克", "name": "豆豉", "dosage": "20", "unit": "克"},
                {"time": 73, "type": 1, "auto": False, "cmd": "手动投放螺丝椒600克", "name": "螺丝椒", "dosage": "600", "unit": "克"},
                {"time": 90, "type": 2, "auto": True, "cmd": "自动投放精盐7克", "name": "精盐", "dosage": "7", "unit": "克"},
                {"time": 120, "type": 1, "auto": False, "cmd": "手动投放兔儿菌150克", "name": "兔儿菌", "dosage": "150", "unit": "克"},
                {"time": 143, "type": 1, "auto": False, "cmd": "手动投放瘦肉片500克", "name": "瘦肉片", "dosage": "500", "unit": "克"},
                {"time": 167, "type": 2, "auto": True, "cmd": "自动投放鸡精3克", "name": "鸡精", "dosage": "3", "unit": "克"},
                {"time": 180, "type": 2, "auto": True, "cmd": "自动投放生抽16克+蚝油22克", "name": "生抽+蚝油", "dosage": "16+22", "unit": "克"},
                {"time": 204, "type": 2, "auto": True, "cmd": "自动投放老抽8克", "name": "老抽", "dosage": "8", "unit": "克"},
            ],
            "ingredient_notes": [],
            "exec_count": 5,
            "status": "failed",
            "has_abnormal": True,
            "modifications": [
                "第2次将精盐从7克调至5克",
                "第3次将蚝油从22克调至18克",
                "第4次更换螺丝椒批次（原批次含水量高）",
                "第5次恢复精盐7克，仍未通过",
            ],
            "exec_time": "17:50",
            "source_record_id": f"mock_144_{target_date}",
        },
    ]

    created = []
    for td in tasks_data:
        task = SyncTask(task_date=target_date, **td)
        db.add(task)
        created.append(task)

    db.commit()
    for t in created:
        db.refresh(t)
    return created
