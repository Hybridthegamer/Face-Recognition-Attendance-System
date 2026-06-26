"""
Report Frame — implements GenerateReport output (Chapter 3, Section 3.8.3).

Displays per-student attendance statistics with Pass/Fail indicators (FR9, FR10).
Provides CSV export (Section 3.6.2 — Attendance Summary Report).
"""

import tkinter as tk
from tkinter import messagebox, ttk

from src.config import COLORS, FONTS, DEFAULT_THRESHOLD_PCT
from src.gui.widgets import make_button, make_entry, ScrollableTreeview
from src.attendance.report_generator import ReportGenerator


class ReportFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['bg'])
        self.app = app
        self._report_gen = ReportGenerator(app.db)
        self._last_course = None
        self._last_threshold = DEFAULT_THRESHOLD_PCT
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS['header_bg'],
                          highlightthickness=1, highlightbackground=COLORS['border'])
        header.pack(fill='x')
        tk.Label(header, text="Attendance Reports",
                 font=FONTS['title'], bg=COLORS['header_bg'], fg=COLORS['text_primary'],
                 padx=24, pady=16).pack(side='left')

        # Controls
        ctrl = tk.Frame(self, bg=COLORS['card_bg'],
                        highlightthickness=1, highlightbackground=COLORS['border'])
        ctrl.pack(fill='x', padx=16, pady=(12, 0))
        inner = tk.Frame(ctrl, bg=COLORS['card_bg'])
        inner.pack(padx=16, pady=14, fill='x')

        tk.Label(inner, text="Course Code", font=FONTS['subheading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary']).grid(row=0, column=0, padx=(0, 4))
        self._course_var = tk.StringVar()
        make_entry(inner, textvariable=self._course_var, width=16).grid(row=0, column=1, padx=(0, 20))

        # Course dropdown (populated from DB)
        tk.Label(inner, text="Or pick course:", font=FONTS['small'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary']).grid(row=0, column=2, padx=(0, 4))
        self._course_combo = ttk.Combobox(inner, width=22, state='readonly', font=FONTS['body'])
        self._course_combo.grid(row=0, column=3, padx=(0, 20))
        self._course_combo.bind('<<ComboboxSelected>>', self._on_combo_select)

        tk.Label(inner, text="Threshold %", font=FONTS['subheading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary']).grid(row=0, column=4, padx=(0, 4))
        self._threshold_var = tk.StringVar(value=str(DEFAULT_THRESHOLD_PCT))
        make_entry(inner, textvariable=self._threshold_var, width=6).grid(row=0, column=5, padx=(0, 20))

        make_button(inner, "Generate Report", command=self._generate,
                    style='primary').grid(row=0, column=6, padx=(0, 8))
        make_button(inner, "Export CSV", command=self._export,
                    style='success').grid(row=0, column=7)

        # Summary cards row
        summary_row = tk.Frame(self, bg=COLORS['bg'])
        summary_row.pack(fill='x', padx=16, pady=12)
        for i in range(4):
            summary_row.columnconfigure(i, weight=1)

        self._summary_vars = {}
        summary_defs = [
            ('total_sessions', 'Total Sessions',    COLORS['primary']),
            ('total_students', 'Students Tracked',  COLORS['text_secondary']),
            ('pass_count',     'Pass (≥ threshold)', COLORS['success']),
            ('fail_count',     'Fail (< threshold)', COLORS['danger']),
        ]
        for col, (key, label, color) in enumerate(summary_defs):
            f = tk.Frame(summary_row, bg=COLORS['card_bg'],
                         highlightthickness=1, highlightbackground=COLORS['border'])
            f.grid(row=0, column=col, padx=6, sticky='ew')
            var = tk.StringVar(value="—")
            self._summary_vars[key] = var
            tk.Label(f, textvariable=var, font=('Helvetica', 22, 'bold'),
                     bg=COLORS['card_bg'], fg=color).pack(padx=16, pady=(12, 4))
            tk.Label(f, text=label, font=FONTS['small'],
                     bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(padx=16, pady=(0, 12))

        # Table
        table_frame = tk.Frame(self, bg=COLORS['bg'])
        table_frame.pack(fill='both', expand=True, padx=16, pady=(0, 10))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure('Pass.Treeview', foreground=COLORS['success'])

        self._tree = ScrollableTreeview(
            table_frame,
            columns=('name', 'id', 'dept', 'prog', 'attended', 'total', 'pct', 'status'),
            headings=('Name', 'Institution ID', 'Department', 'Programme',
                      'Attended', 'Total Sessions', 'Percentage', 'Status'),
            col_widths=(160, 120, 130, 130, 80, 120, 90, 70),
        )
        self._tree.grid(row=0, column=0, sticky='nsew')

        # Status bar
        self._status_var = tk.StringVar(value="Enter a course code and click Generate Report.")
        tk.Label(self, textvariable=self._status_var,
                 font=FONTS['small'], bg=COLORS['bg'],
                 fg=COLORS['text_secondary']).pack(anchor='w', padx=20, pady=(0, 4))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_combo_select(self, _event):
        val = self._course_combo.get().split(' — ')[0].strip()
        self._course_var.set(val)

    def _generate(self):
        course = self._course_var.get().strip().upper()
        if not course:
            messagebox.showwarning("No Course", "Please enter a course code.", parent=self)
            return
        try:
            threshold = float(self._threshold_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Threshold",
                                   "Threshold must be a number (e.g. 75).", parent=self)
            return

        self._last_course = course
        self._last_threshold = threshold

        rows, total = self._report_gen.generate(course, threshold)

        if total == 0:
            messagebox.showinfo("No Data",
                                f"No sessions found for course '{course}'.", parent=self)
            return

        pass_count = sum(1 for r in rows if r['status'] == 'PASS')
        fail_count = len(rows) - pass_count

        self._summary_vars['total_sessions'].set(str(total))
        self._summary_vars['total_students'].set(str(len(rows)))
        self._summary_vars['pass_count'].set(str(pass_count))
        self._summary_vars['fail_count'].set(str(fail_count))

        table_rows = []
        for r in rows:
            pct_str = f"{r['percentage']:.1f}%"
            status = r['status']
            table_rows.append((
                r['name'], r['institution_id'], r['department'], r['programme'],
                r['attended'], r['total_sessions'], pct_str, status,
            ))

        # Re-insert with colour coding
        self._tree.clear()
        for i, row_data in enumerate(table_rows):
            tag = 'fail_row' if row_data[-1] == 'FAIL' else ('even' if i % 2 == 0 else 'odd')
            self._tree.tree.insert('', 'end', values=row_data, tags=(tag,))

        self._tree.tree.tag_configure('fail_row', foreground=COLORS['danger'])
        self._status_var.set(
            f"Report for {course} | {total} sessions | "
            f"{len(rows)} students | threshold {threshold}%"
        )

    def _export(self):
        course = self._last_course or self._course_var.get().strip().upper()
        if not course:
            messagebox.showwarning("No Course",
                                   "Generate a report first before exporting.", parent=self)
            return
        try:
            threshold = float(self._threshold_var.get())
        except ValueError:
            threshold = DEFAULT_THRESHOLD_PCT

        path = self._report_gen.export_csv(course, threshold)
        messagebox.showinfo("Exported", f"Report exported to:\n{path}", parent=self)

    def on_show(self):
        courses = self.app.db.get_distinct_courses()
        values = [f"{c['course_code']} — {c['course_title']}" for c in courses]
        self._course_combo['values'] = values
