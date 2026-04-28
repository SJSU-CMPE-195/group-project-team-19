from __future__ import annotations

import tkinter as tk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Waveshare Bus Servo Controller")
        self.resizable(True, True)