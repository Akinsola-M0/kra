from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from database import get_connection


GRACE_PERIOD_MINUTES = 60


def auto_mark_missed(cursor, now):
    cursor.execute("""
        SELECT id, session_date, session_time, duration_hours
        FROM class_sessions
        WHERE status='scheduled'
    """)

    sessions = cursor.fetchall()

    for session in sessions:
        session_id, date_value, time_value, duration = session
        session_start = datetime.strptime(
            date_value + " " + time_value,
            "%Y-%m-%d %H:%M"
        )
        session_end = session_start + timedelta(hours=duration)
        deadline = session_end + timedelta(minutes=GRACE_PERIOD_MINUTES)

        if now > deadline:
            cursor.execute("""
                UPDATE class_sessions
                SET status='missed',
                    earnings=0,
                    payment_status='unpaid',
                    payment_date=NULL
                WHERE id=?
            """, (session_id,))


def check_scheduled_sessions():
    now = datetime.now()

    with get_connection() as conn:
        c = conn.cursor()
        auto_mark_missed(c, now)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_scheduled_sessions,
        "interval",
        minutes=1,
        id="check_scheduled_sessions"
    )
    scheduler.start()
    return scheduler
