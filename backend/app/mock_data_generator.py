"""
Mock 数据生成器 — 基于真实数据结构
生成 36 位工程师 + 近 30 天的录菜数据
"""
import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

# ============================================================
# 菜谱库（基于真实菜谱结构）
# ============================================================
RECIPE_LIBRARY = [
    {"recipe_id": 79079, "dish_name": "辣椒炒肉", "group_name": "辣椒炒肉", "version": 5, "type": 0, "customer": "鲜尚客·杭州西湖店", "device_id": "CK-3000 #A2187", "exec_range": (1, 5)},
    {"recipe_id": 79080, "dish_name": "辣椒炒肉", "group_name": "辣椒炒肉", "version": 5, "type": 2, "customer": "鲜尚客·杭州西湖店", "device_id": "CK-3000 #A2187", "exec_range": (1, 3)},
    {"recipe_id": 79081, "dish_name": "辣椒炒肉大份加豆豉版", "group_name": "辣椒炒肉", "version": 5, "type": 7, "customer": "鲜尚客·杭州西湖店", "device_id": "CK-3000 #A2187", "exec_range": (1, 6)},
    {"recipe_id": 69545, "dish_name": "青椒肉丝", "group_name": "青椒肉丝", "version": 3, "type": 0, "customer": "湘味阁·深圳南山店", "device_id": "CK-3000 #B3291", "exec_range": (1, 4)},
    {"recipe_id": 79411, "dish_name": "煎鸡蛋", "group_name": "煎鸡蛋", "version": 2, "type": 0, "customer": "湘味阁·深圳南山店", "device_id": "CK-3000 #B3291", "exec_range": (1, 2)},
    {"recipe_id": 79100, "dish_name": "麻婆豆腐", "group_name": "麻婆豆腐", "version": 4, "type": 0, "customer": "川香园·北京朝阳店", "device_id": "CK-3000 #C4102", "exec_range": (1, 3)},
    {"recipe_id": 79101, "dish_name": "红烧肉", "group_name": "红烧肉", "version": 6, "type": 0, "customer": "湘味阁·上海浦东店", "device_id": "CK-3000 #D5023", "exec_range": (1, 4)},
    {"recipe_id": 79102, "dish_name": "宫保鸡丁", "group_name": "宫保鸡丁", "version": 3, "type": 0, "customer": "川香园·广州天河店", "device_id": "CK-3000 #E6134", "exec_range": (1, 3)},
    {"recipe_id": 79103, "dish_name": "鱼香肉丝", "group_name": "鱼香肉丝", "version": 4, "type": 0, "customer": "湘味阁·成都锦江店", "device_id": "CK-3000 #F7245", "exec_range": (1, 5)},
    {"recipe_id": 79104, "dish_name": "水煮鱼", "group_name": "水煮鱼", "version": 5, "type": 0, "customer": "川香园·重庆渝北店", "device_id": "CK-3000 #G8356", "exec_range": (1, 4)},
    {"recipe_id": 79105, "dish_name": "回锅肉", "group_name": "回锅肉", "version": 3, "type": 0, "customer": "川香园·武汉江汉店", "device_id": "CK-3000 #H9467", "exec_range": (1, 3)},
    {"recipe_id": 79106, "dish_name": "糖醋排骨", "group_name": "糖醋排骨", "version": 4, "type": 0, "customer": "湘味阁·南京鼓楼店", "device_id": "CK-3000 #J1578", "exec_range": (1, 4)},
    {"recipe_id": 79107, "dish_name": "干锅花菜", "group_name": "干锅花菜", "version": 2, "type": 0, "customer": "湘味阁·杭州余杭店", "device_id": "CK-3000 #K2689", "exec_range": (1, 3)},
    {"recipe_id": 79108, "dish_name": "酸菜鱼", "group_name": "酸菜鱼", "version": 5, "type": 0, "customer": "川香园·西安雁塔店", "device_id": "CK-3000 #L3790", "exec_range": (1, 5)},
    {"recipe_id": 79109, "dish_name": "剁椒鱼头", "group_name": "剁椒鱼头", "version": 3, "type": 0, "customer": "湘味阁·长沙岳麓店", "device_id": "CK-3000 #M4801", "exec_range": (1, 3)},
    {"recipe_id": 79110, "dish_name": "小炒黄牛肉", "group_name": "小炒黄牛肉", "version": 4, "type": 0, "customer": "湘味阁·深圳福田店", "device_id": "CK-3000 #N5912", "exec_range": (1, 4)},
]

# 功率轨迹模板
POWER_TRACES = {
    "辣椒炒肉": [
        {"cmd": "开始烹饪", "time": 0, "power": 8000},
        {"cmd": "设置功率5000W", "time": 30, "power": 5000},
        {"cmd": "设置功率6000W", "time": 155, "power": 6000},
        {"cmd": "大火收汁", "time": 165, "power": 10000},
    ],
    "青椒肉丝": [
        {"cmd": "开始烹饪", "time": 0, "power": 7000},
        {"cmd": "转中火翻炒", "time": 45, "power": 5000},
        {"cmd": "出锅前大火", "time": 120, "power": 9000},
    ],
    "麻婆豆腐": [
        {"cmd": "开始烹饪", "time": 0, "power": 6000},
        {"cmd": "小火慢炖", "time": 60, "power": 3000},
        {"cmd": "大火勾芡", "time": 180, "power": 8000},
    ],
}

# 投料时序模板
INGREDIENTS = {
    "辣椒炒肉": [
        {"cmd": "手动投放猪油50克", "auto": False, "name": "猪油", "time": 41, "type": 1, "unit": "克", "dosage": "50"},
        {"cmd": "手动投放拍蒜20克", "auto": False, "name": "拍蒜", "time": 49, "type": 1, "unit": "克", "dosage": "20"},
        {"cmd": "手动投放螺丝椒200克", "auto": False, "name": "螺丝椒", "time": 61, "type": 1, "unit": "克", "dosage": "200"},
        {"cmd": "自动投放精盐2.3克", "auto": True, "name": "精盐", "time": 113, "type": 2, "unit": "克", "dosage": "2.3"},
        {"cmd": "手动投放瘦肉片150克", "auto": False, "name": "瘦肉片", "time": 128, "type": 1, "unit": "克", "dosage": "150"},
        {"cmd": "自动投放蚝油8克+生抽6克+老抽2克", "auto": True, "name": "蚝油+生抽+老抽", "time": 144, "type": 2, "unit": "克", "dosage": "8+6+2"},
    ],
    "青椒肉丝": [
        {"cmd": "自动投放花生油30克", "auto": True, "name": "花生油", "time": 20, "type": 2, "unit": "克", "dosage": "30"},
        {"cmd": "手动投放青椒150克", "auto": False, "name": "青椒", "time": 50, "type": 1, "unit": "克", "dosage": "150"},
        {"cmd": "手动投放肉丝120克", "auto": False, "name": "肉丝", "time": 80, "type": 1, "unit": "克", "dosage": "120"},
        {"cmd": "自动投放生抽5克", "auto": True, "name": "生抽", "time": 110, "type": 2, "unit": "克", "dosage": "5"},
    ],
    "麻婆豆腐": [
        {"cmd": "自动投放菜籽油40克", "auto": True, "name": "菜籽油", "time": 15, "type": 2, "unit": "克", "dosage": "40"},
        {"cmd": "手动投放肉末80克", "auto": False, "name": "肉末", "time": 40, "type": 1, "unit": "克", "dosage": "80"},
        {"cmd": "手动投放豆瓣酱30克", "auto": False, "name": "豆瓣酱", "time": 55, "type": 1, "unit": "克", "dosage": "30"},
        {"cmd": "手动投放嫩豆腐300克", "auto": False, "name": "嫩豆腐", "time": 90, "type": 1, "unit": "克", "dosage": "300"},
        {"cmd": "自动投放花椒粉2克", "auto": True, "name": "花椒粉", "time": 170, "type": 2, "unit": "克", "dosage": "2"},
    ],
}

# 异常场景模板
ABNORMAL_SCENARIOS = [
    {"type": "parameter", "desc": "精盐用量从2.3克调至3克，客户反馈偏咸"},
    {"type": "ingredient", "desc": "螺丝椒批次含水量高，影响出菜口感"},
    {"type": "equipment", "desc": "设备加热功率不稳定，第3次执行恢复正常"},
    {"type": "customer", "desc": "客户临时要求减辣，中途调整配方"},
    {"type": "process", "desc": "投料顺序调整后口感明显改善"},
]

MODIFICATIONS_POOL = [
    ["第2次将精盐从2.3克调至3克", "第3次恢复为2.3克"],
    ["第2次将蚝油从22克调至18克"],
    ["第3次更换螺丝椒批次（原批次含水量高）"],
    ["第2次延长翻炒时间至45秒"],
    ["第2次减少辣度，辣椒用量减少20%"],
    ["更换嫩豆腐供应商后口感变化"],
]


def generate_power_trace(dish_name: str) -> List[Dict]:
    """生成功率轨迹"""
    base = POWER_TRACES.get(dish_name, POWER_TRACES["辣椒炒肉"])
    # 添加一些随机变化
    trace = []
    for step in base:
        power_var = random.randint(-500, 500)
        trace.append({
            "cmd": step["cmd"],
            "time": step["time"] + random.randint(-5, 5),
            "power": max(1000, step["power"] + power_var),
        })
    return trace


def generate_ingredients(dish_name: str) -> List[Dict]:
    """生成投料时序"""
    base = INGREDIENTS.get(dish_name, INGREDIENTS["辣椒炒肉"])
    ingredients = []
    for ing in base:
        dosage_var = round(random.uniform(-0.2, 0.2) * float(ing["dosage"].split("+")[0]), 1)
        new_dosage = str(round(max(1, float(ing["dosage"].split("+")[0]) + dosage_var), 1))
        ingredients.append({
            **ing,
            "dosage": new_dosage,
            "time": ing["time"] + random.randint(-3, 3),
        })
    return ingredients


def generate_modifications(exec_count: int, has_abnormal: bool) -> List[str]:
    """生成调整记录"""
    if not has_abnormal:
        return []
    count = min(random.randint(1, 3), exec_count - 1)
    mods = random.sample(MODIFICATIONS_POOL, min(count, len(MODIFICATIONS_POOL)))
    return [m for group in mods for m in group]


def generate_tasks_for_engineer_date(engineer_id: int, task_date: date) -> List[Dict[str, Any]]:
    """生成某工程师某天的任务列表"""
    # 每天每个工程师 0-4 道菜（随机分布）
    if random.random() < 0.3:  # 30% 概率当天无任务
        return []

    num_tasks = random.randint(1, 4)
    recipes = random.sample(RECIPE_LIBRARY, min(num_tasks, len(RECIPE_LIBRARY)))

    tasks = []
    for recipe in recipes:
        exec_count = random.randint(*recipe["exec_range"])
        has_abnormal = random.random() < 0.25  # 25% 概率有异常
        status = "failed" if has_abnormal and random.random() < 0.4 else "passed"

        exec_hour = random.randint(9, 18)
        exec_minute = random.randint(0, 59)

        tasks.append({
            "task_date": task_date,
            "engineer_id": engineer_id,
            "recipe_id": recipe["recipe_id"],
            "dish_name": recipe["dish_name"],
            "group_name": recipe["group_name"],
            "recipe_version": recipe["version"],
            "recipe_type": recipe["type"],
            "pot_type": random.choice([1, 2]),
            "cooking_time": random.randint(60, 300),
            "max_power": random.choice([12000, 15000]),
            "customer_name": recipe["customer"],
            "device_id": recipe["device_id"],
            "power_trace": generate_power_trace(recipe["dish_name"]),
            "ingredients_timeline": generate_ingredients(recipe["dish_name"]),
            "ingredient_notes": [
                {"desc": "螺丝椒滚刀切块长5mm×宽2cm", "index": 1},
                {"desc": "蒜米用刀拍扁", "index": 2},
            ] if "辣椒" in recipe["dish_name"] else [],
            "exec_count": exec_count,
            "status": status,
            "has_abnormal": has_abnormal,
            "modifications": generate_modifications(exec_count, has_abnormal),
            "exec_time": f"{exec_hour:02d}:{exec_minute:02d}",
        })

    return tasks


def generate_30_day_data() -> Dict[str, Any]:
    """生成近 30 天的完整 mock 数据"""
    today = date.today()
    all_tasks = []
    sessions = []

    # 为 36 位工程师生成数据
    for eng_id in range(1, 37):
        # 不是每天都工作，随机分配工作天数
        work_days = random.sample(range(1, 31), k=random.randint(15, 28))

        for day_offset in work_days:
            task_date = today - timedelta(days=day_offset)

            tasks = generate_tasks_for_engineer_date(eng_id, task_date)
            if tasks:
                all_tasks.extend(tasks)

                # 决定是否创建会话（有任务就可能有会话）
                if random.random() < 0.7:  # 70% 概率创建会话
                    status = random.choice(["pending", "pushed", "submitted", "submitted", "submitted"])
                    submitted_at = None
                    duration = None
                    if status == "submitted":
                        duration = random.randint(120, 600)
                        submitted_at = datetime.combine(task_date, datetime.min.time()) + timedelta(
                            hours=random.randint(18, 21), minutes=random.randint(0, 59)
                        )

                    sessions.append({
                        "engineer_id": eng_id,
                        "session_date": task_date,
                        "status": status,
                        "question_count": random.randint(5, 9),
                        "submitted_at": submitted_at,
                        "duration_seconds": duration,
                        "summary_snapshot": [
                            {"dish_name": t["dish_name"], "recipe_id": t["recipe_id"], "exec_count": t["exec_count"], "status": t["status"]}
                            for t in tasks
                        ],
                        "root_event_type": random.choice([
                            None, "iterative_debugging", "customer_feedback", "key_adjustment",
                            "abnormal_failure", "reusable_method", "normal_day"
                        ]) if status == "submitted" else None,
                    })

    return {
        "tasks": all_tasks,
        "sessions": sessions,
        "stats": {
            "total_tasks": len(all_tasks),
            "total_sessions": len(sessions),
            "submitted_sessions": sum(1 for s in sessions if s["status"] == "submitted"),
            "engineers_with_data": len(set(t["engineer_id"] for t in all_tasks)),
        }
    }


if __name__ == "__main__":
    data = generate_30_day_data()
    print(f"Generated {data['stats']['total_tasks']} tasks for {data['stats']['engineers_with_data']} engineers")
    print(f"Generated {data['stats']['total_sessions']} sessions ({data['stats']['submitted_sessions']} submitted)")
