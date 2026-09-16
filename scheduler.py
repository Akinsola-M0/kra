from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from config import REMINDER_MINUTES
from database import get_connection
from mail_service import send_mail
from network import is_connected


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


def check_reminders():
    now = datetime.now()

    with get_connection() as conn:
        c = conn.cursor()
        auto_mark_missed(c, now)

        c.execute("""
            SELECT class_sessions.id,
                   class_sessions.session_date,
                   class_sessions.session_time,
                   class_sessions.day_reminder_sent,
                   class_sessions.minute_reminder_sent,
                   students.name,
                   students.email,
                   classes.title
            FROM class_sessions
            JOIN students ON class_sessions.student_id = students.id
            JOIN classes ON class_sessions.class_id = classes.id
            WHERE status='scheduled'
        """)

        sessions = c.fetchall()
        online = is_connected()

        for session in sessions:
            (
                session_id,
                date_value,
                time_value,
                day_sent,
                minute_sent,
                student_name,
                student_email,
                class_title,
            ) = session
            session_datetime = datetime.strptime(
                date_value + " " + time_value,
                "%Y-%m-%d %H:%M"
            )

            if not online or not student_email or now >= session_datetime:
                continue

            if (
                not day_sent
                and session_datetime - timedelta(days=1) <= now < session_datetime
            ):
                if send_mail(
                    student_email,
                    "Class Reminder (Tomorrow)",
                    (
                        f"Hello {student_name},\n\n"
                        f"This is a reminder that your {class_title} class is scheduled for "
                        f"{date_value} at {time_value}.\n\n"
                        "Please be prepared and on time."
                    )
                ):
                    c.execute("""
                        UPDATE class_sessions
                        SET day_reminder_sent=1
                        WHERE id=?
                    """, (session_id,))

            if (
                not minute_sent
                and session_datetime - timedelta(minutes=REMINDER_MINUTES) <= now < session_datetime
            ):
                if send_mail(
                    student_email,
                    "Class Reminder (Soon)",
                    (
                        f"Hello {student_name},\n\n"
                        f"Your {class_title} class starts in {REMINDER_MINUTES} minutes "
                        f"at {time_value}.\n\n"
                        "Please join soon."
                    )
                ):
                    c.execute("""
                        UPDATE class_sessions
                        SET minute_reminder_sent=1
                        WHERE id=?
                    """, (session_id,))


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_reminders, "interval", minutes=1, id="check_reminders")
    scheduler.start()
    return scheduler
