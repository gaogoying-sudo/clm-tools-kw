
import sys
sys.path.insert(0, '/app')
from app.database import SessionLocal
from app.models import SyncTask
from sqlalchemy import text

db = SessionLocal()

# 1. Get all tasks
tasks = db.query(SyncTask).all()
print(f"Checking {len(tasks)} tasks...")

# 2. Identify junk
junk_ids = []
junk_keywords = ['已定', '定版', '定板', '未录', '无新', '暂无', '正常', '问题', '稳定', '出餐', '今日', '所有菜品', '协助', '支持', '导入', '培训', '测试', '结束', 'POC']

for t in tasks:
    name = t.dish_name.strip()
    # Check exact matches
    if name in ['已定', '菜品定版', '未录菜', '烹饪出品', '正常', '无新品录入', '新店开业', '无新菜录入', '暂无', '铁锅导入', '所有菜品已定板', '菜品均', '菜品', '定版', '菜品都', '所以菜品已定板', '无问题', '今日无新增菜品', '无录菜', '今日无新增sku', '今天早餐出餐', '暂无新品录入', '稳定', '好', '菜品出品正常', '未定版', '今日未定版', '15', '8', '1', '2', '3', '4', '5', '两份', '3份已定', '3份', '12*3', '2份', '-', '无', '协助', '支持', '今日到达北京', '今日在望京协助现场工作。', '目前已有20款菜品定版（语言大学店使用铁锅菜谱）']:
        junk_ids.append(t.id)
        continue
    
    # Check keyword matches
    if any(k in name for k in junk_keywords):
        junk_ids.append(t.id)
        continue
        
    # Check if it's just a number
    try:
        float(name)
        junk_ids.append(t.id)
    except:
        pass

print(f"Identified {len(junk_ids)} junk tasks.")

# 3. Delete in bulk
if junk_ids:
    # SQLAlchemy delete by list of IDs
    db.query(SyncTask).filter(SyncTask.id.in_(junk_ids)).delete(synchronize_session=False)
    db.commit()
    print(f"Deleted {len(junk_ids)} tasks.")
else:
    print("No junk found.")
" 2>&1
