"""
一次性脚本：填充完整的 36 位工程师
执行: python -m app.seed_full_engineers
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import Engineer

engineers_data = [
    {"name": "付强", "feishu_id": "6bc278bd", "role": "高级口味工程师", "region": "华东"},
    {"name": "唐浩宇", "feishu_id": "19ff8ef6", "role": "口味工程师", "region": "华南"},
    {"name": "胡光中", "feishu_id": "efa2gec4", "role": "口味工程师", "region": "华中"},
    {"name": "江飞", "feishu_id": "", "role": "口味工程师", "region": "华北"},
    {"name": "刘兰强", "feishu_id": "", "role": "高级口味工程师", "region": "华东"},
    {"name": "张海", "feishu_id": "", "role": "口味工程师", "region": "华南"},
    {"name": "冯明", "feishu_id": "", "role": "现场交付工程师", "region": "华东"},
    {"name": "周洪亮", "feishu_id": "", "role": "口味工程师", "region": "华中"},
    {"name": "高豪", "feishu_id": "", "role": "口味工程师", "region": "华北"},
    {"name": "罗刚", "feishu_id": "", "role": "高级口味工程师", "region": "华南"},
    {"name": "雷祖壮", "feishu_id": "", "role": "口味工程师", "region": "华东"},
    {"name": "尹龙强", "feishu_id": "", "role": "现场交付工程师", "region": "华中"},
    {"name": "杨梓锋", "feishu_id": "", "role": "口味工程师", "region": "华南"},
    {"name": "张连顺", "feishu_id": "", "role": "口味工程师", "region": "华北"},
    {"name": "许宝华", "feishu_id": "", "role": "高级口味工程师", "region": "华东"},
    {"name": "周思来", "feishu_id": "", "role": "首席口味工程师", "region": "华中"},
    {"name": "马志明", "feishu_id": "", "role": "口味工程师", "region": "华南"},
    {"name": "陈龙", "feishu_id": "", "role": "口味工程师", "region": "华东"},
    {"name": "卢明辉", "feishu_id": "", "role": "现场交付工程师", "region": "华中"},
    {"name": "王野", "feishu_id": "", "role": "口味工程师", "region": "华北"},
    {"name": "周华玉", "feishu_id": "", "role": "口味工程师", "region": "华南"},
    {"name": "周潮凌", "feishu_id": "", "role": "口味工程师", "region": "华东"},
    {"name": "沈伯腾", "feishu_id": "", "role": "高级口味工程师", "region": "华中"},
    {"name": "陈尚贤", "feishu_id": "", "role": "口味工程师", "region": "华南"},
    {"name": "李彦彪", "feishu_id": "", "role": "口味工程师", "region": "华东"},
    {"name": "陈镭福", "feishu_id": "", "role": "现场交付工程师", "region": "华南"},
    {"name": "周辰永", "feishu_id": "", "role": "高级口味工程师", "region": "华东"},
    {"name": "Kevin Hartley", "feishu_id": "", "role": "口味工程师", "region": "海外"},
    {"name": "Fami Taufeq Fakarudin", "feishu_id": "", "role": "现场交付工程师", "region": "海外"},
    {"name": "戴子扬", "feishu_id": "", "role": "口味工程师", "region": "华东"},
    {"name": "黄俊龙", "feishu_id": "", "role": "口味工程师", "region": "华南"},
    {"name": "周杰彪", "feishu_id": "", "role": "高级口味工程师", "region": "华中"},
    {"name": "李传灵", "feishu_id": "", "role": "口味工程师", "region": "华南"},
    {"name": "宗振兴", "feishu_id": "", "role": "现场交付工程师", "region": "华北"},
    {"name": "利伟锋", "feishu_id": "", "role": "口味工程师", "region": "华东"},
    {"name": "唐清林", "feishu_id": "", "role": "口味工程师", "region": "华南"},
]

def seed():
    db = SessionLocal()
    try:
        existing = {e.name for e in db.query(Engineer).all()}
        added = 0
        for e in engineers_data:
            if e["name"] not in existing:
                eng = Engineer(
                    name=e["name"],
                    feishu_user_id=e["feishu_id"] if e["feishu_id"] else None,
                    role=e["role"],
                    region=e["region"],
                )
                db.add(eng)
                added += 1
        db.commit()
        print(f"Added {added} engineers (total now: {db.query(Engineer).count()})")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
