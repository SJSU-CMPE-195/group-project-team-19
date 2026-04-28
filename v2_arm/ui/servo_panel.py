from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from constants import (
    _DEFAULT_SPEED,
    _DEFAULT_NUDGE,
    _MAX_GOAL_SPEED,
    _COUNTS,
    _COUNT_PER_DEG,
    _DEG_PER_COUNT,
)
from widgets import _Tooltip


class ServoPanel(ttk.LabelFrame):
    """UI panel for a single servo on the shared bus."""

    def __init__(self, parent, app: App, default_label: str):
        super().__init__(parent, text=default_label)
        self.app = app

        self.series: str | None = None

        self.v_label  = tk.StringVar(value=default_label)
        self.v_id     = tk.IntVar(value=0)
        self.v_nudge  = tk.DoubleVar(value=_DEFAULT_NUDGE)
        self.v_goto   = tk.DoubleVar(value=0.0)
        self.v_series = tk.StringVar(value="—")
        self._torque_on = False
        self.v_tele = {
            'angle_deg':     tk.StringVar(value='—'),
            'pos_counts':    tk.StringVar(value='—'),
            'speed':         tk.StringVar(value='—'),
            'load_pct':      tk.StringVar(value='—'),
            'voltage_v':     tk.StringVar(value='—'),
            'temperature_c': tk.StringVar(value='—'),
            'current_ma':    tk.StringVar(value='—'),
        }
        # Latest raw telemetry, used by the macro recorder.
        self._last_data: dict | None = None
        self.v_speed = tk.IntVar(value=_DEFAULT_SPEED)
        self._speed_debounce_id = None
        self._zero_counts = 2048
        self._ctrl_btns: list = []
        self.btn_torque: ttk.Button | None = None
        self.btn_change_id: ttk.Button | None = None
        self.btn_set_zero: ttk.Button | None = None
        self.btn_reset_zero: ttk.Button | None = None
        self._teach_mode = False
        self.btn_teach: ttk.Button | None = None

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

        ctrl = ttk.LabelFrame(self, text="Control")
        ctrl.grid(row=1, column=1, sticky="nsew", **P)

        ttk.Label(ctrl, text="Step (°):").grid(row=0, column=0, sticky="w", **P)
        ttk.Entry(ctrl, textvariable=self.v_nudge, width=6).grid(row=0, column=1, **P)

        btn_minus = ttk.Button(ctrl, text="−", width=4, state="disabled",
                               command=lambda: self._nudge(-1))
        btn_plus  = ttk.Button(ctrl, text="+", width=4, state="disabled",
                               command=lambda: self._nudge(+1))
        btn_minus.grid(row=1, column=0, **P)
        btn_plus.grid(row=1, column=1, **P)

        ttk.Separator(ctrl, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=8)

        speed_lbl = ttk.Label(ctrl, text="Speed:")
        speed_lbl.grid(row=3, column=0, sticky="w", **P)
        _Tooltip(speed_lbl, "0 = max speed / no limit (Feetech default after power-cycle)")
        self._speed_slider = tk.Scale(
            ctrl, from_=0, to=_MAX_GOAL_SPEED, orient="horizontal",
            variable=self.v_speed, showvalue=0,
            command=self._on_speed_change,
        )
        self._speed_slider.grid(row=3, column=1, sticky="ew", **P)
        self._speed_slider.bind("<ButtonRelease-1>", self._write_speed_immediate)
        speed_entry = ttk.Entry(ctrl, textvariable=self.v_speed, width=5)
        speed_entry.grid(row=3, column=2, **P)
        speed_entry.bind("<Return>", self._on_speed_entry)
        speed_entry.bind("<FocusOut>", self._on_speed_entry)
        ctrl.columnconfigure(1, weight=1)

        ttk.Label(ctrl, text="Go To (°):").grid(row=4, column=0, sticky="w", **P)
        ttk.Entry(ctrl, textvariable=self.v_goto, width=8).grid(row=4, column=1, **P)
        btn_goto = ttk.Button(ctrl, text="Go", state="disabled", command=self._go_to)
        btn_goto.grid(row=4, column=2, **P)

        ttk.Separator(ctrl, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=8)

        self.btn_torque = ttk.Button(ctrl, text="Torque ON", state="disabled",
                                     command=self._toggle_torque)
        self.btn_torque.grid(row=6, column=0, columnspan=2, **P)

        ttk.Separator(ctrl, orient="horizontal").grid(
            row=7, column=0, columnspan=3, sticky="ew", pady=8)
        self.btn_change_id = ttk.Button(ctrl, text="Change ID…", state="disabled",
                                        command=self._change_id)
        self.btn_change_id.grid(row=8, column=0, columnspan=3, **P)

        self.btn_teach = ttk.Button(ctrl, text="Teach: OFF", state="disabled",
                                    command=self._toggle_teach)
        self.btn_teach.grid(row=9, column=0, columnspan=3, **P)

        ttk.Separator(ctrl, orient="horizontal").grid(
            row=10, column=0, columnspan=3, sticky="ew", pady=8)

        self.btn_set_zero = ttk.Button(ctrl, text="Set zero here", state="disabled",
                                       command=self._set_zero_here)
        self.btn_set_zero.grid(row=11, column=0, columnspan=2, **P)

        self.btn_reset_zero = ttk.Button(ctrl, text="Reset zero", state="disabled",
                                         command=self._reset_zero)
        self.btn_reset_zero.grid(row=11, column=2, **P)

        self._ctrl_btns = [btn_minus, btn_plus, btn_goto, self.btn_torque,
                           self.btn_change_id, self.btn_set_zero, self.btn_reset_zero]

    def _update_title(self):
        try:
            sid = self.v_id.get()
        except tk.TclError:
            return
        label = self.v_label.get() or "?"
        self.config(text=f"{label}  (ID {sid})" if sid else f"{label}  —  not connected")

    def _on_label_change(self, *_):
        self._update_title()
        if hasattr(self.app, "safety_panel"):
            self.app.safety_panel.refresh_servos()

    def _on_id_change(self, *_):
        try:
            sid = self.v_id.get()
        except tk.TclError:
            return
        if sid > 0 and self.app._port is not None:
            self.set_controls_enabled(True)
        elif sid == 0:
            self.set_controls_enabled(False)
        self._update_title()
        if hasattr(self.app, "safety_panel"):
            self.app.safety_panel.refresh_servos()

    def set_servo(self, sid: int, label: str | None = None):
        self.v_id.set(sid)
        if label is not None:
            self.v_label.set(label)
        self.set_controls_enabled(True)
        self._update_title()

    def clear(self):
        if self._teach_mode:
            self._teach_mode = False
            if self.btn_teach:
                self.btn_teach.config(text="Teach: OFF")
        self.set_controls_enabled(False)
        for v in self.v_tele.values():
            v.set("—")
        self.v_series.set("—")
        self._last_data = None
        self._torque_on = False
        if self.btn_torque:
            self.btn_torque.config(text="Torque ON")
        self.v_speed.set(_DEFAULT_SPEED)
        self._zero_counts = 2048

    def set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled and not self._teach_mode else "disabled"
        for btn in self._ctrl_btns:
            btn.config(state=state)
        if self.btn_teach is not None:
            self.btn_teach.config(state="normal" if enabled else "disabled")

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

    def _nudge(self, sign: int):
        self._send_move(self.current_angle() + sign * self.v_nudge.get())

    def _go_to(self):
        self._send_move(self.v_goto.get())

    def _on_speed_entry(self, _event=None):
        try:
            speed = self.v_speed.get()
        except tk.TclError:
            self.v_speed.set(_DEFAULT_SPEED)
            return
        clamped = max(0, min(_MAX_GOAL_SPEED, speed))
        if clamped != speed:
            self.v_speed.set(clamped)
        self._write_speed()

    def _on_speed_change(self, _val=None):
        if self._speed_debounce_id is not None:
            self.after_cancel(self._speed_debounce_id)
        self._speed_debounce_id = self.after(200, self._write_speed)

    def _write_speed_immediate(self, _event=None):
        if self._speed_debounce_id is not None:
            self.after_cancel(self._speed_debounce_id)
            self._speed_debounce_id = None
        self._write_speed()

    def _write_speed(self):
        self._speed_debounce_id = None
        sid = self.v_id.get()
        if not sid or self.app._port is None:
            return
        speed = self.v_speed.get()
        threading.Thread(target=self.app._port.set_speed,
                         args=(sid, speed), daemon=True).start()

    def _send_move(self, deg: float):
        sid = self.v_id.get()
        if not sid or self.app._port is None:
            return
        raw = self._deg_to_counts(deg)
        counts = max(0, min(_COUNTS - 1, raw))
        speed = self.v_speed.get()
        threading.Thread(target=self._move_worker,
                         args=(sid, counts, speed), daemon=True).start()
        msg = f"{self.v_label.get()}: moving to {deg:.1f}°  ({counts} counts)"
        if counts != raw:
            msg += "  — clamped to hardware limit"
        self.app._status(msg)

    def _move_worker(self, sid: int, counts: int, speed: int):
        port = self.app._port
        if port is None:
            return
        port.set_speed(sid, speed)
        port.move_to(sid, counts)

    def _set_zero_here(self):
        label = self.v_label.get()
        if self._last_data is None:
            self.app._status(f"{label}: Set zero failed — no telemetry yet.")
            return
        self._zero_counts = self._last_data['pos_counts']
        self.app._status(f"{label}: zero set at raw count {self._zero_counts}.")
        self.update_telemetry(self._last_data)

    def _reset_zero(self):
        self._zero_counts = 2048
        self.app._status(f"{self.v_label.get()}: zero reset to count 2048.")
        self.update_telemetry(self._last_data)

    def _toggle_torque(self):
        sid = self.v_id.get()
        if not sid or self.app._port is None:
            return
        self._torque_on = not self._torque_on
        en = self._torque_on
        threading.Thread(target=self.app._port.set_torque,
                         args=(sid, en), daemon=True).start()
        self.btn_torque.config(text="Torque OFF" if en else "Torque ON")
        self.app._status(f"{self.v_label.get()}: torque {'enabled' if en else 'disabled'}.")

    def _change_id(self):
        sid = self.v_id.get()
        if not sid or self.app._port is None:
            return
        ok = messagebox.askokcancel(
            "Change Servo ID",
            f"Current ID: {sid}\n\n"
            "Only ONE servo should be connected to the bus when changing IDs,\n"
            "to avoid address conflicts.\n\n"
            "Continue?",
            parent=self,
        )
        if not ok:
            return
        new_id = simpledialog.askinteger(
            "Change Servo ID",
            f"New ID for servo {sid}  (1–253):",
            minvalue=1, maxvalue=253, parent=self,
        )
        if new_id is None or new_id == sid:
            return
        self.btn_change_id.config(state="disabled")
        threading.Thread(
            target=self._change_id_worker, args=(sid, new_id), daemon=True
        ).start()

    def _change_id_worker(self, old_id: int, new_id: int):
        try:
            self.app._port.change_id(old_id, new_id)
            err = None
        except Exception as exc:
            err = str(exc)
        self.after(0, self._change_id_done, old_id, new_id, err)

    def _change_id_done(self, old_id: int, new_id: int, error):
        self.btn_change_id.config(state="normal")
        if error:
            self.app._status(f"ID change failed: {error}")
        else:
            self.v_id.set(new_id)
            self.app._status(f"Servo ID changed from {old_id} to {new_id}.")

    def _toggle_teach(self):
        sid = self.v_id.get()
        if not sid or self.app._port is None:
            return
        if not self._teach_mode:
            self.enter_teach()
        else:
            self.exit_teach_async()

    def enter_teach(self):
        """Enter teach mode no-op if already in it."""
        if self._teach_mode:
            return
        sid = self.v_id.get()
        if not sid or self.app._port is None:
            return
        self._teach_mode = True
        self.btn_teach.config(text="Teach: ON")
        for btn in self._ctrl_btns:
            btn.config(state="disabled")
        self._torque_on = False
        self.btn_torque.config(text="Torque ON")
        threading.Thread(
            target=self.app._port.set_torque, args=(sid, False), daemon=True
        ).start()
        self.app._status(f"{self.v_label.get()}: teach mode ON — move joint freely.")

    def exit_teach_async(self):
        """Exit teach mode then re-engage torque at current position in worker thread."""
        if not self._teach_mode:
            return
        self.btn_teach.config(state="disabled")
        threading.Thread(target=self._exit_teach_worker, daemon=True).start()

    def is_in_teach(self) -> bool:
        return self._teach_mode

    def _exit_teach_worker(self):
        sid = self.v_id.get()
        counts = None
        if sid and self.app._port is not None:
            data = self.app._port.get_telemetry(sid)
            if data:
                counts = data['pos_counts']
                self.app._port.move_to(sid, counts)
                time.sleep(0.05)
            self.app._port.set_torque(sid, True)
        self.after(0, self._exit_teach_done, counts)

    def _exit_teach_done(self, counts):
        self._teach_mode = False
        self._torque_on = True
        self.btn_torque.config(text="Torque OFF")
        self.btn_teach.config(text="Teach: OFF")
        self.set_controls_enabled(True)
        label = self.v_label.get()
        if counts is not None:
            self.app._status(
                f"{label}: teach mode OFF — held at {self._counts_to_deg(counts):.1f}°, torque on."
            )
        else:
            self.app._status(f"{label}: teach mode OFF — torque on.")

