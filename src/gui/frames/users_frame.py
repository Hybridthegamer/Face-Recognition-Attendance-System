"""
Users Management Frame — list all enrolled users, search and delete.
"""

import tkinter as tk
from tkinter import messagebox

from src.config import COLORS, FONTS
from src.gui.widgets import make_button, make_entry, ScrollableTreeview


class UsersFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['bg'])
        self.app = app
        self._all_users = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS['header_bg'],
                          highlightthickness=1, highlightbackground=COLORS['border'])
        header.pack(fill='x')
        tk.Label(header, text="User Management",
                 font=FONTS['title'], bg=COLORS['header_bg'], fg=COLORS['text_primary'],
                 padx=24, pady=16).pack(side='left')

        # Search bar
        bar = tk.Frame(self, bg=COLORS['card_bg'],
                       highlightthickness=1, highlightbackground=COLORS['border'])
        bar.pack(fill='x', padx=16, pady=(12, 0))
        inner = tk.Frame(bar, bg=COLORS['card_bg'])
        inner.pack(padx=16, pady=12, fill='x')

        tk.Label(inner, text="Search:", font=FONTS['subheading'],
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(side='left', padx=(0, 8))
        self._search_var = tk.StringVar()
        self._search_var.trace('w', lambda *_: self._filter())
        make_entry(inner, textvariable=self._search_var, width=30).pack(side='left', padx=(0, 16))
        make_button(inner, "Refresh", command=self.on_show,
                    style='neutral').pack(side='left', padx=(0, 8))
        make_button(inner, "Delete Selected", command=self._delete_selected,
                    style='danger').pack(side='left')

        # Table
        table_frame = tk.Frame(self, bg=COLORS['bg'])
        table_frame.pack(fill='both', expand=True, padx=16, pady=12)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self._tree = ScrollableTreeview(
            table_frame,
            columns=('user_id', 'name', 'institution_id', 'department', 'programme', 'created_at'),
            headings=('ID', 'Full Name', 'Institution ID', 'Department', 'Programme', 'Enrolled At'),
            col_widths=(50, 180, 130, 150, 150, 140),
        )
        self._tree.grid(row=0, column=0, sticky='nsew')

        self._count_var = tk.StringVar(value="0 users enrolled")
        tk.Label(self, textvariable=self._count_var,
                 font=FONTS['small'], bg=COLORS['bg'],
                 fg=COLORS['text_secondary']).pack(anchor='w', padx=20, pady=(0, 6))

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _load_users(self):
        self._all_users = self.app.db.get_all_users()
        self._filter()

    def _filter(self):
        q = self._search_var.get().lower()
        filtered = [
            u for u in self._all_users
            if (q in u['name'].lower() or q in u['institution_id'].lower()
                or q in u['department'].lower())
        ] if q else self._all_users

        rows = [
            (u['user_id'], u['name'], u['institution_id'],
             u['department'], u['programme'], u['created_at'])
            for u in filtered
        ]
        self._tree.insert_rows(rows)
        self._count_var.set(f"{len(filtered)} user(s)")

    def _delete_selected(self):
        selected = self._tree.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a user to delete.", parent=self)
            return
        item = self._tree.tree.item(selected[0])
        user_id = item['values'][0]
        name = item['values'][1]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{name}' (ID: {user_id})?\n\n"
            "This will also remove all face encodings and attendance records for this user.",
            parent=self,
        ):
            return
        self.app.db.delete_user(user_id)
        messagebox.showinfo("Deleted", f"User '{name}' has been removed.", parent=self)
        self._load_users()

    def on_show(self):
        self._load_users()
