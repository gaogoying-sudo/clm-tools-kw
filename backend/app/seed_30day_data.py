"""
生成近 30 天的完整 mock 数据
执行: python -m app.seed_30day_data
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import SyncTask, DailySession, SessionTask, Question, Engineer
from app.mock_data_generator import generate_tasks_for_engineer_date
from datetime import date, timedelta, datetime
import random
from sqlalchemy import text

def seed():
    db = SessionLocal()
    today = date.today()

    # Clear existing data
    for t in ['session_tasks', 'answers', 'experience_candidates', 'daily_sessions', 'sync_tasks']:
        db.execute(text(f'DELETE FROM {t}'))
    db.commit()

    total_tasks = 0
    total_sessions = 0
    engineers = db.query(Engineer).all()

    print(f'Generating data for {len(engineers)} engineers over 30 days...')

    for eng in engineers:
        work_days = sorted(random.sample(range(1, 31), k=random.randint(15, 25)))

        for day_offset in work_days:
            task_date = today - timedelta(days=day_offset)
            tasks_data = generate_tasks_for_engineer_date(eng.id, task_date)

            if tasks_data:
                # Insert tasks first
                inserted_tasks = []
                for td in tasks_data:
                    task = SyncTask(**td)
                    db.add(task)
                    inserted_tasks.append(task)
                    total_tasks += 1

                # 70% chance of session
                if random.random() < 0.7:
                    status = random.choices(
                        ['pending', 'pushed', 'submitted', 'submitted', 'submitted'],
                        weights=[20, 10, 70, 70, 70]
                    )[0]

                    submitted_at = None
                    duration = None
                    root_event = None

                    if status == 'submitted':
                        duration = random.randint(120, 600)
                        submitted_at = datetime.combine(task_date, datetime.min.time()) + timedelta(
                            hours=random.randint(18, 22), minutes=random.randint(0, 59)
                        )
                        root_event = random.choice([
                            'iterative_debugging', 'customer_feedback', 'key_adjustment',
                            'abnormal_failure', 'reusable_method', 'normal_day'
                        ])

                    session = DailySession(
                        engineer_id=eng.id,
                        session_date=task_date,
                        status=status,
                        question_count=random.randint(5, 9),
                        submitted_at=submitted_at,
                        duration_seconds=duration,
                        summary_snapshot=[
                            {'dish_name': t.dish_name, 'recipe_id': t.recipe_id,
                             'exec_count': t.exec_count, 'status': t.status}
                            for t in inserted_tasks
                        ],
                        root_event_type=root_event,
                    )
                    db.add(session)
                    db.flush()  # Get session.id

                    # Link tasks to session
                    for task in inserted_tasks:
                        st = SessionTask(session_id=session.id, sync_task_id=task.id)
                        db.add(st)

                    total_sessions += 1

        if eng.id % 6 == 0:
            print(f'  Engineer {eng.id}/36 done ({eng.name})')

    db.commit()
    print(f'\nDone!')
    print(f'Total tasks: {total_tasks}')
    print(f'Total sessions: {total_sessions}')

    # Verify
    task_count = db.query(SyncTask).count()
    session_count = db.query(DailySession).count()
    submitted = db.query(DailySession).filter(DailySession.status == 'submitted').count()
    print(f'Verified: {task_count} tasks, {session_count} sessions ({submitted} submitted)')
    db.close()

if __name__ == '__main__':
    seed()
