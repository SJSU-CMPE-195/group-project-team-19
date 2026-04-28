from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import serial.tools.list_ports

from constants import _DEFAULT_BAUD, _BAUD_OPTIONS


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Waveshare Bus Servo Controller")
        self.resizable(True, True)

        self.v_port = tk.StringVar()
        self.v_baud = tk.StringVar(value=str(_DEFAULT_BAUD))

        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        P = dict(padx=6, pady=3)

        cf = ttk.LabelFrame(self, text="Connection")
        cf.grid(row=0, column=0, sticky="ew", **P)

        ttk.Label(cf, text="Port:").grid(row=0, column=0, sticky="w", **P)
        self.port_cb = ttk.Combobox(cf, textvariable=self.v_port, width=24, state="readonly")
        self.port_cb.grid(row=0, column=1, **P)
        ttk.Button(cf, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, **P)

        ttk.Label(cf, text="Baud:").grid(row=0, column=3, sticky="w", **P)
        ttk.Combobox(cf, textvariable=self.v_baud,
                     values=[str(b) for b in _BAUD_OPTIONS],
                     width=10, state="readonly").grid(row=0, column=4, **P)

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_cb['values'] = ports
        if 'COM11' in ports:
            self.v_port.set('COM11')
        elif ports and not self.v_port.get():
            self.v_port.set(ports[0])