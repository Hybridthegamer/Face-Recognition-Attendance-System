"""
Enrollment Frame — implements the GUI for the EnrolUser algorithm.

Left panel: user profile form
Right panel: live webcam feed + progress bar
"""

import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import cv2

from src.config import COLORS, FONTS, N_ENROLLMENT_IMAGES
from src.gui.widgets import make_button, make_entry
from src.recognition.enrollment_manager import EnrollmentManager


class EnrollmentFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['bg'])
        self.app = app
        self._mgr = EnrollmentManager(app.db)
        self._enrolling = False
        self._poll_after_id = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS['header_bg'],
                          highlightthickness=1, highlightbackground=COLORS['border'])
        header.pack(fill='x')
        tk.Label(header, text="Enrol New User", font=FONTS['title'],
                 bg=COLORS['header_bg'], fg=COLORS['text_primary'],
                 padx=24, pady=16).pack(side='left')

        # Two-column layout
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(fill='both', expand=True, padx=20, pady=16)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)

        # ---- LEFT: form ----
        left = tk.Frame(body, bg=COLORS['card_bg'],
                        highlightthickness=1, highlightbackground=COLORS['border'])
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        form = tk.Frame(left, bg=COLORS['card_bg'])
        form.pack(padx=20, pady=20, fill='x')

        tk.Label(form, text="User Profile", font=FONTS['heading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 12))

        self._vars = {}
        fields = [
            ('name',           'Full Name *'),
            ('institution_id', 'Matriculation / Staff ID *'),
            ('department',     'Department *'),
            ('programme',      'Programme / Role *'),
        ]
        for key, label in fields:
            tk.Label(form, text=label, font=FONTS['subheading'],
                     bg=COLORS['card_bg'], fg=COLORS['text_secondary'],
                     anchor='w').pack(fill='x', pady=(8, 2))
            var = tk.StringVar()
            self._vars[key] = var
            make_entry(form, textvariable=var, width=35).pack(fill='x')

        tk.Frame(form, bg=COLORS['border'], height=1).pack(fill='x', pady=16)

        self._start_btn = make_button(form, "Start Enrolment",
                                      command=self._start_enrollment,
                                      style='primary')
        self._start_btn.pack(fill='x')
        self._cancel_btn = make_button(form, "Cancel",
                                       command=self._cancel_enrollment,
                                       style='danger')
        self._cancel_btn.pack(fill='x', pady=(8, 0))
        self._cancel_btn.config(state='disabled')

        # Status label
        self._status_var = tk.StringVar(value="Fill in the form and click 'Start Enrolment'.")
        tk.Label(form, textvariable=self._status_var, font=FONTS['small'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary'],
                 wraplength=280, justify='left').pack(anchor='w', pady=(12, 0))

        # ---- RIGHT: video + progress ----
        right = tk.Frame(body, bg=COLORS['card_bg'],
                         highlightthickness=1, highlightbackground=COLORS['border'])
        right.grid(row=0, column=1, sticky='nsew')

        video_area = tk.Frame(right, bg=COLORS['card_bg'])
        video_area.pack(fill='both', expand=True, padx=16, pady=16)

        tk.Label(video_area, text="Webcam Preview", font=FONTS['subheading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(anchor='w')

        self._video_label = tk.Label(video_area, bg='#0f1520',
                                      relief='flat', width=64, height=24)
        self._video_label.pack(pady=(8, 12), fill='both', expand=True)

        # Placeholder text
        tk.Label(self._video_label, text="Camera feed will appear here\nwhen enrolment starts",
                 bg='#0f1520', fg='#4a5568', font=FONTS['body']).place(relx=0.5, rely=0.5,
                                                                        anchor='center')

        # Progress
        prog_frame = tk.Frame(right, bg=COLORS['card_bg'])
        prog_frame.pack(fill='x', padx=16, pady=(0, 16))

        tk.Label(prog_frame, text="Capture Progress", font=FONTS['subheading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(anchor='w')

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(prog_frame, variable=self._progress_var,
                                              maximum=N_ENROLLMENT_IMAGES,
                                              mode='determinate', length=400)
        self._progress_bar.pack(fill='x', pady=(4, 4))

        self._progress_label = tk.StringVar(value="0 / 0 images captured")
        tk.Label(prog_frame, textvariable=self._progress_label,
                 font=FONTS['small'], bg=COLORS['card_bg'],
                 fg=COLORS['text_secondary']).pack(anchor='w')

    # ------------------------------------------------------------------
    # Enrollment actions
    # ------------------------------------------------------------------

    def _start_enrollment(self):
        name    = self._vars['name'].get().strip()
        inst_id = self._vars['institution_id'].get().strip()
        dept    = self._vars['department'].get().strip()
        prog    = self._vars['programme'].get().strip()

        if not all([name, inst_id, dept, prog]):
            messagebox.showwarning("Incomplete Form",
                                   "All fields marked * are required.", parent=self)
            return

        self._enrolling = True
        self._start_btn.config(state='disabled')
        self._cancel_btn.config(state='normal')
        self._status_var.set("Starting webcam…")
        self._progress_var.set(0)
        self._progress_label.set("0 / 0 images captured")

        self._mgr.start_enrollment(
            name=name, institution_id=inst_id,
            department=dept, programme=prog,
            frame_callback=self._on_frame,
            progress_callback=self._on_progress,
            done_callback=self._on_done,
        )
        self._poll_frame_queue()

    def _cancel_enrollment(self):
        self._mgr.cancel()
        self._reset_ui()

    # ------------------------------------------------------------------
    # Callbacks from background thread (called on bg thread — only queue data)
    # ------------------------------------------------------------------

    # The enrollment manager calls frame_callback on the background thread.
    # We cannot update Tkinter from a non-main thread, so we store the latest
    # frame and let _poll_frame_queue (running on the main thread via after()) display it.

    def _on_frame(self, bgr_frame):
        self._latest_frame = bgr_frame

    def _on_progress(self, n, total, msg):
        # Schedule GUI update on main thread
        self.after(0, lambda n=n, total=total, msg=msg: self._update_progress(n, total, msg))

    def _on_done(self, success, message):
        self.after(0, lambda: self._finish(success, message))

    # ------------------------------------------------------------------
    # Main-thread GUI updates
    # ------------------------------------------------------------------

    def _poll_frame_queue(self):
        frame = getattr(self, '_latest_frame', None)
        if frame is not None and self._enrolling:
            self._display_frame(frame)
        if self._enrolling:
            self._poll_after_id = self.after(30, self._poll_frame_queue)

    def _display_frame(self, bgr_frame):
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).resize((560, 360), Image.LANCZOS)
        photo = ImageTk.PhotoImage(pil)
        self._video_label.config(image=photo, text='')
        self._video_label.image = photo

    def _update_progress(self, n, total, msg):
        if total > 0:
            self._progress_bar.config(maximum=total)
            self._progress_var.set(n)
            self._progress_label.set(f"{n} / {total} images captured")
        self._status_var.set(msg)

    def _finish(self, success, message):
        self._enrolling = False
        if self._poll_after_id:
            self.after_cancel(self._poll_after_id)
            self._poll_after_id = None

        if success:
            messagebox.showinfo("Enrolment Complete", message, parent=self)
            self._clear_form()
        else:
            messagebox.showerror("Enrolment Failed", message, parent=self)

        self._reset_ui()

    def _reset_ui(self):
        self._enrolling = False
        self._start_btn.config(state='normal')
        self._cancel_btn.config(state='disabled')
        self._status_var.set("Fill in the form and click 'Start Enrolment'.")
        self._progress_var.set(0)
        self._progress_label.set("0 / 0 images captured")
        self._video_label.config(image='',
                                  text="Camera feed will appear here\nwhen enrolment starts")

    def _clear_form(self):
        for var in self._vars.values():
            var.set("")

    def on_show(self):
        pass
