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

      # ── Public actions ────────────────────────────────────────────────────

    def refresh_servos(self):
        for panel, limit in self._limits.items():
            row = self._rows[panel]
            sid = self._safe_int(panel.v_id)
            row['name'].set(panel.v_label.get() or "Servo")
            row['sid'].set(str(sid) if sid else "-")
            connected = self.app._port is not None and sid > 0

            if not connected:
                row['status'].set("Not connected." if sid else "Not assigned.")
                self._set_row_bg(panel, self._DISABLED_BG)
            elif limit.faulted:
                row['status'].set(limit.fault_message)
                self._set_row_bg(panel, self._FAULT_BG)
            else:
                row['status'].set("Monitoring." if limit.enabled.get() else "Limits disabled.")
                self._set_row_bg(panel, self._OK_BG)

            state = "normal" if sid > 0 else "disabled"
            for widget in row['inputs']:
                widget.config(state=state)
            row['apply_btn'].config(state="normal" if connected else "disabled")

        self._refresh_fault_indicator()

    def monitor(self):
        """Called from App._tele_done after panels receive their latest telemetry."""
        if self.app._port is None:
            self.refresh_servos()
            return

        for panel, limit in self._limits.items():
            sid = self._safe_int(panel.v_id)
            if sid <= 0 or not limit.enabled.get() or limit.faulted:
                continue

            data = panel._last_data
            if not data:
                continue

            fault = self._find_fault(panel, limit, data)
            if fault:
                self._trip_fault(panel, sid, fault)

        self.refresh_servos()

    def enable_all(self):
        for panel, limit in self._limits.items():
            if self._safe_int(panel.v_id) > 0:
                limit.enabled.set(True)
        self.refresh_servos()
        self.app._status("Safety: all assigned servo limits enabled.")

    def disable_all(self):
        for limit in self._limits.values():
            limit.enabled.set(False)
        self.refresh_servos()
        self.app._status("Safety: all limits disabled.")

    def reset_defaults(self):
        for panel, limit in self._limits.items():
            default_kgcm = _DEFAULT_TORQUE_KGCM.get(
                panel.v_label.get(), _DEFAULT_TORQUE_FALLBACK_KGCM
            )
            self._suppress_clamp[panel] = True
            try:
                limit.max_torque_kgcm.set(default_kgcm)
            finally:
                self._suppress_clamp[panel] = False
            limit.max_load_pct.set(_DEFAULT_MAX_LOAD_PCT)
            limit.max_current_ma.set(_DEFAULT_MAX_CURRENT_MA)
            limit.max_temp_c.set(_DEFAULT_MAX_TEMP_C)
            limit.enabled.set(False)
            limit.faulted = False
            limit.fault_message = ""
        self.refresh_servos()
        self.app._status("Safety: limits reset to per-joint defaults.")

    def apply_all_torque_limits(self):
        """Write every assigned servo's torque limit to register 48 sequentially."""
        port = self.app._port
        if port is None:
            self.app._status("Safety: connect to the bus before applying torque limits.")
            return
        targets = []
        for panel, limit in self._limits.items():
            sid = self._safe_int(panel.v_id)
            if sid <= 0:
                continue
            try:
                kgcm = float(limit.max_torque_kgcm.get())
            except (ValueError, tk.TclError):
                continue
            kgcm = max(0.0, min(kgcm, _TORQUE_HARD_CEILING_KGCM))
            raw = self._kgcm_to_raw(kgcm)
            targets.append((panel, sid, kgcm, raw))
        if not targets:
            self.app._status("Safety: no assigned servos to apply torque limits to.")
            return
        for row in self._rows.values():
            row['apply_btn'].config(state="disabled")
        threading.Thread(
            target=self._apply_all_worker, args=(port, targets), daemon=True
        ).start()
    def clear_faults(self):
        port = self.app._port
        to_enable = []
        for panel, limit in self._limits.items():
            if not limit.faulted:
                continue
            sid = self._safe_int(panel.v_id)
            limit.faulted = False
            limit.fault_message = ""
            if port is not None and sid > 0:
                to_enable.append((panel, sid))

        self.refresh_servos()
        if to_enable and port is not None:
            threading.Thread(
                target=self._reenable_torque_worker, args=(port, to_enable), daemon=True
            ).start()
            self.app._status("Safety: faults cleared; torque re-enable requested.")
        else:
            self.app._status("Safety: faults cleared.")

    def on_connection_changed(self):
        if self.app._port is None:
            for limit in self._limits.values():
                limit.faulted = False
                limit.fault_message = ""
        self.refresh_servos()

    # ── Fault detection ──────────────────────────────────────────────────

    def _find_fault(self, panel: ServoPanel, limit: SafetyLimit, data: dict) -> str | None:
        label = panel.v_label.get() or f"ID {panel.v_id.get()}"
        try:
            user_max_load  = float(limit.max_load_pct.get())
            max_current    = int(limit.max_current_ma.get())
            max_temp       = int(limit.max_temp_c.get())
            max_torque_kgcm = float(limit.max_torque_kgcm.get())
        except (ValueError, tk.TclError):
            return f"{label} invalid safety limit - torque disabled"

        load    = float(data.get('load_pct', 0.0))
        current = int(data.get('current_ma', 0))
        temp    = int(data.get('temperature_c', 0))

        torque_load_cap  = (max_torque_kgcm / _SERVO_RATED_KGCM) * 100.0
        effective_max_load = min(user_max_load, torque_load_cap)

        if load > effective_max_load:
            if torque_load_cap < user_max_load:
                return (
                    f"{label} overload ({load:.1f}% > {effective_max_load:.1f}%) "
                    f"- exceeded torque cap of {max_torque_kgcm:.1f} kg-cm "
                    f"- torque disabled"
                )
            return (
                f"{label} overload ({load:.1f}% > {user_max_load:.1f}%) "
                f"- torque disabled"
            )
        if current > max_current:
            return f"{label} overcurrent ({current}mA > {max_current}mA) - torque disabled"
        if temp > max_temp:
            return f"{label} overtemp ({temp}C > {max_temp}C) - torque disabled"
        return None

    def _trip_fault(self, panel: ServoPanel, sid: int, message: str):
        limit = self._limits[panel]
        limit.faulted = True
        limit.fault_message = message
        panel._torque_on = False
        if panel.btn_torque:
            panel.btn_torque.config(text="Torque ON")
        self.v_status.set(message)
        self.app._status(f"Safety: {message}")

        port = self.app._port
        if port is not None:
            threading.Thread(
                target=self._disable_torque_worker, args=(port, sid), daemon=True
            ).start()
        
        # ── Worker threads ───────────────────────────────────────────────────

    def _disable_torque_worker(self, port: ServoPort, sid: int):
        try:
            port.set_torque(sid, False)
        except Exception as exc:
            print(f"[DBG safety] set_torque(False) failed for ID {sid}: {exc}", flush=True)

    def _reenable_torque_worker(self, port: ServoPort, servos: list[tuple[ServoPanel, int]]):
        for panel, sid in servos:
            try:
                port.set_torque(sid, True)
                panel.after(0, self._torque_reenabled, panel)
            except Exception as exc:
                print(f"[DBG safety] set_torque(True) failed for ID {sid}: {exc}", flush=True)

    def _torque_reenabled(self, panel: ServoPanel):
        panel._torque_on = True
        if panel.btn_torque:
            panel.btn_torque.config(text="Torque OFF")

    # ── Torque-limit Apply (per row) ─────────────────────────────────────

    def _apply_torque_limit_clicked(self, panel: ServoPanel):
        """Per-row Apply: write this servo's torque limit to register 48."""
        port = self.app._port
        if port is None:
            self.app._status("Safety: connect to the bus before applying torque limits.")
            return
        sid = self._safe_int(panel.v_id)
        if sid <= 0:
            self.app._status(
                f"Safety: {panel.v_label.get() or 'panel'} has no servo assigned."
            )
            return
        limit = self._limits[panel]
        try:
            kgcm = float(limit.max_torque_kgcm.get())
        except (ValueError, tk.TclError):
            self.app._status(
                f"Safety: {panel.v_label.get()} torque value invalid — fix and retry."
            )
            return
        kgcm = max(0.0, min(kgcm, _TORQUE_HARD_CEILING_KGCM))
        raw = self._kgcm_to_raw(kgcm)
        self._rows[panel]['apply_btn'].config(state="disabled")
        threading.Thread(
            target=self._apply_torque_worker,
            args=(port, panel, sid, kgcm, raw),
            daemon=True,
        ).start()

    def _apply_torque_worker(self, port: ServoPort, panel: ServoPanel,
                             sid: int, kgcm: float, raw: int):
        err: str | None = None
        try:
            port.write_bytes(sid, _TORQUE_LIMIT_L_REG, [raw & 0xFF, (raw >> 8) & 0xFF])
        except Exception as exc:
            err = str(exc)
            print(f"[DBG safety] torque-limit write failed for ID {sid}: {exc}", flush=True)
        self.after(0, self._apply_torque_done, panel, sid, kgcm, raw, err)

    def _apply_torque_done(self, panel: ServoPanel, sid: int,
                           kgcm: float, raw: int, err: str | None):
        connected = self.app._port is not None
        self._rows[panel]['apply_btn'].config(state="normal" if connected else "disabled")
        label = panel.v_label.get() or f"ID {sid}"
        if err is not None:
            msg = f"{label}: torque-limit write failed — {err}"
            self._rows[panel]['status'].set(msg)
            self.app._status(f"Safety: {msg}")
            return
        msg = f"Torque limit set: {kgcm:.1f} kg-cm ({raw}/1000)"
        self._rows[panel]['status'].set(msg)
        self.app._status(f"Safety: {label} {msg.lower()}")

    def _apply_all_worker(self, port: ServoPort,
                          targets: list[tuple[ServoPanel, int, float, int]]):
        results = []
        for panel, sid, kgcm, raw in targets:
            try:
                port.write_bytes(sid, _TORQUE_LIMIT_L_REG,
                                 [raw & 0xFF, (raw >> 8) & 0xFF])
                results.append((panel, sid, kgcm, raw, None))
            except Exception as exc:
                results.append((panel, sid, kgcm, raw, str(exc)))
                print(f"[DBG safety] apply-all write failed for ID {sid}: {exc}", flush=True)
        self.after(0, self._apply_all_done, results)

    def _apply_all_done(self, results: list[tuple]):
        connected = self.app._port is not None
        ok_count = 0
        for panel, sid, kgcm, raw, err in results:
            self._rows[panel]['apply_btn'].config(
                state="normal" if connected else "disabled"
            )
            label = panel.v_label.get() or f"ID {sid}"
            if err is not None:
                self._rows[panel]['status'].set(
                    f"{label}: torque-limit write failed — {err}"
                )
            else:
                self._rows[panel]['status'].set(
                    f"Torque limit set: {kgcm:.1f} kg-cm ({raw}/1000)"
                )
                ok_count += 1
        for panel, row in self._rows.items():
            if not row['apply_btn']['state']:
                continue
            row['apply_btn'].config(state="normal" if connected else "disabled")
        total = len(results)
        if ok_count == total:
            self.app._status(f"Safety: applied torque limits to {ok_count} servo(s).")
        else:
            self.app._status(
                f"Safety: applied torque limits to {ok_count}/{total} servo(s); "
                f"see row status for failures."
            )
