from __future__ import annotations

import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from constants import (
    _TORQUE_LIMIT_L_REG,
    _TORQUE_HARD_CEILING_KGCM,
    _SERVO_RATED_KGCM,
    _DEFAULT_TORQUE_KGCM,
    _DEFAULT_TORQUE_FALLBACK_KGCM,
    _DEFAULT_MAX_LOAD_PCT,
    _DEFAULT_MAX_CURRENT_MA,
    _DEFAULT_MAX_TEMP_C,
)
from protocol import ServoPort
from servo_panel import ServoPanel
from widgets import _Tooltip


@dataclass
class SafetyLimit:
    enabled: tk.BooleanVar
    max_torque_kgcm: tk.DoubleVar
    max_load_pct: tk.DoubleVar
    max_current_ma: tk.IntVar
    max_temp_c: tk.IntVar
    faulted: bool = False
    fault_message: str = ""
class SafetyPanel(ttk.LabelFrame):
    """Per-servo safety limits driven by the existing telemetry poll."""

    _OK_BG       = "#ffffff"
    _FAULT_BG    = "#ffd6d6"
    _DISABLED_BG = "#f2f2f2"

    def __init__(self, parent, app: App):
        super().__init__(parent, text="Safety / Torque Limiters")
        self.app = app
        self._limits: dict[ServoPanel, SafetyLimit] = {}
        self._rows: dict[ServoPanel, dict] = {}
        # Suppress trace_add re-entrancy when we programmatically clamp values.
        self._suppress_clamp: dict[ServoPanel, bool] = {}
        self._flash_on = False
        self._flash_after_id = None
        self.v_status = tk.StringVar(value="No faults.")

        self._build()
        self.refresh_servos()

    def _build(self):
        buttons = ttk.Frame(self)
        buttons.grid(row=0, column=0, sticky="ew", padx=4, pady=(1, 1))

        ttk.Button(buttons, text="Enable All Limits",
                   command=self.enable_all).pack(side="left", padx=2)
        ttk.Button(buttons, text="Disable All Limits",
                   command=self.disable_all).pack(side="left", padx=2)
        ttk.Button(buttons, text="Reset to Defaults",
                   command=self.reset_defaults).pack(side="left", padx=2)
        ttk.Button(buttons, text="Apply All Torque Limits",
                   command=self.apply_all_torque_limits).pack(side="left", padx=2)
        ttk.Button(buttons, text="Clear Faults",
                   command=self.clear_faults).pack(side="left", padx=2)

        ttk.Label(buttons, textvariable=self.v_status, anchor="w",
                  relief="sunken").pack(side="left", fill="x", expand=True, padx=(8, 0))
        table = tk.Frame(self, background="#d9d9d9")
        table.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 3))
        self._table = table

        headers = [
            ("Servo", 12),
            ("ID", 4),
            ("Enabled", 7),
            ("Max Torque (kg-cm)", 16),
            ("Max Load %", 8),
            ("Current mA", 10),
            ("Temp C", 8),
            ("Status", 30),
            ("", 7),  # Apply button column
        ]
        for col, (text, width) in enumerate(headers):
            anchor = "w" if col in (0, 7) else "center"
            lbl = tk.Label(table, text=text, width=width, anchor=anchor,
                           background="#e6e6e6", font=("Segoe UI", 9, "bold"),
                           padx=3, pady=0)
            lbl.grid(row=0, column=col, sticky="ew", padx=1, pady=0)
            table.grid_columnconfigure(col, weight=1 if col == 7 else 0)
            if text == "Max Torque (kg-cm)":
                _Tooltip(
                    lbl,
                    "Rated 50 kg-cm. Hard ceiling 45. Written to register 48 "
                    "(Torque Limit, RAM) on Apply. RAM resets on power-cycle, "
                    "so Apply must be re-run after reconnect."
                )
        for idx, panel in enumerate(self.app.panels, start=1):
            default_kgcm = _DEFAULT_TORQUE_KGCM.get(
                panel.v_label.get(), _DEFAULT_TORQUE_FALLBACK_KGCM
            )
            limit = SafetyLimit(
                enabled=tk.BooleanVar(value=False),
                max_torque_kgcm=tk.DoubleVar(value=default_kgcm),
                max_load_pct=tk.DoubleVar(value=_DEFAULT_MAX_LOAD_PCT),
                max_current_ma=tk.IntVar(value=_DEFAULT_MAX_CURRENT_MA),
                max_temp_c=tk.IntVar(value=_DEFAULT_MAX_TEMP_C),
            )
            self._limits[panel] = limit
            self._suppress_clamp[panel] = False

            limit.max_torque_kgcm.trace_add(
                'write', lambda *_, p=panel: self._on_torque_var_change(p)
            )

            name   = tk.StringVar(value="")
            sid    = tk.StringVar(value="")
            status = tk.StringVar(value="No servo connected.")

            apply_btn = tk.Button(
                table, text="Apply", width=7, padx=2, pady=0,
                command=lambda p=panel: self._apply_torque_limit_clicked(p),
                state="disabled",
            )

            widgets = [
                tk.Label(table, textvariable=name, width=12, anchor="w", padx=3, pady=0),
                tk.Label(table, textvariable=sid, width=4, anchor="center", padx=2, pady=0),
                tk.Checkbutton(table, variable=limit.enabled, width=7,
                               command=lambda p=panel: self._on_toggle(p)),
                tk.Entry(table, textvariable=limit.max_torque_kgcm, width=16, justify="center"),
                tk.Entry(table, textvariable=limit.max_load_pct, width=8, justify="center"),
                tk.Entry(table, textvariable=limit.max_current_ma, width=10, justify="center"),
                tk.Entry(table, textvariable=limit.max_temp_c, width=8, justify="center"),
                tk.Label(table, textvariable=status, width=30, anchor="w", padx=3, pady=0),
                apply_btn,
            ]
            for col, widget in enumerate(widgets):
                if col == 7:
                    sticky = "ew"
                elif col == 0:
                    sticky = "w"
                else:
                    sticky = ""
                widget.grid(row=idx, column=col, sticky=sticky, padx=1, pady=0)

            self._rows[panel] = {
                'name': name,
                'sid': sid,
                'status': status,
                'widgets': widgets,
                'inputs': widgets[2:7],
                'apply_btn': apply_btn,
            }

        self.grid_columnconfigure(0, weight=1)