#!/usr/bin/env python3
"""
添加 cook_steps 字段到 sync_tasks 表
使用方法：python add_cook_steps_column.py
"""
import sys
sys.path.insert(0, 'app')

from database import SessionLocal, engine
from sqlalchemy import text

def add_cook_steps_column():
    """添加 cook_steps 列到 sync_tasks 表"""
    db = SessionLocal()
    try:
        # 检查列是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'clm_review' 
            AND TABLE_NAME = 'sync_tasks' 
            AND COLUMN_NAME = 'cook_steps'
        """))
        exists = result.scalar()
        
        if exists:
            print("✅ cook_steps 列已存在")
            return
        
        # 添加列
        db.execute(text("""
            ALTER TABLE sync_tasks 
            ADD COLUMN cook_steps JSON DEFAULT NULL COMMENT '烹饪步骤 [{step,time,temp,cmd,desc}]'
        """))
        db.commit()
        print("✅ 成功添加 cook_steps 列到 sync_tasks 表")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 添加列失败：{e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_cook_steps_column()
