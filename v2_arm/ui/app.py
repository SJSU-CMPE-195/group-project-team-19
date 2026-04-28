from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

import serial.tools.list_ports

from constants import (
    _DEFAULT_BAUD,
    _BAUD_OPTIONS,
    _DEFAULT_LABELS,
    _GRID_COLS,
    _GRID_ROWS,
)
from protocol import ServoPort
from servo_panel import ServoPanel


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Waveshare Bus Servo Controller")
        self.resizable(True, True)

        self._port: ServoPort | None = None

        self.v_port   = tk.StringVar()
        self.v_baud   = tk.StringVar(value=str(_DEFAULT_BAUD))
        self.v_status = tk.StringVar(value="Not connected.")

        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        P = dict(padx=6, pady=3)

        cf = ttk.LabelFrame(self, text="Connection")
        cf.grid(row=0, column=0, columnspan=_GRID_COLS, sticky="ew", **P)

        ttk.Label(cf, text="Port:").grid(row=0, column=0, sticky="w", **P)
        self.port_cb = ttk.Combobox(cf, textvariable=self.v_port, width=24, state="readonly")
        self.port_cb.grid(row=0, column=1, **P)
        ttk.Button(cf, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, **P)

        ttk.Label(cf, text="Baud:").grid(row=0, column=3, sticky="w", **P)
        ttk.Combobox(cf, textvariable=self.v_baud,
                     values=[str(b) for b in _BAUD_OPTIONS],
                     width=10, state="readonly").grid(row=0, column=4, **P)

        self.btn_connect = ttk.Button(cf, text="Connect", command=self._toggle_connect)
        self.btn_connect.grid(row=0, column=5, **P)

        self.btn_detect = ttk.Button(cf, text="Auto-detect", command=self._auto_detect,
                                     state="disabled")
        self.btn_detect.grid(row=0, column=6, **P)

        self.panels = [
            ServoPanel(self, self, label) for label in _DEFAULT_LABELS
        ]
        for idx, panel in enumerate(self.panels):
            row = 1 + (idx // _GRID_COLS)
            col = idx % _GRID_COLS
            panel.grid(row=row, column=col, sticky="nsew", **P)

        for r in range(1, 1 + _GRID_ROWS):
            self.grid_rowconfigure(r, weight=1)
        for c in range(_GRID_COLS):
            self.grid_columnconfigure(c, weight=2)

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_cb['values'] = ports
        if 'COM11' in ports:
            self.v_port.set('COM11')
        elif ports and not self.v_port.get():
            self.v_port.set(ports[0])

    def _toggle_connect(self):
        if self._port is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self):
        port = self.v_port.get()
        if not port:
            self._status("Select a port first.")
            return
        baud = int(self.v_baud.get())
        try:
            self._port = ServoPort(port, baud)
        except Exception as exc:
            self._status(f"Could not open {port}: {exc}")
            self._port = None
            return
        self.btn_connect.config(text="Disconnect")
        self.btn_detect.config(state="normal")
        self._status(f"Connected  {port}  @  {baud:,} baud.")

    def _disconnect(self):
        if self._port:
            self._port.close()
            self._port = None
        self.btn_connect.config(text="Connect")
        self.btn_detect.config(state="disabled")
        for panel in self.panels:
            panel.clear()
        self._status("Disconnected.")

    def _auto_detect(self):
        self._status("Scanning IDs 1–20 …")
        self.btn_detect.config(state="disabled")
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_worker(self):
        found = []
        for sid in range(1, 21):
            if self._port is None:
                break
            try:
                if self._port.ping(sid) is not None:
                    found.append(sid)
            except Exception:
                pass
        self.after(0, self._detect_done, found)

    def _detect_done(self, found: list[int]):
        self.btn_detect.config(state="normal")
        if not found:
            self._status("No servos found on IDs 1–20. Check wiring and power.")
            return

        if len(found) == 1:
            sid = found[0]
            for panel in self.panels:
                if panel.v_id.get() == 0:
                    panel.set_servo(sid)
                    break
            self._status(f"Found 1 servo at ID {sid}. Assign label manually if needed.")
            return

        sorted_ids = sorted(found)
        assigned = []
        id_iter = iter(sorted_ids)
        for panel, default_label in zip(self.panels, _DEFAULT_LABELS):
            if panel.v_id.get() != 0:
                continue
            try:
                sid = next(id_iter)
            except StopIteration:
                break
            panel.set_servo(sid, default_label)
            assigned.append(f"{default_label}→ID {sid}")

        if assigned:
            self._status(
                f"Found IDs {sorted_ids}. Auto-assigned: {', '.join(assigned)}."
            )
        else:
            self._status(
                f"Found IDs {sorted_ids} — all panels already assigned, no changes."
            )

    def _status(self, msg: str):
        self.v_status.set(msg)