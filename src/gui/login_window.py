"""
Login Window (NFR6 — administrator authentication before access).
Default credentials: admin / admin123
"""

import tkinter as tk
from tkinter import messagebox
from src.config import COLORS, FONTS
from src.gui.widgets import make_button, make_entry


class LoginWindow(tk.Toplevel):
    def __init__(self, parent, db_manager, on_success):
        super().__init__(parent)
        self.db = db_manager
        self._on_success = on_success

        self.title("Login — Face Recognition Attendance System")
        self.resizable(False, False)
        self.configure(bg=COLORS['sidebar_bg'])
        self.grab_set()  # Modal

        w, h = 420, 500
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        self._build_ui()
        self.bind('<Return>', lambda e: self._login())

    def _build_ui(self):
        # Header
        tk.Label(self, text="🎓", font=('Helvetica', 48),
                 bg=COLORS['sidebar_bg'], fg='white').pack(pady=(40, 8))
        tk.Label(self, text="Face Recognition\nAttendance System",
                 font=('Helvetica', 16, 'bold'),
                 bg=COLORS['sidebar_bg'], fg='white',
                 justify='center').pack()
        tk.Label(self, text="Administrator Login",
                 font=FONTS['body'],
                 bg=COLORS['sidebar_bg'], fg=COLORS['sidebar_text']).pack(pady=(4, 30))

        # Card
        card = tk.Frame(self, bg='white', relief='flat',
                        highlightthickness=1, highlightbackground=COLORS['border'])
        card.pack(padx=40, fill='x')

        inner = tk.Frame(card, bg='white')
        inner.pack(padx=24, pady=24, fill='x')

        # Username
        tk.Label(inner, text="Username", font=FONTS['subheading'],
                 bg='white', fg=COLORS['text_secondary'],
                 anchor='w').pack(fill='x')
        self._username_var = tk.StringVar(value="admin")
        make_entry(inner, textvariable=self._username_var, width=32).pack(fill='x', pady=(4, 14))

        # Password
        tk.Label(inner, text="Password", font=FONTS['subheading'],
                 bg='white', fg=COLORS['text_secondary'],
                 anchor='w').pack(fill='x')
        self._password_var = tk.StringVar()
        make_entry(inner, textvariable=self._password_var, show='•', width=32).pack(fill='x', pady=(4, 20))

        make_button(inner, "LOGIN", command=self._login, width=30).pack(fill='x')

        # Status
        self._status_var = tk.StringVar()
        tk.Label(self, textvariable=self._status_var,
                 font=FONTS['small'], bg=COLORS['sidebar_bg'],
                 fg='#ff8080').pack(pady=8)

        tk.Label(self, text="Default: admin / admin123",
                 font=FONTS['small'],
                 bg=COLORS['sidebar_bg'], fg=COLORS['sidebar_text']).pack()

    def _login(self):
        username = self._username_var.get().strip()
        password = self._password_var.get()
        if not username or not password:
            self._status_var.set("Please enter both username and password.")
            return
        admin = self.db.verify_admin(username, password)
        if admin:
            self._on_success(admin)
            self.destroy()
        else:
            self._status_var.set("Invalid username or password.")
            self._password_var.set("")
