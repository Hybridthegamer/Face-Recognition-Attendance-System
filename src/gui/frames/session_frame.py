"""
Session Frame — GUI for creating a session and running live recognition.

Left panel  : session configuration form + live attendance log
Right panel : live webcam feed with face annotation
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime
import cv2

from src.config import COLORS, FONTS
from src.gui.widgets import make_button, make_entry, ScrollableTreeview
from src.attendance.attendance_controller import AttendanceController
from src.attendance.session_manager import SessionManager


class SessionFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['bg'])
        self.app = app
        self._ctrl = AttendanceController(app.db)
        self._session_mgr = SessionManager(app.db)
        self._active_session = None
        self._poll_id = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS['header_bg'],
                          highlightthickness=1, highlightbackground=COLORS['border'])
        header.pack(fill='x')
        tk.Label(header, text="Session & Live Recognition",
                 font=FONTS['title'], bg=COLORS['header_bg'], fg=COLORS['text_primary'],
                 padx=24, pady=16).pack(side='left')
        self._session_status_lbl = tk.Label(header, text="● No active session",
                                             font=FONTS['body'],
                                             bg=COLORS['header_bg'],
                                             fg=COLORS['danger'], padx=16)
        self._session_status_lbl.pack(side='right')

        # Two-column body
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(fill='both', expand=True, padx=16, pady=14)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ---- LEFT ----
        left = tk.Frame(body, bg=COLORS['card_bg'],
                        highlightthickness=1, highlightbackground=COLORS['border'])
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        # Session form
        form = tk.Frame(left, bg=COLORS['card_bg'])
        form.grid(row=0, column=0, sticky='ew', padx=18, pady=16)

        tk.Label(form, text="New Session", font=FONTS['heading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 10))

        self._sv = {}
        for key, label in [
            ('course_code',   'Course Code *'),
            ('course_title',  'Course Title *'),
            ('lecturer_name', 'Lecturer Name *'),
        ]:
            tk.Label(form, text=label, font=FONTS['subheading'],
                     bg=COLORS['card_bg'], fg=COLORS['text_secondary'],
                     anchor='w').pack(fill='x', pady=(6, 2))
            var = tk.StringVar()
            self._sv[key] = var
            make_entry(form, textvariable=var, width=30).pack(fill='x')

        btn_row = tk.Frame(form, bg=COLORS['card_bg'])
        btn_row.pack(fill='x', pady=14)
        self._start_btn = make_button(btn_row, "▶  Start Session",
                                      command=self._start_session, style='success')
        self._start_btn.pack(side='left', padx=(0, 8))
        self._stop_btn = make_button(btn_row, "■  End Session",
                                     command=self._stop_session, style='danger')
        self._stop_btn.pack(side='left')
        self._stop_btn.config(state='disabled')

        tk.Frame(left, bg=COLORS['border'], height=1).grid(row=1, column=0, sticky='ew')

        # Attendance log
        log_frame = tk.Frame(left, bg=COLORS['card_bg'])
        log_frame.grid(row=2, column=0, sticky='nsew', padx=14, pady=12)
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)

        tk.Label(log_frame, text="Attendance Log (this session)",
                 font=FONTS['subheading'], bg=COLORS['card_bg'],
                 fg=COLORS['text_secondary']).grid(row=0, column=0, sticky='w', pady=(0, 6))

        self._log_tree = ScrollableTreeview(
            log_frame,
            columns=('name', 'id', 'time'),
            headings=('Name', 'Institution ID', 'Time'),
            col_widths=(160, 110, 90),
        )
        self._log_tree.grid(row=1, column=0, sticky='nsew')

        self._log_count_var = tk.StringVar(value="0 students marked")
        tk.Label(log_frame, textvariable=self._log_count_var,
                 font=FONTS['small'], bg=COLORS['card_bg'],
                 fg=COLORS['text_secondary']).grid(row=2, column=0, sticky='w', pady=(4, 0))

        # ---- RIGHT: video ----
        right = tk.Frame(body, bg=COLORS['card_bg'],
                         highlightthickness=1, highlightbackground=COLORS['border'])
        right.grid(row=0, column=1, sticky='nsew')
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        tk.Label(right, text="Live Recognition Feed",
                 font=FONTS['subheading'], bg=COLORS['card_bg'],
                 fg=COLORS['text_secondary'],
                 padx=16, pady=10).grid(row=0, column=0, sticky='w')

        self._video_label = tk.Label(right, bg='#0f1520', relief='flat')
        self._video_label.grid(row=1, column=0, sticky='nsew', padx=12, pady=(0, 12))

        tk.Label(self._video_label,
                 text="Live feed will appear here\nonce a session is started",
                 bg='#0f1520', fg='#4a5568', font=FONTS['body']).place(relx=0.5, rely=0.5,
                                                                        anchor='center')

        self._fps_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self._fps_var, font=FONTS['small'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary'],
                 padx=16).grid(row=2, column=0, sticky='w')

        self._log_rows = []

    # ------------------------------------------------------------------
    # Session control
    # ------------------------------------------------------------------

    def _start_session(self):
        code    = self._sv['course_code'].get().strip().upper()
        title   = self._sv['course_title'].get().strip()
        lecturer = self._sv['lecturer_name'].get().strip()

        if not all([code, title, lecturer]):
            messagebox.showwarning("Incomplete", "All session fields are required.", parent=self)
            return

        session_id = self._session_mgr.create_session(code, title, lecturer)
        ok, msg = self._ctrl.start_session(session_id)
        if not ok:
            self.app.db.close_session(session_id)
            messagebox.showerror("Error", msg, parent=self)
            return

        self._active_session = session_id
        self._log_rows.clear()
        self._log_tree.clear()
        self._log_count_var.set("0 students marked")
        self._start_btn.config(state='disabled')
        self._stop_btn.config(state='normal')
        self._session_status_lbl.config(
            text=f"● Session active: {code}", fg=COLORS['success']
        )
        self._poll_queues()

    def _stop_session(self):
        if self._poll_id:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self._ctrl.stop_session()
        self._active_session = None
        self._start_btn.config(state='normal')
        self._stop_btn.config(state='disabled')
        self._session_status_lbl.config(text="● No active session", fg=COLORS['danger'])
        self._video_label.config(image='',
                                  text="Live feed will appear here\nonce a session is started")
        messagebox.showinfo("Session Ended",
                            "The attendance session has been closed successfully.", parent=self)

    # ------------------------------------------------------------------
    # Polling queues on main thread
    # ------------------------------------------------------------------

    def _poll_queues(self):
        import queue

        # Video frames
        try:
            frame = self._ctrl.frame_queue.get_nowait()
            self._display_frame(frame)
        except queue.Empty:
            pass

        # Attendance events
        try:
            while True:
                event = self._ctrl.attendance_queue.get_nowait()
                self._add_log_entry(event)
        except queue.Empty:
            pass

        if self._ctrl.is_running():
            self._poll_id = self.after(30, self._poll_queues)
        else:
            # Camera disconnected unexpectedly
            if self._active_session:
                self._stop_session()

    def _display_frame(self, bgr_frame):
        # Dynamically size to fill the label
        lw = max(self._video_label.winfo_width(), 640)
        lh = max(self._video_label.winfo_height(), 400)
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).resize((lw, lh), Image.LANCZOS)
        photo = ImageTk.PhotoImage(pil)
        self._video_label.config(image=photo, text='')
        self._video_label.image = photo

    def _add_log_entry(self, event):
        time_str = event['timestamp'].split(' ')[-1]
        row = (event['name'], event['institution_id'], time_str)
        self._log_rows.insert(0, row)
        self._log_tree.insert_rows(self._log_rows)
        self._log_count_var.set(f"{len(self._log_rows)} student(s) marked")

    def on_show(self):
        active = self.app.db.get_active_session()
        if active and not self._ctrl.is_running():
            self._session_status_lbl.config(
                text=f"● Session from previous run: {active['course_code']}",
                fg=COLORS['warning']
            )
