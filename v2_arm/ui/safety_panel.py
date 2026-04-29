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