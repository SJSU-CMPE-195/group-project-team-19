from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ServoPanel(ttk.LabelFrame):
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ServoPanel(ttk.LabelFrame):
    """Self-contained UI panel for a single servo on the shared bus."""

    def __init__(self, parent, app, default_label: str):
        super().__init__(parent, text=default_label)
        self.app = app

        self.v_label = tk.StringVar(value=default_label)
        self.v_id = tk.IntVar(value=0)

        self._build()
        self.v_label.trace_add('write', self._on_label_change)
        self.v_id.trace_add('write', self._on_id_change)

    def _build(self):
        P = dict(padx=6, pady=3)

        hdr = ttk.Frame(self)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", **P)

        ttk.Label(hdr, text="Label:").pack(side="left")
        ttk.Entry(hdr, textvariable=self.v_label, width=8).pack(side="left", padx=(2, 8))

        ttk.Label(hdr, text="ID:").pack(side="left")
        ttk.Spinbox(hdr, from_=0, to=253, textvariable=self.v_id,
                    width=5).pack(side="left", padx=(2, 8))

        ttk.Button(hdr, text="Rescan bus",
                   command=lambda: self.app._auto_detect()).pack(side="left")

    def _update_title(self):
        try:
            sid = self.v_id.get()
        except tk.TclError:
            return
        label = self.v_label.get() or "?"
        self.config(text=f"{label}  (ID {sid})" if sid else f"{label}  —  not connected")

    def _on_label_change(self, *_):
        self._update_title()

    def _on_id_change(self, *_):
        self._update_title()
    def __init__(self, parent, app, default_label: str):
        super().__init__(parent, text=default_label)
        self.app = app

        self.v_label = tk.StringVar(value=default_label)
        self.v_id = tk.IntVar(value=0)

        self._build()
        self.v_label.trace_add('write', self._on_label_change)
        self.v_id.trace_add('write', self._on_id_change)

    def _build(self):
        P = dict(padx=6, pady=3)

        hdr = ttk.Frame(self)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", **P)

        ttk.Label(hdr, text="Label:").pack(side="left")
        ttk.Entry(hdr, textvariable=self.v_label, width=8).pack(side="left", padx=(2, 8))

        ttk.Label(hdr, text="ID:").pack(side="left")
        ttk.Spinbox(hdr, from_=0, to=253, textvariable=self.v_id,
                    width=5).pack(side="left", padx=(2, 8))

        ttk.Button(hdr, text="Rescan bus",
                   command=lambda: self.app._auto_detect()).pack(side="left")

    def _update_title(self):
        try:
            sid = self.v_id.get()
        except tk.TclError:
            return
        label = self.v_label.get() or "?"
        self.config(text=f"{label}  (ID {sid})" if sid else f"{label}  —  not connected")

    def _on_label_change(self, *_):
        self._update_title()

    def _on_id_change(self, *_):
        self._update_title()