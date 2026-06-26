"""
Home / Dashboard Frame — statistics and quick access shortcuts.
"""

import tkinter as tk
from datetime import datetime
from src.config import COLORS, FONTS
from src.gui.widgets import make_label, make_button, Card


class HomeFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['bg'])
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Page header
        header = tk.Frame(self, bg=COLORS['header_bg'],
                          highlightthickness=1, highlightbackground=COLORS['border'])
        header.pack(fill='x', pady=(0, 0))
        tk.Label(header, text="Dashboard", font=FONTS['title'],
                 bg=COLORS['header_bg'], fg=COLORS['text_primary'],
                 padx=24, pady=16).pack(side='left')
        self._clock_lbl = tk.Label(header, text="", font=FONTS['body'],
                                    bg=COLORS['header_bg'], fg=COLORS['text_secondary'],
                                    padx=24)
        self._clock_lbl.pack(side='right')

        # Content
        content = tk.Frame(self, bg=COLORS['bg'])
        content.pack(fill='both', expand=True, padx=24, pady=20)

        # Stat cards row
        stats_row = tk.Frame(content, bg=COLORS['bg'])
        stats_row.pack(fill='x')
        stats_row.columnconfigure((0, 1, 2, 3), weight=1)

        self._stat_vars = {}
        stat_defs = [
            ('enrolled_users',    'Enrolled Users',         COLORS['primary']),
            ('today_attendance',  "Today's Attendance",     COLORS['success']),
            ('total_sessions',    'Total Sessions',         COLORS['warning']),
            ('active_session',    'Active Session',         COLORS['danger']),
        ]
        for col, (key, label, color) in enumerate(stat_defs):
            card = tk.Frame(stats_row, bg=color, relief='flat')
            card.grid(row=0, column=col, padx=8, pady=4, sticky='ew')
            var = tk.StringVar(value="—")
            self._stat_vars[key] = var
            tk.Label(card, textvariable=var, font=('Helvetica', 28, 'bold'),
                     bg=color, fg='white').pack(padx=20, pady=(16, 4))
            tk.Label(card, text=label, font=FONTS['small'],
                     bg=color, fg='white').pack(padx=20, pady=(0, 16))

        # Quick actions
        qa_frame = tk.LabelFrame(content, text=" Quick Actions ",
                                  bg=COLORS['bg'], fg=COLORS['text_secondary'],
                                  font=FONTS['subheading'], relief='groove', bd=1)
        qa_frame.pack(fill='x', pady=20, padx=4)

        actions = [
            ("Enroll New User",      lambda: self.app.show_frame('enrollment'), 'primary'),
            ("Start New Session",    lambda: self.app.show_frame('session'),    'success'),
            ("View Records",         lambda: self.app.show_frame('records'),    'neutral'),
            ("Generate Report",      lambda: self.app.show_frame('reports'),    'warning'),
        ]
        for i, (text, cmd, style) in enumerate(actions):
            make_button(qa_frame, text, command=cmd, style=style,
                        width=20).grid(row=0, column=i, padx=12, pady=16)

        # Active session info
        self._session_card = Card(content)
        self._session_card.pack(fill='x', padx=4)
        body = self._session_card.body()
        tk.Label(body, text="Active Session", font=FONTS['subheading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(anchor='w')
        self._session_info_var = tk.StringVar(value="No active session")
        tk.Label(body, textvariable=self._session_info_var, font=FONTS['body'],
                 bg=COLORS['card_bg'], fg=COLORS['text_primary']).pack(anchor='w', pady=(4, 0))

        self._refresh()
        self._tick()

    def _refresh(self):
        db = self.app.db
        self._stat_vars['enrolled_users'].set(str(db.get_user_count()))
        self._stat_vars['today_attendance'].set(str(db.get_today_attendance_count()))
        sessions = db.get_all_sessions()
        self._stat_vars['total_sessions'].set(str(len(sessions)))

        active = db.get_active_session()
        if active:
            self._stat_vars['active_session'].set("LIVE")
            info = (f"{active['course_code']} — {active['course_title']}\n"
                    f"Lecturer: {active['lecturer_name']}  |  "
                    f"Date: {active['date']}  |  Started: {active['start_time']}")
            self._session_info_var.set(info)
        else:
            self._stat_vars['active_session'].set("None")
            self._session_info_var.set("No active session")

    def _tick(self):
        now = datetime.now().strftime("%A, %d %B %Y  %H:%M:%S")
        self._clock_lbl.config(text=now)
        self.after(1000, self._tick)

    def on_show(self):
        self._refresh()
