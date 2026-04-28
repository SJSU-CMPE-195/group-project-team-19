from __future__ import annotations

import struct
import threading
import time
import tkinter as tk
from tkinter import simpledialog, ttk

from constants import (
    _PRESENT_POS_L,
    _COUNTS,
    _COUNT_PER_DEG,
    _DEG_PER_COUNT,
)
from servo_panel import ServoPanel


class RecorderPanel(ttk.LabelFrame):
    """
    Teach-and-repeat macro recorder.

    Recording: snapshots are captured from the existing telemetry loop, so no
    extra serial traffic is generated. Each snapshot is a list of per-servo
    dicts taken at one poll tick, sharing one timestamp.

    Playback: replays the stored trajectory in a worker thread, honoring the
    original inter-snapshot timing. Movement commands go through
    ServoPort.move_to, identical to manual controls.
    """

    def __init__(self, parent, app: App):
        super().__init__(parent, text="Macro Recorder (Teach & Repeat)")
        self.app = app

        # Multi-macro storage: name → list of snapshots
        self._macros: dict[str, list[dict]] = {"Macro 1": []}
        self._active_macro: str = "Macro 1"
        self.v_active_macro = tk.StringVar(value="Macro 1")

        # Recording state
        self._recording = False
        self._record_start: float = 0.0
        self._stop_record_flag = threading.Event()
        self._record_thread: threading.Thread | None = None
        self.v_sample_rate = tk.StringVar(value="20")

        # Playback state
        self._playing = False
        self._stop_playback_flag = threading.Event()
        self._playback_thread: threading.Thread | None = None

        self.v_status = tk.StringVar(value="Idle.")
        self.v_count  = tk.StringVar(value="0 points")

        self._build()
        self._refresh_buttons()

    @property
    def _points(self) -> list[dict]:
        return self._macros.get(self._active_macro, [])

    @_points.setter
    def _points(self, val: list) -> None:
        self._macros[self._active_macro] = val

    def _refresh_macro_list(self):
        names = list(self._macros.keys())
        self._macro_combo['values'] = names
        self.v_active_macro.set(self._active_macro)
        n = len(self._points)
        self.v_count.set(f"{n} points")

    def _on_macro_select(self, _event=None):
        selected = self.v_active_macro.get()
        if selected and selected in self._macros:
            self._active_macro = selected
            n = len(self._points)
            self.v_count.set(f"{n} points")
            self.v_status.set("Idle." if n == 0 else f"Ready — {n} points.")
            self._refresh_buttons()

    def _new_macro(self):
        i = 1
        while f"Macro {i}" in self._macros:
            i += 1
        name = f"Macro {i}"
        self._macros[name] = []
        self._active_macro = name
        self._refresh_macro_list()
        self._refresh_buttons()
        self.app._status(f"Recorder: created {name}.")

    def _rename_macro(self):
        new_name = simpledialog.askstring(
            "Rename Macro", "Enter new name:",
            initialvalue=self._active_macro, parent=self,
        )
        if not new_name or new_name == self._active_macro:
            return
        if new_name in self._macros:
            self.app._status(f"Recorder: a macro named '{new_name}' already exists.")
            return
        self._macros = {
            (new_name if k == self._active_macro else k): v
            for k, v in self._macros.items()
        }
        self._active_macro = new_name
        self._refresh_macro_list()
        self.app._status(f"Recorder: renamed to '{new_name}'.")

    def _delete_macro(self):
        if len(self._macros) <= 1:
            self.app._status("Recorder: cannot delete the last macro.")
            return
        name = self._active_macro
        del self._macros[name]
        self._active_macro = next(iter(self._macros))
        self._refresh_macro_list()
        self._refresh_buttons()
        self.app._status(f"Recorder: deleted '{name}'.")

    def _build(self):
        # ── Macro selector ───────────────────────────────────────────────
        mrow = ttk.Frame(self)
        mrow.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 1))

        ttk.Label(mrow, text="Macro:").pack(side="left")
        self._macro_combo = ttk.Combobox(
            mrow, textvariable=self.v_active_macro,
            values=["Macro 1"], state="readonly", width=16,
        )
        self._macro_combo.pack(side="left", padx=(2, 6))
        self._macro_combo.bind("<<ComboboxSelected>>", self._on_macro_select)

        self.btn_new_macro    = ttk.Button(mrow, text="New",    width=6,
                                           command=self._new_macro)
        self.btn_rename_macro = ttk.Button(mrow, text="Rename", width=7,
                                           command=self._rename_macro)
        self.btn_delete_macro = ttk.Button(mrow, text="Delete", width=7,
                                           command=self._delete_macro)
        self.btn_new_macro.pack(side="left", padx=2)
        self.btn_rename_macro.pack(side="left", padx=2)
        self.btn_delete_macro.pack(side="left", padx=2)

        # ── Record / playback controls ───────────────────────────────────
        row = ttk.Frame(self)
        row.grid(row=1, column=0, sticky="ew", padx=4, pady=(1, 1))

        self.btn_start = ttk.Button(row, text="● Start Recording",
                                    command=self.start_recording)
        self.btn_start.pack(side="left", padx=3)

        self.btn_stop = ttk.Button(row, text="■ Stop Recording",
                                   command=self.stop_recording)
        self.btn_stop.pack(side="left", padx=3)

        self.btn_clear = ttk.Button(row, text="Clear Recording",
                                    command=self.clear_recording)
        self.btn_clear.pack(side="left", padx=3)

        ttk.Separator(row, orient="vertical").pack(side="left", fill="y", padx=8)

        self.btn_play = ttk.Button(row, text="▶ Playback",
                                   command=self.start_playback)
        self.btn_play.pack(side="left", padx=3)

        self.btn_stop_play = ttk.Button(row, text="Stop Playback",
                                        command=self.stop_playback)
        self.btn_stop_play.pack(side="left", padx=3)

        ttk.Label(row, textvariable=self.v_count, width=14,
                  anchor="e", relief="sunken").pack(side="right", padx=6)
        ttk.Label(row, textvariable=self.v_status, anchor="w",
                  relief="sunken").pack(side="right", fill="x", expand=True, padx=6)

        cfg = ttk.Frame(self)
        cfg.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 2))
        ttk.Label(cfg, text="Sample rate:").pack(side="left")
        ttk.Combobox(cfg, textvariable=self.v_sample_rate,
                     values=["5", "10", "20", "50"],
                     width=4, state="readonly").pack(side="left", padx=(2, 4))
        ttk.Label(cfg, text="Hz   (warn at 5 min, stop at 10 min)",
                  foreground="gray").pack(side="left")

        ttk.Separator(cfg, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Label(cfg, text="Playback speed:").pack(side="left")
        self.v_playback_speed = tk.StringVar(value="1")
        ttk.Combobox(cfg, textvariable=self.v_playback_speed,
                     values=["0.25", "0.5", "1", "2", "4"],
                     width=5, state="readonly").pack(side="left", padx=(2, 4))
        ttk.Label(cfg, text="×", foreground="gray").pack(side="left")

    # ── Button state management ──────────────────────────────────────────

    def _refresh_buttons(self):
        connected = self.app._port is not None
        has_points = len(self._points) > 0
        idle = not self._recording and not self._playing

        # Macro management: only available when idle.
        self.btn_new_macro.config(state="normal" if idle else "disabled")
        self.btn_rename_macro.config(state="normal" if idle else "disabled")
        self.btn_delete_macro.config(
            state="normal" if idle and len(self._macros) > 1 else "disabled"
        )
        self._macro_combo.config(state="readonly" if idle else "disabled")

        # Start recording: requires connection, not currently recording or playing.
        self.btn_start.config(
            state="normal" if connected and idle else "disabled"
        )
        # Stop recording: only while recording.
        self.btn_stop.config(
            state="normal" if self._recording else "disabled"
        )
        # Clear: allowed when we have data and aren't mid-operation.
        self.btn_clear.config(
            state="normal" if has_points and idle else "disabled"
        )
        # Playback: needs points, connection, and idle state.
        self.btn_play.config(
            state="normal" if has_points and connected and idle else "disabled"
        )
        # Stop playback: only during playback.
        self.btn_stop_play.config(
            state="normal" if self._playing else "disabled"
        )

    # ── Recording ────────────────────────────────────────────────────────

    def start_recording(self):
        if self._recording or self._playing:
            return
        if self.app._port is None:
            self.app._status("Recorder: connect to the bus before recording.")
            return
        self._points = []
        self._record_start = time.monotonic()
        self._recording = True
        self._stop_record_flag.clear()
        self.v_status.set("Recording…")
        self.v_count.set("0 points")
        self._refresh_buttons()
        self.app._status("Recorder: recording started. Move the arm in teach mode.")
        self._record_thread = threading.Thread(target=self._record_worker, daemon=True)
        self._record_thread.start()

    def stop_recording(self):
        if not self._recording:
            return
        self._recording = False
        self._stop_record_flag.set()
        self.btn_stop.config(state="disabled")
        self.v_status.set("Stopping…")

    def _record_worker(self):
        try:
            rate = int(self.v_sample_rate.get())
        except (ValueError, tk.TclError):
            rate = 20
        interval = 1.0 / rate

        panel_info = [
            (p.v_label.get(), p.v_id.get())
            for p in self.app.panels if p.v_id.get() > 0
        ]

        t_start = time.monotonic()
        next_tick = t_start
        warned_5min = False

        try:
            while self._recording:
                sleep_time = next_tick - time.monotonic()
                if sleep_time > 0:
                    self._stop_record_flag.wait(timeout=sleep_time)
                if not self._recording:
                    break

                elapsed = time.monotonic() - t_start

                if elapsed >= 600:
                    self.after(0, self.app._status,
                               "Recorder: 10-minute limit reached — stopping.")
                    self._recording = False
                    break
                if not warned_5min and elapsed >= 300:
                    warned_5min = True
                    self.after(0, self.app._status,
                               "Recorder: 5-minute warning — recording still active.")

                port = self.app._port
                if port is None:
                    break

                read_start = time.monotonic()
                t = read_start - t_start
                per_servo = []
                for label, sid in panel_info:
                    raw = port.read_bytes(sid, _PRESENT_POS_L, 2)
                    if raw and len(raw) >= 2:
                        counts = struct.unpack_from('<H', raw, 0)[0] & 0x0FFF
                        per_servo.append({
                            'label':      label,
                            'servo_id':   sid,
                            'angle_deg':  counts * _DEG_PER_COUNT,
                            'pos_counts': counts,
                        })

                if per_servo:
                    self._points.append({'t': t, 'servos': per_servo})

                read_dur = time.monotonic() - read_start
                if read_dur > interval:
                    self.after(0, self.app._status,
                               f"Recorder: sample took {read_dur*1000:.0f}ms > {interval*1000:.0f}ms — best effort")

                self.after(0, self._update_record_ui, len(self._points), elapsed)

                next_tick += interval
                if next_tick < time.monotonic():
                    next_tick = time.monotonic()
        finally:
            self.after(0, self._record_done)

    def _update_record_ui(self, n: int, elapsed: float):
        self.v_count.set(f"{n} points")
        self.v_status.set(f"Recording… {elapsed:.1f}s  {n} pts")

    def _record_done(self):
        self._recording = False
        n = len(self._points)
        self.v_status.set(f"Stopped — {n} points.")
        self.v_count.set(f"{n} points")
        self._refresh_buttons()
        self.app._status(f"Recorder: recording stopped. {n} snapshots captured.")

    def clear_recording(self):
        if self._recording or self._playing:
            return
        self._points = []
        self.v_status.set("Idle.")
        self.v_count.set("0 points")
        self._refresh_buttons()
        self.app._status("Recorder: recording cleared.")

    def is_recording(self) -> bool:
        return self._recording

    def snapshot(self, panels: list[ServoPanel]):
        """
        Called from the main thread (inside _tele_done) once per telemetry poll.
        Captures the current angle/counts for every assigned servo at one shared
        timestamp — so all joints record simultaneously.
        """
        if not self._recording:
            return
        t = time.monotonic() - self._record_start
        per_servo = []
        for panel in panels:
            sid = panel.v_id.get()
            if not sid:
                continue
            data = panel._last_data
            if data is None:
                continue
            counts = data.get('pos_counts')
            if counts is None:
                continue
            per_servo.append({
                'label':      panel.v_label.get(),
                'servo_id':   sid,
                'angle_deg':  counts * _DEG_PER_COUNT,
                'pos_counts': counts,
            })
        if not per_servo:
            return
        self._points.append({'t': t, 'servos': per_servo})
        n = len(self._points)
        self.v_count.set(f"{n} points")
        # Status refresh ~once per second.
        if n % 3 == 0:
            self.v_status.set(f"Recording… {t:5.1f}s, {n} points")

    # ── Playback ─────────────────────────────────────────────────────────

    def start_playback(self):
        if self._recording or self._playing:
            return
        if not self._points:
            self.app._status("Recorder: nothing to play back.")
            return
        if self.app._port is None:
            self.app._status("Recorder: connect to the bus before playback.")
            return

        # Teach OFF, torque ON before playback.
        for panel in self.app.panels:
            if panel.is_in_teach():
                panel.exit_teach_async()

        self._stop_playback_flag.clear()
        self._playing = True
        self.v_status.set("Playback starting…")
        self._refresh_buttons()
        self.app._status("Recorder: playback started.")

        self._playback_thread = threading.Thread(
            target=self._playback_worker, daemon=True
        )
        self._playback_thread.start()

    def stop_playback(self):
        if not self._playing:
            return
        self._stop_playback_flag.set()
        self.app._status("Recorder: stopping playback…")

    def _playback_worker(self):
        """
        Runs in a background thread. Sleeps between snapshots to recreate
        the original timing, then sends move_to for each servo.
        """
        # Give any just-exited teach mode time to complete its torque-on write.
        time.sleep(0.15)

        try:
            speed_mult = float(self.v_playback_speed.get())
        except ValueError:
            speed_mult = 1.0
        speed_label = self.v_playback_speed.get()

        t0 = time.monotonic()
        points = list(self._points)   # snapshot so a macro switch can't affect playback
        total = len(points)

        try:
            for i, point in enumerate(points):
                if self._stop_playback_flag.is_set():
                    break
                # Scale the recorded timestamp by the speed multiplier.
                target_elapsed = point['t'] / speed_mult
                while True:
                    if self._stop_playback_flag.is_set():
                        break
                    now_elapsed = time.monotonic() - t0
                    remaining = target_elapsed - now_elapsed
                    if remaining <= 0:
                        break
                    # Sleep in small chunks so stop is responsive.
                    time.sleep(min(remaining, 0.05))

                if self._stop_playback_flag.is_set():
                    break

                port = self.app._port
                if port is None:
                    break

                # Send move commands for every servo in this snapshot.
                for s in point['servos']:
                    counts = s.get('pos_counts')
                    if counts is None:
                        # Fall back to angle if counts weren't recorded.
                        deg = s.get('angle_deg', 0.0)
                        counts = max(0, min(_COUNTS - 1,
                                            int(round(deg * _COUNT_PER_DEG))))
                    try:
                        port.move_to(s['servo_id'], counts)
                    except Exception as exc:
                        print(f"[DBG playback] move_to failed for ID {s['servo_id']}: {exc}",
                              flush=True)

                # Throttle status updates.
                if i % 3 == 0:
                    self.after(0, self.v_status.set,
                               f"Playback @ {speed_label}× — {i + 1}/{total}")
        finally:
            stopped_early = self._stop_playback_flag.is_set()
            self.after(0, self._playback_done, stopped_early)

    def _playback_done(self, stopped_early: bool):
        self._playing = False
        n = len(self._points)
        if stopped_early:
            self.v_status.set(f"Playback stopped. ({n} points)")
            self.app._status("Recorder: playback stopped by user.")
        else:
            self.v_status.set(f"Playback finished. ({n} points)")
            self.app._status("Recorder: playback finished.")
        self._refresh_buttons()

    # ── External hooks ───────────────────────────────────────────────────

    def on_connection_changed(self):
        """Called by App when connect/disconnect happens."""
        if self.app._port is None:
            if self._recording:
                self.stop_recording()
            if self._playing:
                self.stop_playback()
        self._refresh_buttons()