"""
Database Manager — Data Layer (Chapter 3, Section 3.7)

Implements the five-table SQLite schema:
  Users, FaceEncodings, Sessions, AttendanceRecords, Admins

All public methods create a fresh connection per call so they are safe to
call from multiple threads (background recognition + main GUI thread).
"""

import sqlite3
import hashlib
import os
import threading
from datetime import datetime
from src.config import DB_PATH


class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._db_path = DB_PATH
        self._lock = threading.Lock()
        self._init_database()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self):
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")   # Better concurrent write
        return conn

    def _init_database(self):
        """Create all tables and indexes on first run. Insert default admin."""
        ddl = """
        CREATE TABLE IF NOT EXISTS Users (
            user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            institution_id TEXT    NOT NULL UNIQUE,
            department     TEXT    NOT NULL,
            programme      TEXT    NOT NULL,
            created_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS FaceEncodings (
            encoding_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            encoding_blob BLOB   NOT NULL,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Sessions (
            session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code   TEXT    NOT NULL,
            course_title  TEXT    NOT NULL,
            lecturer_name TEXT    NOT NULL,
            date          TEXT    NOT NULL,
            start_time    TEXT    NOT NULL,
            end_time      TEXT,
            is_active     INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS AttendanceRecords (
            record_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            timestamp  TEXT    NOT NULL,
            FOREIGN KEY (user_id)    REFERENCES Users(user_id)    ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES Sessions(session_id) ON DELETE CASCADE,
            UNIQUE(user_id, session_id)
        );

        CREATE TABLE IF NOT EXISTS Admins (
            admin_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_enc_user     ON FaceEncodings(user_id);
        CREATE INDEX IF NOT EXISTS idx_att_session  ON AttendanceRecords(session_id);
        CREATE INDEX IF NOT EXISTS idx_att_user     ON AttendanceRecords(user_id);
        CREATE INDEX IF NOT EXISTS idx_sess_course  ON Sessions(course_code);
        """
        with self._lock:
            conn = self._connect()
            try:
                conn.executescript(ddl)
                cur = conn.execute("SELECT COUNT(*) FROM Admins")
                if cur.fetchone()[0] == 0:
                    h = hashlib.sha256("admin123".encode()).hexdigest()
                    conn.execute(
                        "INSERT INTO Admins (username, password_hash) VALUES (?, ?)",
                        ("admin", h)
                    )
                    conn.commit()
            finally:
                conn.close()

    # ------------------------------------------------------------------
    # Admin operations
    # ------------------------------------------------------------------

    def verify_admin(self, username: str, password: str):
        ph = hashlib.sha256(password.encode()).hexdigest()
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT admin_id, username FROM Admins WHERE username=? AND password_hash=?",
                (username, ph)
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def change_admin_password(self, username: str, new_password: str):
        ph = hashlib.sha256(new_password.encode()).hexdigest()
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE Admins SET password_hash=? WHERE username=?",
                    (ph, username)
                )
                conn.commit()
            finally:
                conn.close()

    # ------------------------------------------------------------------
    # User operations
    # ------------------------------------------------------------------

    def add_user(self, name: str, institution_id: str, department: str, programme: str) -> int:
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    "INSERT INTO Users (name, institution_id, department, programme) VALUES (?, ?, ?, ?)",
                    (name, institution_id, department, programme)
                )
                conn.commit()
                return cur.lastrowid
            finally:
                conn.close()

    def get_user(self, user_id: int):
        conn = self._connect()
        try:
            cur = conn.execute("SELECT * FROM Users WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_by_institution_id(self, institution_id: str):
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT * FROM Users WHERE institution_id=?", (institution_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_users(self):
        conn = self._connect()
        try:
            cur = conn.execute("SELECT * FROM Users ORDER BY name")
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def delete_user(self, user_id: int):
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("DELETE FROM Users WHERE user_id=?", (user_id,))
                conn.commit()
            finally:
                conn.close()

    def get_user_count(self) -> int:
        conn = self._connect()
        try:
            return conn.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Face encoding operations
    # ------------------------------------------------------------------

    def add_face_encoding(self, user_id: int, encoding_blob: bytes):
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO FaceEncodings (user_id, encoding_blob) VALUES (?, ?)",
                    (user_id, encoding_blob)
                )
                conn.commit()
            finally:
                conn.close()

    def get_all_encodings(self):
        """Returns rows: user_id, name, institution_id, encoding_blob."""
        conn = self._connect()
        try:
            cur = conn.execute("""
                SELECT fe.user_id, u.name, u.institution_id, fe.encoding_blob
                FROM FaceEncodings fe
                JOIN Users u ON fe.user_id = u.user_id
            """)
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def has_encodings(self, user_id: int) -> bool:
        conn = self._connect()
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM FaceEncodings WHERE user_id=?", (user_id,)
            ).fetchone()[0]
            return n > 0
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Session operations
    # ------------------------------------------------------------------

    def create_session(self, course_code: str, course_title: str,
                       lecturer_name: str, date: str, start_time: str) -> int:
        with self._lock:
            conn = self._connect()
            try:
                # Deactivate any running session first
                conn.execute("UPDATE Sessions SET is_active=0 WHERE is_active=1")
                cur = conn.execute(
                    """INSERT INTO Sessions
                       (course_code, course_title, lecturer_name, date, start_time, is_active)
                       VALUES (?, ?, ?, ?, ?, 1)""",
                    (course_code, course_title, lecturer_name, date, start_time)
                )
                conn.commit()
                return cur.lastrowid
            finally:
                conn.close()

    def get_active_session(self):
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT * FROM Sessions WHERE is_active=1 ORDER BY session_id DESC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def close_session(self, session_id: int):
        end_time = datetime.now().strftime("%H:%M:%S")
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE Sessions SET is_active=0, end_time=? WHERE session_id=?",
                    (end_time, session_id)
                )
                conn.commit()
            finally:
                conn.close()

    def get_all_sessions(self):
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT * FROM Sessions ORDER BY date DESC, start_time DESC"
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_session_count_for_course(self, course_code: str) -> int:
        conn = self._connect()
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM Sessions WHERE course_code=?", (course_code,)
            ).fetchone()[0]
        finally:
            conn.close()

    def get_distinct_courses(self):
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT DISTINCT course_code, course_title FROM Sessions ORDER BY course_code"
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Attendance record operations
    # ------------------------------------------------------------------

    def mark_attendance(self, user_id: int, session_id: int, timestamp: str) -> bool:
        """
        Insert attendance record. Returns True on success, False if already marked.
        Uses atomic INSERT to enforce the UNIQUE(user_id, session_id) constraint.
        """
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO AttendanceRecords (user_id, session_id, timestamp) VALUES (?, ?, ?)",
                    (user_id, session_id, timestamp)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Duplicate — already marked for this session
            finally:
                conn.close()

    def is_attendance_marked(self, user_id: int, session_id: int) -> bool:
        conn = self._connect()
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM AttendanceRecords WHERE user_id=? AND session_id=?",
                (user_id, session_id)
            ).fetchone()[0]
            return n > 0
        finally:
            conn.close()

    def get_attendance_records(self, session_id=None, user_id=None, date_from=None, date_to=None):
        query = """
            SELECT ar.record_id, u.name, u.institution_id, u.department,
                   s.course_code, s.course_title, s.date, ar.timestamp, ar.session_id
            FROM AttendanceRecords ar
            JOIN Users    u ON ar.user_id    = u.user_id
            JOIN Sessions s ON ar.session_id = s.session_id
        """
        params = []
        conds = []
        if session_id:
            conds.append("ar.session_id=?");  params.append(session_id)
        if user_id:
            conds.append("ar.user_id=?");     params.append(user_id)
        if date_from:
            conds.append("s.date>=?");        params.append(date_from)
        if date_to:
            conds.append("s.date<=?");        params.append(date_to)
        if conds:
            query += " WHERE " + " AND ".join(conds)
        query += " ORDER BY ar.timestamp DESC"

        conn = self._connect()
        try:
            cur = conn.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_today_attendance_count(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._connect()
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM AttendanceRecords ar "
                "JOIN Sessions s ON ar.session_id=s.session_id WHERE s.date=?",
                (today,)
            ).fetchone()[0]
        finally:
            conn.close()

    def get_session_attendance_count(self, session_id: int) -> int:
        conn = self._connect()
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM AttendanceRecords WHERE session_id=?",
                (session_id,)
            ).fetchone()[0]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Report data (Chapter 3, Section 3.8.3)
    # ------------------------------------------------------------------

    def get_report_data(self, course_code: str, threshold_pct: float = 75.0):
        """
        Implements GenerateReport algorithm from Chapter 3.
        Returns (rows, total_sessions).
        Each row: name, institution_id, department, programme,
                  attended, total_sessions, percentage, status
        """
        conn = self._connect()
        try:
            total = conn.execute(
                "SELECT COUNT(*) FROM Sessions WHERE course_code=?", (course_code,)
            ).fetchone()[0]

            if total == 0:
                return [], 0

            cur = conn.execute("""
                SELECT u.user_id, u.name, u.institution_id, u.department, u.programme,
                       COUNT(ar.record_id) AS attended
                FROM Users u
                LEFT JOIN AttendanceRecords ar ON u.user_id = ar.user_id
                LEFT JOIN Sessions s
                    ON ar.session_id = s.session_id AND s.course_code = ?
                GROUP BY u.user_id
                HAVING attended > 0
                ORDER BY attended DESC
            """, (course_code,))

            rows = []
            for r in cur.fetchall():
                row = dict(r)
                row['total_sessions'] = total
                row['percentage'] = round((row['attended'] / total) * 100, 1)
                row['status'] = 'PASS' if row['percentage'] >= threshold_pct else 'FAIL'
                rows.append(row)
            return rows, total
        finally:
            conn.close()
