
import zipfile
import xml.etree.ElementTree as ET
import re
import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models import Engineer, SyncTask, DailySession, SessionTask, Answer, Question
from sqlalchemy import text
from datetime import datetime, timedelta

INVALID_NAMES = {'排休', '项目出差', '巡店', '浣熊食堂', '会议', '培训'}

def parse_sheet(z, sheet_path):
    with z.open(sheet_path) as f:
        tree = ET.parse(f)
        root = tree.getroot()
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        sheet_data = root.find('ns:sheetData', ns)
        if sheet_data is None: return []
        rows_data = []
        for row in sheet_data.findall('ns:row', ns):
            row_data = []
            cells = row.findall('ns:c', ns)
            cells.sort(key=lambda c: c.get('r', ''))
            for cell in cells:
                val = ''
                inline_str = cell.find('ns:is/ns:t', ns)
                if inline_str is not None: val = inline_str.text
                elif cell.get('t') == 's': val = '[Shared]'
                else:
                    v = cell.find('ns:v', ns)
                    if v is not None: val = v.text
                row_data.append(val)
            rows_data.append(row_data)
        return rows_data

def clean_name(name):
    if not name or name == '[Shared]': return None
    if name in INVALID_NAMES: return None
    parts = re.split(r'[-\s]', name)
    first_part = parts[0].strip()
    if first_part in INVALID_NAMES: return None
    return first_part

def clean_dishes(dish_str):
    if not dish_str or dish_str == '无': return []
    # Split by comma, Chinese comma, or Newline
    dishes = []
    for d in re.split(r'[,，\n]', dish_str):
        d = d.strip()
        if d and len(d) < 50: # Filter out huge blocks of text that failed to split
            # Remove numbering "1.", "2."
            d = re.sub(r'^\d+\.\s*', '', d)
            # Remove status "已定版", "已上线"
            d = re.sub(r'已定版|已上线|已认证', '', d)
            d = d.strip()
            if d: dishes.append(d)
    return dishes

def main():
    print("Starting import V3 (Fixing Dish Parsing)...")
    db = SessionLocal()
    
    # 1. Map valid engineers
    all_engs = db.query(Engineer).all()
    valid_engs = []
    for e in all_engs:
        clean = clean_name(e.name)
        if clean: valid_engs.append(e.name)
        else: db.delete(e)
    db.commit()
    
    eng_map = {e.name: e.id for e in db.query(Engineer).all()}
    
    # 2. Parse Tasks
    try:
        with zipfile.ZipFile('/app/big_excel.xlsx') as z:
            rows = parse_sheet(z, 'xl/worksheets/sheet3.xml')
            
            tasks_created = 0
            
            for r in rows[1:]:
                eng_name = r[3].strip() if len(r) > 3 else None
                clean_eng = clean_name(eng_name)
                
                if not clean_eng or clean_eng not in eng_map: continue
                eng_id = eng_map[clean_eng]
                
                # Date
                date_str = r[13] if len(r) > 13 else None
                task_date = None
                if date_str:
                    try:
                        if '.' in date_str:
                            days = int(float(date_str))
                            base = datetime(1899, 12, 30)
                            task_date = (base + timedelta(days=days)).date()
                    except: pass
                
                if not task_date:
                    title = r[0] if len(r) > 0 else ""
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', title)
                    if match:
                        try: task_date = datetime.strptime(match.group(1), '%Y-%m-%d').date()
                        except: pass
                            
                if not task_date: continue 

                # Dishes
                dish_str = r[8] if len(r) > 8 else ""
                issues = r[9] if len(r) > 9 else ""
                
                dishes = clean_dishes(dish_str)
                
                # Create SyncTasks
                for dish in dishes:
                    task = SyncTask(
                        task_date=task_date,
                        engineer_id=eng_id,
                        dish_name=dish,
                        group_name=dish,
                        recipe_version=1,
                        recipe_type=0,
                        pot_type=1,
                        cooking_time=120,
                        max_power=12000,
                        customer_name="Excel导入",
                        device_id="Excel导入",
                        power_trace=[],
                        ingredients_timeline=[],
                        ingredient_notes=[],
                        exec_count=1,
                        status="passed",
                        has_abnormal=bool(issues),
                        modifications=[issues] if issues else [],
                        exec_time="12:00",
                        source_record_id="excel_import"
                    )
                    db.add(task)
                    tasks_created += 1
                
            db.commit()
            print(f"Imported {tasks_created} tasks from Excel.")
            
            # 3. Generate Sessions
            tasks = db.query(SyncTask).filter(SyncTask.source_record_id == 'excel_import').all()
            session_keys = set()
            sessions_created = 0
            for t in tasks:
                key = (t.engineer_id, t.task_date)
                if key not in session_keys:
                    session_keys.add(key)
                    session = DailySession(
                        engineer_id=t.engineer_id,
                        session_date=t.task_date,
                        status="submitted",
                        question_count=7,
                        submitted_at=datetime.combine(t.task_date, datetime.min.time()) + timedelta(hours=20),
                        duration_seconds=300,
                        summary_snapshot=[{"dish": t.dish_name}],
                        root_event_type="normal_day",
                    )
                    db.add(session)
                    db.flush()
                    
                    eng_date_tasks = [tk for tk in tasks if tk.engineer_id == t.engineer_id and tk.task_date == t.task_date]
                    for tk in eng_date_tasks:
                        st = SessionTask(session_id=session.id, sync_task_id=tk.id)
                        db.add(st)
                        
                    # Mock answer
                    q = db.query(Question).first()
                    if q:
                        a = Answer(session_id=session.id, question_id=q.id, answer_text="Excel导入模拟回答", raw_input={"text": "正常"}, transcribed_text="正常", structured_result={"sentiment": "positive"})
                        db.add(a)
                    sessions_created += 1
            
            db.commit()
            print(f"Created {sessions_created} sessions.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    main()
