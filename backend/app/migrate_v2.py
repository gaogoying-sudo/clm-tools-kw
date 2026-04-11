"""
V2 迁移：为 Question、DailySession、Answer 添加节点式问题流与三层存储字段
"""
from sqlalchemy import text
from .database import engine


def migrate_v2():
    """添加新列到已有表，若列已存在则跳过"""
    for stmt, name in _get_alter_statements():
        try:
            with engine.connect() as conn:
                conn.execute(text(stmt))
                conn.commit()
                print(f"  ✓ {name}")
        except Exception as e:
            err = str(e).lower()
            if "duplicate column" in err or "1060" in err:
                print(f"  - {name} 已存在，跳过")
            else:
                raise


def _get_alter_statements():
    return [
        ("ALTER TABLE daily_sessions ADD COLUMN summary_snapshot JSON", "daily_sessions.summary_snapshot"),
        ("ALTER TABLE daily_sessions ADD COLUMN root_event_type VARCHAR(50)", "daily_sessions.root_event_type"),
        ("ALTER TABLE daily_sessions ADD COLUMN generated_flow_version VARCHAR(20) DEFAULT 'v1'", "daily_sessions.generated_flow_version"),
        ("ALTER TABLE daily_sessions ADD COLUMN trigger_summary TEXT", "daily_sessions.trigger_summary"),
        ("ALTER TABLE daily_sessions ADD COLUMN flow_status VARCHAR(20) DEFAULT 'active'", "daily_sessions.flow_status"),
        ("ALTER TABLE questions ADD COLUMN node_type VARCHAR(20) DEFAULT 'branch'", "questions.node_type"),
        ("ALTER TABLE questions ADD COLUMN source_type VARCHAR(20) DEFAULT 'fixed'", "questions.source_type"),
        ("ALTER TABLE questions ADD COLUMN related_event_type VARCHAR(50)", "questions.related_event_type"),
        ("ALTER TABLE questions ADD COLUMN visible_if JSON", "questions.visible_if"),
        ("ALTER TABLE questions ADD COLUMN next_rule VARCHAR(200)", "questions.next_rule"),
        ("ALTER TABLE questions ADD COLUMN context_bindings JSON", "questions.context_bindings"),
        ("ALTER TABLE questions ADD COLUMN display_order INT DEFAULT 0", "questions.display_order"),
        ("ALTER TABLE answers ADD COLUMN raw_input JSON", "answers.raw_input"),
        ("ALTER TABLE answers ADD COLUMN transcribed_text TEXT", "answers.transcribed_text"),
        ("ALTER TABLE answers ADD COLUMN structured_result JSON", "answers.structured_result"),
    ]
