import tkinter as tk
from tkinter import ttk


class _Tooltip:
    """Minimal hover tooltip for any widget."""

    def __init__(self, widget, text: str):
        self._widget = widget
        self._text = text
        self._win = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None):
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._win = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        ttk.Label(tw, text=self._text, background="#ffffe0", relief="solid",
                  borderwidth=1, padding=4).pack()

    def _hide(self, _event=None):
        if self._win:
            self._win.destroy()
            self._win = None