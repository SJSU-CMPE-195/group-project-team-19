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