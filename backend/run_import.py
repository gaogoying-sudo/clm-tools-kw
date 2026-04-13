
import zipfile
import xml.etree.ElementTree as ET
import sys
sys.path.insert(0, '/app')
from app.database import SessionLocal
from app.models import Engineer
from sqlalchemy import text

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

print("Connecting to DB...")
db = SessionLocal()
print("Clearing old data...")
for t in ['session_tasks', 'answers', 'experience_candidates', 'daily_sessions', 'sync_tasks', 'engineers']:
    db.execute(text(f'DELETE FROM {t}'))
db.commit()
print('Cleared.')

try:
    with zipfile.ZipFile('/app/big_excel.xlsx') as z:
        rows2 = parse_sheet(z, 'xl/worksheets/sheet2.xml')
        rows3 = parse_sheet(z, 'xl/worksheets/sheet3.xml')
        
        names = set()
        for r in rows2[1:]:
            if len(r) > 27 and r[27]: names.add(r[27].strip())
        for r in rows3[1:]:
            if len(r) > 5 and r[5]: names.add(r[5].strip())
        
        print(f'Found {len(names)} engineers.')
        for name in names:
            if name and name != '[Shared]':
                eng = Engineer(name=name, role='口味工程师', region='待确认')
                db.add(eng)
        db.commit()
        print(f'Imported {len(names)} engineers successfully.')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
