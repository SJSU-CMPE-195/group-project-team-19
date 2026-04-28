from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from constants import _COUNT_PER_DEG, _DEG_PER_COUNT


class ServoPanel(ttk.LabelFrame):
    """Self-contained UI panel for a single servo on the shared bus."""

    def __init__(self, parent, app, default_label: str):
        super().__init__(parent, text=default_label)
        self.app = app

        self.v_label = tk.StringVar(value=default_label)
        self.v_id = tk.IntVar(value=0)
        self.v_series = tk.StringVar(value="—")
        self.v_tele = {
            'angle_deg':     tk.StringVar(value='—'),
            'pos_counts':    tk.StringVar(value='—'),
            'speed':         tk.StringVar(value='—'),
            'load_pct':      tk.StringVar(value='—'),
            'voltage_v':     tk.StringVar(value='—'),
            'temperature_c': tk.StringVar(value='—'),
            'current_ma':    tk.StringVar(value='—'),
        }
        self._last_data: dict | None = None
        self._zero_counts = 2048

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

        tf = ttk.LabelFrame(self, text="Telemetry")
        tf.grid(row=1, column=0, sticky="nsew", **P)

        for i, (label, key) in enumerate([
            ("Angle (°)",    'angle_deg'),
            ("Raw counts",   'pos_counts'),
            ("Speed",        'speed'),
            ("Load (%)",     'load_pct'),
            ("Voltage (V)",  'voltage_v'),
            ("Temp (°C)",    'temperature_c'),
            ("Current (mA)", 'current_ma'),
        ]):
            ttk.Label(tf, text=label).grid(row=i, column=0, sticky="w", **P)
            ttk.Label(tf, textvariable=self.v_tele[key], width=10,
                      anchor="e", relief="sunken").grid(row=i, column=1, **P)

        ttk.Label(tf, text="Series").grid(row=7, column=0, sticky="w", **P)
        ttk.Label(tf, textvariable=self.v_series, width=10,
                  anchor="e", relief="sunken").grid(row=7, column=1, **P)

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

    def clear(self):
        for v in self.v_tele.values():
            v.set("—")
        self.v_series.set("—")
        self._last_data = None
        self._zero_counts = 2048

    def update_telemetry(self, data):
        if data is None:
            self._last_data = None
            for v in self.v_tele.values():
                v.set("?")
            return
        self._last_data = data
        angle = self._counts_to_deg(data['pos_counts'])
        self.v_tele['angle_deg'].set(f"{angle:.2f}")
        self.v_tele['pos_counts'].set(str(data['pos_counts']))
        self.v_tele['speed'].set(str(data['speed']))
        self.v_tele['load_pct'].set(f"{data['load_pct']:.1f}")
        self.v_tele['voltage_v'].set(f"{data['voltage_v']:.1f}")
        self.v_tele['temperature_c'].set(str(data['temperature_c']))
        self.v_tele['current_ma'].set(str(data['current_ma']))

    def _counts_to_deg(self, counts: int) -> float:
        return (counts - self._zero_counts) * _DEG_PER_COUNT

    def _deg_to_counts(self, deg: float) -> int:
        return self._zero_counts + int(round(deg * _COUNT_PER_DEG))

    def current_angle(self) -> float:
        try:
            return float(self.v_tele['angle_deg'].get())
        except (ValueError, TypeError):
            return 0.0