from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ServoPanel(ttk.LabelFrame):
    """UI panel for a single servo on the shared bus."""

    def __init__(self, parent, app, default_label: str):
        super().__init__(parent, text=default_label)
        self.app = app

        self.v_label = tk.StringVar(value=default_label)

        self._build()

    def _build(self):
        pass