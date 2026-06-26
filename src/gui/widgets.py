"""
Reusable Tkinter widget helpers and themed components.
"""

import tkinter as tk
from tkinter import ttk
from src.config import COLORS, FONTS


def make_button(parent, text, command=None, style='primary', width=None, **kw):
    bg_map = {
        'primary': COLORS['primary'],
        'success': COLORS['success'],
        'danger':  COLORS['danger'],
        'warning': COLORS['warning'],
        'neutral': COLORS['text_secondary'],
    }
    bg = bg_map.get(style, COLORS['primary'])
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg='white',
        font=FONTS['button'],
        relief='flat', cursor='hand2',
        padx=14, pady=7,
        activebackground=COLORS['primary_dark'],
        activeforeground='white',
        **kw,
    )
    if width:
        btn.config(width=width)
    return btn


def make_label(parent, text, style='body', fg=None, **kw):
    font_map = {
        'title':      FONTS['title'],
        'heading':    FONTS['heading'],
        'subheading': FONTS['subheading'],
        'body':       FONTS['body'],
        'small':      FONTS['small'],
    }
    return tk.Label(
        parent, text=text,
        font=font_map.get(style, FONTS['body']),
        fg=fg or COLORS['text_primary'],
        bg=parent.cget('bg'),
        **kw,
    )


def make_entry(parent, textvariable=None, width=30, show=None, **kw):
    e = tk.Entry(
        parent,
        textvariable=textvariable,
        font=FONTS['body'],
        relief='solid', bd=1,
        bg='white', fg=COLORS['text_primary'],
        insertbackground=COLORS['primary'],
        width=width,
        show=show or '',
        **kw,
    )
    return e


def make_separator(parent, orient='horizontal'):
    return ttk.Separator(parent, orient=orient)


class Card(tk.Frame):
    """Raised white card with subtle shadow simulation."""
    def __init__(self, parent, padding=16, **kw):
        super().__init__(parent,
                         bg=COLORS['card_bg'],
                         relief='flat',
                         highlightthickness=1,
                         highlightbackground=COLORS['border'],
                         **kw)
        self._padding = padding

    def body(self):
        f = tk.Frame(self, bg=COLORS['card_bg'])
        f.pack(fill='both', expand=True, padx=self._padding, pady=self._padding)
        return f


class ScrollableTreeview(tk.Frame):
    """Treeview with vertical and horizontal scrollbars."""
    def __init__(self, parent, columns, headings, col_widths=None, **kw):
        super().__init__(parent, bg=COLORS['bg'])

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.Treeview',
                        background=COLORS['card_bg'],
                        foreground=COLORS['text_primary'],
                        fieldbackground=COLORS['card_bg'],
                        rowheight=28,
                        font=FONTS['body'])
        style.configure('Custom.Treeview.Heading',
                        background=COLORS['table_header'],
                        foreground=COLORS['text_primary'],
                        font=FONTS['subheading'],
                        relief='flat')
        style.map('Custom.Treeview',
                  background=[('selected', COLORS['primary'])],
                  foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self, columns=columns, show='headings',
                                 style='Custom.Treeview', **kw)

        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        for col, heading in zip(columns, headings):
            self.tree.heading(col, text=heading, anchor='w')
        if col_widths:
            for col, w in zip(columns, col_widths):
                self.tree.column(col, width=w, minwidth=60)

        # Alternating row tags
        self.tree.tag_configure('odd',  background=COLORS['card_bg'])
        self.tree.tag_configure('even', background=COLORS['table_alt'])

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_rows(self, rows):
        self.clear()
        for i, row in enumerate(rows):
            tag = 'even' if i % 2 == 0 else 'odd'
            self.tree.insert('', 'end', values=row, tags=(tag,))
