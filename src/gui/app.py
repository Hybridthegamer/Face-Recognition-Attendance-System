"""
Application controller — initialises the database, shows login, and
manages the transition between login window and main window.
"""

import tkinter as tk
from src.database.db_manager import DatabaseManager


class FaceAttendanceApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hidden until login succeeds

        self.db = DatabaseManager()
        self.current_admin: dict = {}

        self._main_window = None
        self.show_login()

    # ------------------------------------------------------------------
    # Public navigation helpers (used by MainWindow and frames)
    # ------------------------------------------------------------------

    def show_login(self):
        from src.gui.login_window import LoginWindow
        LoginWindow(self.root, self.db, self._on_login_success)

    def show_frame(self, name: str):
        if self._main_window:
            self._main_window.show_frame(name)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_login_success(self, admin: dict):
        self.current_admin = admin
        self.root.deiconify()
        if self._main_window is None:
            from src.gui.main_window import MainWindow
            self._main_window = MainWindow(self.root, self)
        else:
            self._main_window.show_frame('home')

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self):
        self.root.mainloop()
