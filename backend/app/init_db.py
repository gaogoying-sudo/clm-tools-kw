"""
数据库初始化：建表 + 迁移 + 写入问题模板（现场语言）+ 模拟工程师
"""
from .database import engine, SessionLocal, Base
from .models import Engineer, Question


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")

    try:
        from .migrate_v2 import migrate_v2
        print("运行 V2 迁移...")
        migrate_v2()
        print("✅ V2 迁移完成")
    except Exception as e:
        print(f"⚠ V2 迁移跳过或失败: {e}")

    db = SessionLocal()
    try:
        _upsert_questions(db)
        _seed_engineers(db)
        db.commit()
        print("✅ 初始数据写入完成")
    finally:
        db.close()


def _upsert_questions(db):
    """插入或更新问题模板（现场语言、节点式）"""
    # 旧问题 key 置为禁用，保留兼容
    for old_key in ("q1", "q2", "q3", "q4", "q5", "q_seasoning", "q_version"):
        q = db.query(Question).filter(Question.question_key == old_key).first()
        if q:
            q.is_active = False

    questions = [
        # === 入口题 ===
        {
            "question_key": "q_entry",
            "question_type": "single",
            "title": "今天最值得说的一件事，更接近下面哪种情况？",
            "subtitle": "",
            "options": [
                "有道菜今天来回调了好几次",
                "客户今天提了明显意见",
                "我改了一个地方，效果很明显",
                "今天出了意料外的问题",
                "有个做法我觉得以后可以固定下来",
                "今天整体比较顺，没什么特别的",
            ],
            "placeholder": None,
            "node_type": "entry",
            "source_type": "fixed",
            "related_event_type": None,
            "is_triggered": False,
            "trigger_rule": "",
            "display_order": 1,
            "sort_order": 1,
        },
        # === 分支题：通用 ===
        {
            "question_key": "q_factor",
            "question_type": "multi",
            "title": "今天最关键的影响因素是什么？",
            "subtitle": "可多选",
            "options": [
                "食材状态（含水量、新鲜度、批次差异）",
                "调味料/液料比例",
                "火候/时间参数",
                "步骤顺序",
                "客户说不清要啥",
                "设备状况",
                "现场操作因素",
                "其他",
            ],
            "placeholder": None,
            "node_type": "branch",
            "source_type": "branch",
            "related_event_type": None,
            "is_triggered": False,
            "display_order": 2,
            "sort_order": 2,
        },
        {
            "question_key": "q_anchor",
            "question_type": "anchor",
            "title": "今天最想说的是哪道菜？",
            "subtitle": "选一道后可以补充原因",
            "options": None,
            "placeholder": "为什么选这道菜？",
            "node_type": "branch",
            "source_type": "branch",
            "related_event_type": None,
            "is_triggered": False,
            "display_order": 3,
            "sort_order": 3,
        },
        {
            "question_key": "q_experience",
            "question_type": "open",
            "title": "用一句话说清楚，你会怎么说？",
            "subtitle": "",
            "options": None,
            "placeholder": "例：这道菜最难的不是火力而是汁感\n例：高含水螺丝椒必须提前沥干\n例：豆豉版比标准版多的不是豆豉味而是底味层次",
            "node_type": "branch",
            "source_type": "branch",
            "related_event_type": None,
            "is_triggered": False,
            "display_order": 4,
            "sort_order": 4,
        },
        # === 分支题：客户反馈时追加 ===
        {
            "question_key": "q_customer",
            "question_type": "open",
            "title": "客户具体怎么说？或者你当时怎么判断的？",
            "subtitle": "",
            "options": None,
            "placeholder": "例：客户说太咸，但减盐后蚝油味太突出...",
            "node_type": "branch",
            "source_type": "branch",
            "related_event_type": "customer_feedback",
            "is_triggered": False,
            "display_order": 5,
            "sort_order": 5,
        },
        # === 触发题：failure/retry ===
        {
            "question_key": "q_fail",
            "question_type": "single",
            "title": "这次失败更像是哪类问题？",
            "subtitle": "",
            "options": ["参数问题", "食材问题", "设备问题", "客户预期问题", "工艺路径问题", "综合因素"],
            "placeholder": None,
            "node_type": "trigger",
            "source_type": "trigger",
            "related_event_type": None,
            "is_triggered": True,
            "trigger_rule": "failure_retry",
            "trigger_priority": 1,
            "display_order": 10,
            "sort_order": 10,
        },
        {
            "question_key": "q_retry",
            "question_type": "open",
            "title": "反复调最核心的原因是什么？",
            "subtitle": "",
            "options": None,
            "placeholder": "例：前几次以为是参数问题在调盐，后来换了螺丝椒批次才发现是食材含水量",
            "node_type": "trigger",
            "source_type": "trigger",
            "related_event_type": None,
            "is_triggered": True,
            "trigger_rule": "failure_retry",
            "trigger_priority": 1,
            "display_order": 11,
            "sort_order": 11,
        },
    ]

    for qd in questions:
        existing = db.query(Question).filter(Question.question_key == qd["question_key"]).first()
        if existing:
            for k, v in qd.items():
                setattr(existing, k, v)
            print(f"  更新问题: {qd['question_key']}")
        else:
            q = Question(**qd)
            db.add(q)
            print(f"  新增问题: {qd['question_key']}")

    print(f"问题模板共 {len(questions)} 个")


def _seed_engineers(db):
    """写入模拟工程师"""
    if db.query(Engineer).count() > 0:
        print("工程师数据已存在，跳过")
        return

    engineers = [
        Engineer(name="张明", feishu_user_id="zhangming", role="高级口味工程师", region="华东"),
        Engineer(name="李薇", feishu_user_id="liwei", role="口味工程师", region="华南"),
        Engineer(name="王建国", feishu_user_id="wangjianguo", role="现场交付工程师", region="华北"),
    ]
    for e in engineers:
        db.add(e)
    print(f"写入 {len(engineers)} 个工程师")


if __name__ == "__main__":
    init_db()
