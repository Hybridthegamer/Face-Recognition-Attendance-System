"""
Session Manager — thin wrapper over DatabaseManager for session lifecycle.
Corresponds to the Session entity in the UML class diagram (Chapter 3).
"""

from datetime import datetime


class SessionManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_session(self, course_code: str, course_title: str, lecturer_name: str) -> int:
        now = datetime.now()
        return self.db.create_session(
            course_code=course_code,
            course_title=course_title,
            lecturer_name=lecturer_name,
            date=now.strftime("%Y-%m-%d"),
            start_time=now.strftime("%H:%M:%S"),
        )

    def get_active_session(self):
        return self.db.get_active_session()

    def close_session(self, session_id: int):
        self.db.close_session(session_id)

    def get_all_sessions(self):
        return self.db.get_all_sessions()

    def get_distinct_courses(self):
        return self.db.get_distinct_courses()
