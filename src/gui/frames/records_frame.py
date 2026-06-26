"""
Records Frame — searchable, filterable view of all attendance records.
Corresponds to FR8 (searchable records) and FR9 (filterable by course/date).
"""

import tkinter as tk
from tkinter import messagebox
import csv
import os
from datetime import datetime

from src.config import COLORS, FONTS, REPORTS_DIR
from src.gui.widgets import make_button, make_entry, ScrollableTreeview


class RecordsFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['bg'])
        self.app = app
        self._all_records = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS['header_bg'],
                          highlightthickness=1, highlightbackground=COLORS['border'])
        header.pack(fill='x')
        tk.Label(header, text="Attendance Records",
                 font=FONTS['title'], bg=COLORS['header_bg'], fg=COLORS['text_primary'],
                 padx=24, pady=16).pack(side='left')

        # Filter bar
        filter_bar = tk.Frame(self, bg=COLORS['card_bg'],
                              highlightthickness=1, highlightbackground=COLORS['border'])
        filter_bar.pack(fill='x', padx=16, pady=(12, 0))

        inner = tk.Frame(filter_bar, bg=COLORS['card_bg'])
        inner.pack(padx=16, pady=12, fill='x')

        tk.Label(inner, text="Filter Records", font=FONTS['subheading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_primary']).grid(
                     row=0, column=0, columnspan=8, sticky='w', pady=(0, 8))

        labels_vars = [
            ("Session ID",    '_filt_session'),
            ("Course Code",   '_filt_course'),
            ("Date From",     '_filt_from'),
            ("Date To",       '_filt_to'),
            ("Name Search",   '_filt_name'),
        ]
        for col, (label, attr) in enumerate(labels_vars):
            tk.Label(inner, text=label, font=FONTS['small'],
                     bg=COLORS['card_bg'], fg=COLORS['text_secondary']).grid(
                         row=1, column=col*2, padx=(12, 2) if col else (0, 2), sticky='w')
            var = tk.StringVar()
            setattr(self, attr, var)
            make_entry(inner, textvariable=var, width=14).grid(row=1, column=col*2+1, padx=(0, 12))

        make_button(inner, "Search", command=self._load_records,
                    style='primary').grid(row=1, column=10, padx=(8, 0))
        make_button(inner, "Clear", command=self._clear_filters,
                    style='neutral').grid(row=1, column=11, padx=(4, 0))
        make_button(inner, "Export CSV", command=self._export_csv,
                    style='success').grid(row=1, column=12, padx=(12, 0))

        # Table
        table_frame = tk.Frame(self, bg=COLORS['bg'])
        table_frame.pack(fill='both', expand=True, padx=16, pady=12)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self._tree = ScrollableTreeview(
            table_frame,
            columns=('name', 'id', 'dept', 'course_code', 'course_title', 'date', 'time'),
            headings=('Name', 'Institution ID', 'Department',
                      'Course Code', 'Course Title', 'Date', 'Time'),
            col_widths=(160, 120, 130, 110, 180, 100, 90),
        )
        self._tree.grid(row=0, column=0, sticky='nsew')

        # Footer count
        self._count_var = tk.StringVar(value="0 records")
        tk.Label(self, textvariable=self._count_var,
                 font=FONTS['small'], bg=COLORS['bg'],
                 fg=COLORS['text_secondary']).pack(anchor='w', padx=20, pady=(0, 6))

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _load_records(self):
        sess_id = self._filt_session.get().strip() or None
        course  = self._filt_course.get().strip().upper() or None
        d_from  = self._filt_from.get().strip() or None
        d_to    = self._filt_to.get().strip() or None
        name_q  = self._filt_name.get().strip().lower()

        if sess_id:
            try:
                sess_id = int(sess_id)
            except ValueError:
                sess_id = None

        records = self.app.db.get_attendance_records(
            session_id=sess_id, date_from=d_from, date_to=d_to
        )

        if course:
            records = [r for r in records if r['course_code'] == course]
        if name_q:
            records = [r for r in records if name_q in r['name'].lower()]

        self._all_records = records
        rows = [
            (
                r['name'], r['institution_id'], r['department'],
                r['course_code'], r['course_title'],
                r['date'], r['timestamp'].split(' ')[-1],
            )
            for r in records
        ]
        self._tree.insert_rows(rows)
        self._count_var.set(f"{len(rows)} record(s) found")

    def _clear_filters(self):
        for attr in ('_filt_session', '_filt_course', '_filt_from',
                     '_filt_to', '_filt_name'):
            getattr(self, attr).set("")
        self._load_records()

    def _export_csv(self):
        if not self._all_records:
            messagebox.showinfo("No Data", "No records to export.", parent=self)
            return
        os.makedirs(REPORTS_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(REPORTS_DIR, f"attendance_records_{ts}.csv")
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Institution ID', 'Department',
                             'Course Code', 'Course Title', 'Date', 'Timestamp'])
            for r in self._all_records:
                writer.writerow([
                    r['name'], r['institution_id'], r['department'],
                    r['course_code'], r['course_title'], r['date'], r['timestamp'],
                ])
        messagebox.showinfo("Exported", f"Records exported to:\n{path}", parent=self)

    def on_show(self):
        self._load_records()
