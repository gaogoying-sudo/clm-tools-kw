"""
问题流引擎

节点式问题流：入口题 → 分支题 → 触发题
规则负责：数据检索、问题流主框架、触发判断
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .models import Question, SyncTask


# 入口题选项 → root_event_type 映射
ENTRY_OPTION_TO_EVENT = {
    "有道菜今天来回调了好几次": "iterative_debugging",
    "客户今天提了明显意见": "customer_feedback",
    "我改了一个地方，效果很明显": "key_adjustment",
    "今天出了意料外的问题": "abnormal_failure",
    "有个做法我觉得以后可以固定下来": "reusable_method",
    "今天整体比较顺，没什么特别的": "normal_day",
}

# root_event_type → 分类池映射
ROOT_EVENT_TO_POOL = {
    "iterative_debugging": "tuning_record",
    "customer_feedback": "customer_pref",
    "key_adjustment": "experience",
    "abnormal_failure": "failure_case",
    "reusable_method": "experience",
    "normal_day": "daily_record",
}


# ============================================================
# 信号识别
# ============================================================

def detect_signals(tasks: List[SyncTask]) -> Dict[str, Any]:
    """从当天任务数据中识别信号"""
    signals = {
        "has_tasks": len(tasks) > 0,
        "task_count": len(tasks),
        "total_exec": sum(t.exec_count for t in tasks),
        "has_failed": any(t.status == "failed" for t in tasks),
        "failed_tasks": [t for t in tasks if t.status == "failed"],
        "has_high_exec": any(t.exec_count >= 4 for t in tasks),
        "high_exec_tasks": [t for t in tasks if t.exec_count >= 4],
        "has_abnormal": any(t.has_abnormal for t in tasks),
        "has_modifications": any(len(t.modifications or []) >= 2 for t in tasks),
        "same_group_multi_version": False,
        "group_counts": {},
        "has_seasoning_change": False,
        "seasoning_mods": [],
    }

    groups = {}
    for t in tasks:
        g = t.group_name or t.dish_name
        groups.setdefault(g, []).append(t)
    signals["group_counts"] = {k: len(v) for k, v in groups.items()}
    signals["same_group_multi_version"] = any(len(v) > 1 for v in groups.values())

    seasoning_keywords = ["盐", "蚝油", "生抽", "老抽", "酱油", "糖", "醋", "料酒", "鸡精", "味精"]
    for t in tasks:
        for m in (t.modifications or []):
            if any(k in m for k in seasoning_keywords):
                signals["seasoning_mods"].append({"task": t, "mod": m})
    signals["has_seasoning_change"] = len(signals["seasoning_mods"]) > 0

    return signals


# ============================================================
# 节点式问题流
# ============================================================

def select_flow_questions(db: Session, signals: Dict[str, Any], root_event_type: Optional[str] = None) -> List[Dict]:
    """
    按节点式问题流选取题目，返回带元数据的列表。
    root_event_type: 入口题答案，用于过滤分支题；若为 None 则返回全部分支（前端按答案过滤）。
    """
    if not signals["has_tasks"]:
        return []

    out = []

    # 1. 入口题
    q_entry = db.query(Question).filter(
        Question.is_active == True,
        Question.node_type == "entry",
    ).order_by(Question.display_order, Question.sort_order).first()
    if q_entry:
        out.append(_to_flow_node(q_entry, None))

    # 2. 分支题：related_event_type 为 null 表示通用；否则需匹配 root_event_type
    branches = db.query(Question).filter(
        Question.is_active == True,
        Question.node_type == "branch",
    ).order_by(Question.display_order, Question.sort_order).all()

    for q in branches:
        if q.related_event_type is None or q.related_event_type == "":
            out.append(_to_flow_node(q, None))
        elif root_event_type and q.related_event_type == root_event_type:
            out.append(_to_flow_node(q, None))
        elif root_event_type is None:
            out.append(_to_flow_node(q, None))

    # 3. 触发题：failure/retry + customer_feedback
    triggers = []
    if signals["has_failed"]:
        q = db.query(Question).filter(Question.question_key == "q_fail").first()
        if q:
            triggers.append((q, 1, _build_trigger_context(signals, "q_fail")))
    if signals["has_high_exec"]:
        q = db.query(Question).filter(Question.question_key == "q_retry").first()
        if q:
            triggers.append((q, 1, _build_trigger_context(signals, "q_retry")))
    if root_event_type == "customer_feedback":
        q = db.query(Question).filter(Question.question_key == "q_customer").first()
        if q:
            triggers.append((q, 2, "客户今天提了明显意见，想听你说说具体情况"))

    triggers.sort(key=lambda x: x[1])
    for q, _, ctx in triggers[:3]:
        out.append(_to_flow_node(q, ctx))

    return out


def _to_flow_node(q: Question, trigger_context: Optional[str]) -> Dict:
    return {
        "id": q.id,
        "question_key": q.question_key,
        "question_type": q.question_type,
        "title": q.title,
        "subtitle": q.subtitle or "",
        "options": q.options,
        "placeholder": q.placeholder,
        "node_type": q.node_type or ("trigger" if q.is_triggered else "branch"),
        "source_type": q.source_type or ("trigger" if q.is_triggered else "branch"),
        "related_event_type": q.related_event_type,
        "trigger_context": trigger_context,
        "display_order": q.display_order or q.sort_order,
        "is_triggered": q.is_triggered,
    }


def _build_trigger_context(signals: Dict[str, Any], question_key: str) -> str:
    if question_key == "q_fail":
        t = signals["failed_tasks"][0] if signals["failed_tasks"] else None
        return f"「{t.dish_name}」(recipe#{t.recipe_id}) 执行失败" if t else "检测到有失败任务"
    if question_key == "q_retry":
        t = signals["high_exec_tasks"][0] if signals["high_exec_tasks"] else None
        return f"「{t.dish_name}」执行了{t.exec_count}次" if t else "检测到反复执行"
    return ""


def build_trigger_context(signals: Dict[str, Any], question_key: str) -> str:
    """兼容旧接口"""
    return _build_trigger_context(signals, question_key)


# ============================================================
# 兼容旧接口：select_questions 返回 Question 列表
# ============================================================

def select_questions(db: Session, signals: Dict[str, Any], root_event_type: Optional[str] = None) -> List[Question]:
    """
    兼容旧接口。根据 root_event_type 过滤分支题，返回 Question 列表。
    """
    nodes = select_flow_questions(db, signals, root_event_type)
    keys = [n["question_key"] for n in nodes]
    if not keys:
        return []
    questions = db.query(Question).filter(Question.question_key.in_(keys)).all()
    order_map = {k: i for i, k in enumerate(keys)}
    return sorted(questions, key=lambda q: order_map.get(q.question_key, 999))


# ============================================================
# 发送门槛
# ============================================================

def should_send(signals: Dict[str, Any]) -> bool:
    if not signals["has_tasks"]:
        return False
    return True


def build_trigger_summary(signals: Dict[str, Any]) -> str:
    """生成触发信号摘要，写入 session"""
    parts = []
    if signals.get("has_failed") and signals.get("failed_tasks"):
        t = signals["failed_tasks"][0]
        parts.append(f"失败:{t.dish_name}")
    if signals.get("has_high_exec") and signals.get("high_exec_tasks"):
        t = signals["high_exec_tasks"][0]
        parts.append(f"重试:{t.dish_name}×{t.exec_count}")
    return "; ".join(parts) if parts else ""
