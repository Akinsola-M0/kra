import sqlite3
from datetime import date, datetime


DB_NAME = "classes.db"
SESSION_STATUSES = ("scheduled", "taken", "missed", "cancelled")
PAYMENT_STATUSES = ("unpaid", "paid")


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {column[1] for column in cursor.fetchall()}


def ensure_column(cursor, table_name, column_name, column_definition):
    existing_columns = get_table_columns(cursor, table_name)
    if column_name not in existing_columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def run_migrations(cursor):
    ensure_column(cursor, "students", "current_class", "TEXT")
    ensure_column(cursor, "students", "curriculum", "TEXT")

    ensure_column(cursor, "class_sessions", "status", "TEXT DEFAULT 'scheduled'")
    ensure_column(cursor, "class_sessions", "earnings", "REAL DEFAULT 0")
    ensure_column(cursor, "class_sessions", "payment_status", "TEXT DEFAULT 'unpaid'")
    ensure_column(cursor, "class_sessions", "payment_date", "TEXT")
    ensure_column(cursor, "class_sessions", "created_at", "TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO schema_migrations (name)
        VALUES ('class_sessions_status_payment_columns')
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_class_sessions_date
        ON class_sessions (session_date)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_class_sessions_status
        ON class_sessions (status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_class_sessions_payment_status
        ON class_sessions (payment_status)
    """)


def init_db():
    with get_connection() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                current_class TEXT,
                curriculum TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                hourly_rate REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS class_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                session_time TEXT NOT NULL,
                duration_hours REAL NOT NULL,
                status TEXT DEFAULT 'scheduled',
                earnings REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)
        run_migrations(c)


def normalize_payment(status, payment_status, payment_date):
    if status not in SESSION_STATUSES:
        raise ValueError("Session status is invalid.")

    if payment_status not in PAYMENT_STATUSES:
        raise ValueError("Payment status is invalid.")

    if status != "taken":
        return "unpaid", None

    if payment_status == "paid" and not payment_date:
        payment_date = date.today().isoformat()

    if payment_status == "unpaid":
        payment_date = None

    return payment_status, payment_date


def calculate_session_earnings(cursor, class_id, duration, status):
    if status != "taken":
        return 0

    cursor.execute("SELECT hourly_rate FROM classes WHERE id = ?", (class_id,))
    class_row = cursor.fetchone()
    if class_row is None:
        raise ValueError("Class not found.")

    return class_row[0] * duration


def add_student(name, email, current_class="", curriculum=""):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO students (name, email, current_class, curriculum)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, current_class, curriculum)
        )


def update_student(student_id, name, email, current_class="", curriculum=""):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            UPDATE students
            SET name = ?, email = ?, current_class = ?, curriculum = ?
            WHERE id = ?
            """,
            (name, email, current_class, curriculum, student_id)
        )

        if c.rowcount == 0:
            raise ValueError("Student not found.")


def delete_student(student_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM class_sessions WHERE student_id = ?",
            (student_id,)
        )
        session_count = c.fetchone()[0]

        if session_count:
            raise ValueError(
                "This student has sessions. Delete or reassign those sessions first."
            )

        c.execute("DELETE FROM students WHERE id = ?", (student_id,))

        if c.rowcount == 0:
            raise ValueError("Student not found.")


def add_class(title, description, rate):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO classes (title, description, hourly_rate) VALUES (?, ?, ?)",
            (title, description, rate)
        )


def update_class(class_id, title, description, rate):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            UPDATE classes
            SET title = ?, description = ?, hourly_rate = ?
            WHERE id = ?
            """,
            (title, description, rate, class_id)
        )

        if c.rowcount == 0:
            raise ValueError("Class not found.")


def delete_class(class_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM class_sessions WHERE class_id = ?",
            (class_id,)
        )
        session_count = c.fetchone()[0]

        if session_count:
            raise ValueError(
                "This class has sessions. Delete or reassign those sessions first."
            )

        c.execute("DELETE FROM classes WHERE id = ?", (class_id,))

        if c.rowcount == 0:
            raise ValueError("Class not found.")


def add_session(
    class_id,
    student_id,
    date_value,
    time_value,
    duration,
    status="scheduled",
    payment_status="unpaid",
    payment_date=None,
):
    with get_connection() as conn:
        c = conn.cursor()
        payment_status, payment_date = normalize_payment(
            status,
            payment_status,
            payment_date
        )
        earnings = calculate_session_earnings(c, class_id, duration, status)

        c.execute("""
            INSERT INTO class_sessions
            (
                class_id,
                student_id,
                session_date,
                session_time,
                duration_hours,
                status,
                earnings,
                payment_status,
                payment_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            class_id,
            student_id,
            date_value,
            time_value,
            duration,
            status,
            earnings,
            payment_status,
            payment_date,
        ))


def update_session(
    session_id,
    class_id,
    student_id,
    date_value,
    time_value,
    duration,
    status,
    payment_status,
    payment_date,
):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id
            FROM class_sessions
            WHERE id = ?
        """, (session_id,))

        if c.fetchone() is None:
            raise ValueError("Session not found.")

        payment_status, payment_date = normalize_payment(
            status,
            payment_status,
            payment_date
        )
        earnings = calculate_session_earnings(c, class_id, duration, status)

        c.execute("""
            UPDATE class_sessions
            SET class_id = ?,
                student_id = ?,
                session_date = ?,
                session_time = ?,
                duration_hours = ?,
                status = ?,
                earnings = ?,
                payment_status = ?,
                payment_date = ?
            WHERE id = ?
        """, (
            class_id,
            student_id,
            date_value,
            time_value,
            duration,
            status,
            earnings,
            payment_status,
            payment_date,
            session_id,
        ))


def get_students():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, name, email, current_class, curriculum, created_at
            FROM students
            ORDER BY name COLLATE NOCASE
        """)
        data = c.fetchall()
    return data


def get_classes():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM classes ORDER BY title COLLATE NOCASE")
        data = c.fetchall()
    return data


def build_session_filter_clause(
    search_text="",
    status="All",
    payment_status="All",
    date_from="",
    date_to="",
):
    clauses = []
    params = []

    if search_text:
        clauses.append("""
            (
                students.name LIKE ?
                OR classes.title LIKE ?
                OR class_sessions.session_date LIKE ?
                OR class_sessions.status LIKE ?
                OR class_sessions.payment_status LIKE ?
            )
        """)
        search_value = f"%{search_text}%"
        params.extend([search_value] * 5)

    if status and status != "All":
        clauses.append("class_sessions.status = ?")
        params.append(status)

    if payment_status and payment_status != "All":
        clauses.append("class_sessions.payment_status = ?")
        params.append(payment_status)

    if date_from:
        clauses.append("class_sessions.session_date >= ?")
        params.append(date_from)

    if date_to:
        clauses.append("class_sessions.session_date <= ?")
        params.append(date_to)

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


def get_sessions(
    search_text="",
    status="All",
    payment_status="All",
    date_from="",
    date_to="",
):
    with get_connection() as conn:
        c = conn.cursor()
        where_clause, params = build_session_filter_clause(
            search_text,
            status,
            payment_status,
            date_from,
            date_to
        )
        c.execute(f"""
            SELECT class_sessions.id,
                   students.name,
                   classes.title,
                   session_date,
                   session_time,
                   duration_hours,
                   status,
                   earnings,
                   payment_status,
                   payment_date
            FROM class_sessions
            JOIN students ON class_sessions.student_id = students.id
            JOIN classes ON class_sessions.class_id = classes.id
            {where_clause}
            ORDER BY session_date DESC, session_time DESC
        """, params)
        data = c.fetchall()
    return data


def get_session_report_rows(
    search_text="",
    status="All",
    payment_status="All",
    date_from="",
    date_to="",
):
    return get_sessions(
        search_text=search_text,
        status=status,
        payment_status=payment_status,
        date_from=date_from,
        date_to=date_to,
    )


def get_session(session_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id,
                   class_id,
                   student_id,
                   session_date,
                   session_time,
                   duration_hours,
                   status,
                   payment_status,
                   payment_date
            FROM class_sessions
            WHERE id = ?
        """, (session_id,))
        data = c.fetchone()
    return data


def mark_session_taken(session_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT classes.hourly_rate,
                   class_sessions.duration_hours,
                   class_sessions.payment_status,
                   class_sessions.payment_date
            FROM class_sessions
            JOIN classes ON class_sessions.class_id = classes.id
            WHERE class_sessions.id = ?
        """, (session_id,))

        row = c.fetchone()
        if row is None:
            raise ValueError("Session not found.")

        rate, duration, payment_status, payment_date = row
        earnings = rate * duration

        if payment_status == "paid" and not payment_date:
            payment_date = date.today().isoformat()

        c.execute("""
            UPDATE class_sessions
            SET status='taken',
                earnings=?,
                payment_status=?,
                payment_date=?
            WHERE id=?
        """, (earnings, payment_status, payment_date, session_id))


def delete_session(session_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM class_sessions WHERE id = ?", (session_id,))

        if c.rowcount == 0:
            raise ValueError("Session not found.")


def clear_all_sessions():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM class_sessions")


def get_total_earnings():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT SUM(earnings) FROM class_sessions WHERE status='taken'")
        result = c.fetchone()[0]
    return result if result else 0


def get_total_sessions_taken():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM class_sessions WHERE status='taken'")
        result = c.fetchone()[0]
    return result


def get_scheduled_sessions():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM class_sessions WHERE status='scheduled'")
        result = c.fetchone()[0]
    return result


def get_monthly_earnings():
    current_month = datetime.now().strftime("%Y-%m")
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT SUM(earnings)
            FROM class_sessions
            WHERE status='taken'
            AND session_date LIKE ?
        """, (f"{current_month}%",))
        result = c.fetchone()[0]
    return result if result else 0


def get_total_paid():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT SUM(earnings)
            FROM class_sessions
            WHERE status='taken'
            AND payment_status='paid'
        """)
        result = c.fetchone()[0]
    return result if result else 0


def get_total_unpaid():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT SUM(earnings)
            FROM class_sessions
            WHERE status='taken'
            AND payment_status='unpaid'
        """)
        result = c.fetchone()[0]
    return result if result else 0


def get_today_sessions():
    today = date.today().isoformat()
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT students.name,
                   classes.title,
                   session_time,
                   status
            FROM class_sessions
            JOIN students ON class_sessions.student_id = students.id
            JOIN classes ON class_sessions.class_id = classes.id
            WHERE session_date = ?
            ORDER BY session_time
        """, (today,))
        data = c.fetchall()
    return data
