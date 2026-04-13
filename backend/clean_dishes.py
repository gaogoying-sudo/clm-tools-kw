
import sys
sys.path.insert(0, '/app')
from app.database import SessionLocal
from app.models import SyncTask

db = SessionLocal()

# List of junk strings to remove
junk = {
    '已定', '菜品定版', '未录菜', '烹饪出品', '正常', '无新品录入', '新店开业', 
    '无新菜录入', '暂无', '铁锅导入', '所有菜品已定板', '菜品均', '菜品', 
    '定版', '菜品都', '所以菜品已定板', '无问题', '今日无新增菜品', '无录菜',
    '今日无新增sku', '今天早餐出餐', '暂无新品录入', '稳定', '好', '菜品出品正常',
    '未定版', '今日未定版', '15', '8', '1', '2', '3', '4', '5',
    '两份', '3份已定', '3份', '12*3', '2份', '-', '无', '协助', '支持',
    '今日到达北京', '今日在望京协助现场工作。', '目前已有20款菜品定版（语言大学店使用铁锅菜谱）',
    '今日在望京协助现场工作', 'POC'
}

# Also remove anything containing "定版" or "未录"
count = 0
tasks_to_delete = []
for task in db.query(SyncTask).all():
    name = task.dish_name.strip()
    if name in junk:
        tasks_to_delete.append(task)
        continue
    
    # Keyword check
    keywords = ['已定', '定版', '定板', '未录', '无新', '暂无', '正常', '问题', '稳定', '出餐', '今日', '所有菜品', '协助', '支持', '导入', '培训', '测试', '结束']
    if any(k in name for k in keywords):
        tasks_to_delete.append(task)
        
print(f"Found {len(tasks_to_delete)} junk tasks.")

for task in tasks_to_delete:
    db.delete(task)

db.commit()
print("Cleanup done.")
