"""
Main Window — three-tier presentation layer.

Layout:
  +----+----------------------------------+
  |    |  Header (page title + clock)    |
  |    +----------------------------------+
  |    |                                  |
  | S  |   Content area (swapped frames) |
  | I  |                                  |
  | D  |                                  |
  | E  |                                  |
  | B  |                                  |
  | A  |                                  |
  | R  |                                  |
  +----+----------------------------------+

Satisfies NFR4: all primary actions within ≤ 3 clicks from home screen.
"""

import tkinter as tk
from src.config import COLORS, FONTS, WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH


NAV_ITEMS = [
    ('home',       '⌂  Dashboard'),
    ('enrollment', '➕  Enrol User'),
    ('session',    '▶  Session'),
    ('records',    '📋  Records'),
    ('reports',    '📊  Reports'),
    ('users',      '👥  Users'),
]


class MainWindow:
    def __init__(self, root: tk.Tk, app):
        self.root = root
        self.app = app
        self._frames = {}
        self._current = None
        self._nav_buttons = {}

        self._build_window()
        self._build_sidebar()
        self._build_content_area()
        self._register_frames()
        self.show_frame('home')

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _build_window(self):
        self.root.title("Face Recognition Attendance System")
        self.root.configure(bg=COLORS['sidebar_bg'])
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - WINDOW_WIDTH) // 2
        y = (sh - WINDOW_HEIGHT) // 2
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=COLORS['sidebar_bg'],
                                width=SIDEBAR_WIDTH)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Logo / system title
        logo_frame = tk.Frame(self.sidebar, bg=COLORS['sidebar_bg'])
        logo_frame.pack(fill='x', pady=(20, 6))
        tk.Label(logo_frame, text="🎓", font=('Helvetica', 28),
                 bg=COLORS['sidebar_bg'], fg='white').pack()
        tk.Label(logo_frame, text="FaceAttend",
                 font=FONTS['logo'], bg=COLORS['sidebar_bg'],
                 fg='white').pack()
        tk.Label(logo_frame, text="Attendance System",
                 font=FONTS['small'], bg=COLORS['sidebar_bg'],
                 fg=COLORS['sidebar_text']).pack()

        # Divider
        tk.Frame(self.sidebar, bg='#2d3a5a', height=1).pack(fill='x', pady=12)

        # Navigation buttons
        for key, label in NAV_ITEMS:
            btn = tk.Button(
                self.sidebar, text=label,
                font=FONTS['sidebar'],
                bg=COLORS['sidebar_bg'], fg=COLORS['sidebar_text'],
                relief='flat', anchor='w', padx=20, pady=10,
                cursor='hand2', activebackground=COLORS['sidebar_hover'],
                activeforeground='white',
                command=lambda k=key: self.show_frame(k),
            )
            btn.pack(fill='x')
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['sidebar_hover']))
            btn.bind('<Leave>', lambda e, b=btn, k=key:
                     b.config(bg=COLORS['sidebar_active']
                              if self._current == k else COLORS['sidebar_bg']))
            self._nav_buttons[key] = btn

        # Spacer pushes logout to bottom
        tk.Frame(self.sidebar, bg=COLORS['sidebar_bg']).pack(fill='y', expand=True)

        # Admin info + logout
        tk.Frame(self.sidebar, bg='#2d3a5a', height=1).pack(fill='x')
        admin_info = tk.Frame(self.sidebar, bg=COLORS['sidebar_bg'])
        admin_info.pack(fill='x', pady=8)
        tk.Label(admin_info, text=f"Logged in as",
                 font=FONTS['small'], bg=COLORS['sidebar_bg'],
                 fg=COLORS['sidebar_text']).pack(padx=16, anchor='w')
        self._admin_lbl = tk.Label(admin_info,
                                    text=self.app.current_admin.get('username', 'admin'),
                                    font=('Helvetica', 10, 'bold'),
                                    bg=COLORS['sidebar_bg'], fg='white')
        self._admin_lbl.pack(padx=16, anchor='w')
        tk.Button(
            self.sidebar, text="⏻  Logout",
            font=FONTS['small'], bg='#2d3a5a', fg='#ff8080',
            relief='flat', padx=16, pady=6, cursor='hand2',
            command=self._logout,
        ).pack(fill='x', pady=(4, 12))

    def _build_content_area(self):
        self.content = tk.Frame(self.root, bg=COLORS['bg'])
        self.content.pack(side='right', fill='both', expand=True)

    # ------------------------------------------------------------------
    # Frame management
    # ------------------------------------------------------------------

    def _register_frames(self):
        from src.gui.frames.home_frame       import HomeFrame
        from src.gui.frames.enrollment_frame import EnrollmentFrame
        from src.gui.frames.session_frame    import SessionFrame
        from src.gui.frames.records_frame    import RecordsFrame
        from src.gui.frames.report_frame     import ReportFrame
        from src.gui.frames.users_frame      import UsersFrame

        frame_classes = {
            'home':       HomeFrame,
            'enrollment': EnrollmentFrame,
            'session':    SessionFrame,
            'records':    RecordsFrame,
            'reports':    ReportFrame,
            'users':      UsersFrame,
        }
        for key, cls in frame_classes.items():
            frame = cls(self.content, self.app)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._frames[key] = frame

    def show_frame(self, name: str):
        if name not in self._frames:
            return
        # Reset previous nav button colour
        if self._current and self._current in self._nav_buttons:
            self._nav_buttons[self._current].config(bg=COLORS['sidebar_bg'])

        self._current = name
        self._frames[name].tkraise()
        self._frames[name].on_show()

        # Highlight active nav button
        if name in self._nav_buttons:
            self._nav_buttons[name].config(bg=COLORS['sidebar_active'], fg='white')

    # ------------------------------------------------------------------
    # Window / session events
    # ------------------------------------------------------------------

    def _logout(self):
        from tkinter import messagebox
        if messagebox.askyesno("Logout", "Are you sure you want to log out?",
                               parent=self.root):
            self._safe_shutdown()
            self.root.withdraw()
            self.app.show_login()

    def _on_close(self):
        self._safe_shutdown()
        self.root.destroy()

    def _safe_shutdown(self):
        """Stop any running recognition session before exit."""
        session_frame = self._frames.get('session')
        if session_frame and session_frame._ctrl.is_running():
            session_frame._ctrl.stop_session()
