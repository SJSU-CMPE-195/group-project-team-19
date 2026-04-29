from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

import serial.tools.list_ports

from constants import (
    _DEFAULT_BAUD,
    _BAUD_OPTIONS,
    _TELEMETRY_MS,
    _DEFAULT_LABELS,
    _GRID_COLS,
    _GRID_ROWS,
)
from protocol import ServoPort
from servo_panel import ServoPanel
from camera_panel import CameraPanel
from recorder_panel import RecorderPanel
from safety_panel import SafetyPanel


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Waveshare Bus Servo Controller")
        self.resizable(True, True)

        self._port: ServoPort | None = None
        self._poll_id = None

        self.v_port   = tk.StringVar()
        self.v_baud   = tk.StringVar(value=str(_DEFAULT_BAUD))
        self.v_status = tk.StringVar(value="Not connected.")

        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        P = dict(padx=6, pady=3)

        # Total columns: 1 for camera + _GRID_COLS for servo grid
        total_cols = 1 + _GRID_COLS

        cf = ttk.LabelFrame(self, text="Connection")
        cf.grid(row=0, column=0, columnspan=total_cols, sticky="ew", **P)

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

        ttk.Button(cf, text="Help / How to use",
                   command=self._show_help).grid(row=0, column=7, **P)

        # Camera on the left, spanning all servo rows
        self.camera_panel = CameraPanel(self, camera_index=0)
        self.camera_panel.grid(row=1, column=0, rowspan=_GRID_ROWS,
                               sticky="nsew", **P)

        # Build 5 servo panels in a 3-column × 2-row grid to the right of the camera
        self.panels = [
            ServoPanel(self, self, label) for label in _DEFAULT_LABELS
        ]
        for idx, panel in enumerate(self.panels):
            row = 1 + (idx // _GRID_COLS)
            col = 1 + (idx % _GRID_COLS)
            panel.grid(row=row, column=col, sticky="nsew", **P)

        # Tools row, directly below the servo grid
        recorder_row = 1 + _GRID_ROWS
        self.tools_notebook = ttk.Notebook(self)
        self.tools_notebook.grid(row=recorder_row, column=0,
                                 columnspan=total_cols, sticky="ew",
                                 padx=6, pady=(1, 2))

        recorder_tab = ttk.Frame(self.tools_notebook)
        safety_tab   = ttk.Frame(self.tools_notebook)
        self.tools_notebook.add(recorder_tab, text="Macro Recorder")
        self.tools_notebook.add(safety_tab,   text="Safety / Torque Limiters")

        self.recorder_panel = RecorderPanel(recorder_tab, self)
        self.recorder_panel.pack(fill="x", expand=False, padx=0, pady=0)

        self.safety_panel = SafetyPanel(safety_tab, self)
        self.safety_panel.pack(fill="x", expand=False, padx=0, pady=0)

        # Status bar at the bottom
        ttk.Label(self, textvariable=self.v_status, relief="sunken",
                  anchor="w").grid(row=recorder_row + 1, column=0,
                                   columnspan=total_cols,
                                   sticky="ew", padx=6, pady=2)

        for r in range(1, 1 + _GRID_ROWS):
            self.grid_rowconfigure(r, weight=1)
        self.grid_columnconfigure(0, weight=1)
        for c in range(1, total_cols):
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
        if hasattr(self, "recorder_panel"):
            self.recorder_panel.on_connection_changed()
        if hasattr(self, "safety_panel"):
            self.safety_panel.on_connection_changed()
        self._schedule_poll()

    def _disconnect(self):
        if self._poll_id:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        if self._port:
            self._port.close()
            self._port = None
        self.btn_connect.config(text="Connect")
        self.btn_detect.config(state="disabled")
        for panel in self.panels:
            panel.clear()
        if hasattr(self, "recorder_panel"):
            self.recorder_panel.on_connection_changed()
        if hasattr(self, "safety_panel"):
            self.safety_panel.on_connection_changed()
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
            if hasattr(self, "recorder_panel"):
                self.recorder_panel.on_connection_changed()
            if hasattr(self, "safety_panel"):
                self.safety_panel.refresh_servos()
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
        if hasattr(self, "recorder_panel"):
            self.recorder_panel.on_connection_changed()
        if hasattr(self, "safety_panel"):
            self.safety_panel.refresh_servos()

    def _schedule_poll(self):
        if self._port is None:
            print("[DBG poll] _schedule_poll called but port is None — stopping", flush=True)
            return
        print("[DBG poll] _schedule_poll — spawning worker thread", flush=True)
        threading.Thread(target=self._tele_worker, daemon=True).start()

    def _tele_worker(self):
        import traceback
        results = []
        for panel in self.panels:
            sid = panel.v_id.get()
            if not sid or self._port is None:
                results.append(None)
                continue
            print(f"[DBG poll] tele_worker tick — ID {sid}", flush=True)
            try:
                data = self._port.get_telemetry(sid)
                print(f"[DBG poll] ID {sid} get_telemetry returned: {data}", flush=True)
            except Exception as exc:
                print(f"[DBG poll] ID {sid} EXCEPTION in get_telemetry: {exc}", flush=True)
                traceback.print_exc()
                data = None
            results.append(data)
        self.after(0, self._tele_done, results)

    def _tele_done(self, results: list):
        statuses = ['None' if d is None else 'OK' for d in results]
        print(f"[DBG poll] _tele_done — results: {statuses}", flush=True)
        for panel, data in zip(self.panels, results):
            if panel.v_id.get():
                panel.update_telemetry(data)

        if hasattr(self, "safety_panel"):
            self.safety_panel.monitor()

        if self._port:
            self._poll_id = self.after(_TELEMETRY_MS, self._schedule_poll)

    def _show_help(self):
        """Open a scrollable how-to window."""
        existing = getattr(self, "_help_win", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_set()
            return

        win = tk.Toplevel(self)
        win.title("How to use the Servo Controller")
        win.geometry("720x640")
        win.transient(self)
        self._help_win = win

        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        text = tk.Text(frame, wrap="word", font=("Segoe UI", 10),
                       padx=10, pady=10, relief="flat")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        text.tag_configure("h1", font=("Segoe UI", 14, "bold"), spacing3=8)
        text.tag_configure("h2", font=("Segoe UI", 11, "bold"), spacing1=10, spacing3=4)
        text.tag_configure("body", spacing3=4)
        text.tag_configure("bullet", lmargin1=20, lmargin2=40, spacing3=2)
        text.tag_configure("warn", foreground="#a00", font=("Segoe UI", 10, "bold"))

        def add(content, tag="body"):
            text.insert("end", content + "\n", tag)

        add("Waveshare Bus Servo Controller — How to Use", "h1")

        add("The core problem", "h2")
        add(
            "Every STS3215 ships with the same default ID (usually 1). "
            "If two servos share an ID on the bus, they both respond to every "
            "command and collide. Each servo needs a unique ID before you can "
            "use them together."
        )

        add("Step 1 — Assign unique IDs (one-time setup)", "h2")
        add("Do this once per servo, before wiring them all together:")
        add("1. Connect ONLY ONE servo to the bus.", "bullet")
        add("2. Pick your COM port, then click Connect.", "bullet")
        add("3. Click Auto-detect — the servo shows up in the first panel.", "bullet")
        add("4. Click Change ID… and pick a number (1, 2, 3, 4, 5).", "bullet")
        add("5. Power down, swap in the next servo, repeat with the next ID.", "bullet")
        add(
            "⚠ Only one servo on the bus during ID change, otherwise every "
            "servo with the current ID gets the new ID at once.",
            "warn",
        )

        add("Step 2 — Normal use with all servos connected", "h2")
        add("1. Daisy-chain all 5 servos to the bus.", "bullet")
        add("2. Pick port → Connect.", "bullet")
        add("3. Click Auto-detect — it pings IDs 1–20 and finds all servos.", "bullet")
        add(
            "4. Servos are auto-assigned in ascending ID order: lowest ID → "
            "Pan, next → Tilt, then Joint 3, 4, 5.",
            "bullet",
        )
        add("5. Rename any panel by typing a new Label (e.g. 'Joint 3' → 'Elbow').", "bullet")

        add("Step 3 — Manual assignment", "h2")
        add("If auto-detect's order isn't what you want, you have two options:")
        add(
            "• Quick rename: type a new name in the Label field. The ID stays, "
            "the panel just displays a different name.",
            "bullet",
        )
        add(
            "• Reassign ID: change the ID spinbox on a panel to point it at a "
            "different servo. Set it to 0 to clear the panel.",
            "bullet",
        )

        add("Identifying which physical servo is which", "h2")
        add(
            "When you don't know which ID is which joint, use one of these "
            "tricks to find out:"
        )
        add(
            "• Wiggle test: on any panel, set Go To to a value a few degrees "
            "from the current angle, click Go. Whichever servo twitches is "
            "that panel's servo. Work through them one at a time.",
            "bullet",
        )
        add(
            "• Torque test: click Torque ON for one panel, then try to move "
            "each physical joint by hand. The one that won't budge is that "
            "panel's servo.",
            "bullet",
        )
        add(
            "• Teach test: click Teach: ON for one panel (this releases "
            "torque), then wiggle a joint by hand. If the Angle readout on "
            "that panel changes, you've found the right servo.",
            "bullet",
        )
        add(
            "Tip: once identified, write the ID on tape and stick it to the "
            "servo. Future you will thank you.",
            "bullet",
        )

        add("Panel controls explained", "h2")
        add("• Label / ID: panel name and the servo ID on the bus.", "bullet")
        add(
            "• Telemetry: live readings — angle, raw counts, speed, load %, "
            "voltage, temperature, current draw.",
            "bullet",
        )
        add(
            "• Step (°) with − / + buttons: nudge the servo by that many degrees.",
            "bullet",
        )
        add("• Go To (°) + Go: jump directly to an absolute angle (0–359.9°).", "bullet")
        add(
            "• Torque ON/OFF: lock the servo in place (ON) or let it spin "
            "freely (OFF). Torque must be ON to hold position against a load.",
            "bullet",
        )
        add(
            "• Change ID…: writes a new ID to the servo's EEPROM. "
            "Single servo on the bus only.",
            "bullet",
        )
        add(
            "• Teach: ON/OFF: releases torque so you can move the joint by "
            "hand. When you turn Teach OFF, the servo locks at its current "
            "position with torque back on — useful for recording poses.",
            "bullet",
        )

        add("Safety / Torque Limiters", "h2")
        add(
            "Two layers of protection. Edit values per-row, then click Apply "
            "(or Apply All Torque Limits) to push the kg-cm cap to the servo's "
            "register 48."
        )
        add(
            "• Max Torque (kg-cm): hardware torque cap. Rated 50 kg-cm, "
            "hard ceiling 45. Values above 45 are clamped automatically. "
            "Lives in RAM — must be re-applied after every power-cycle / reconnect.",
            "bullet",
        )
        add(
            "• Per-joint defaults: Pan/Tilt/Joint 3 = 40 kg-cm, Joint 4 = 30, "
            "Joint 5 = 25. Reset to Defaults restores these.",
            "bullet",
        )
        add(
            "• Max Load %, Current mA, Temp C: software fault thresholds. "
            "When any is exceeded, that servo's torque is disabled and the "
            "row turns red. Click Clear Faults to re-enable torque.",
            "bullet",
        )
        add(
            "• The kg-cm cap also acts as a software load cap: effective "
            "load ceiling = min(Max Load %, kg-cm/50 × 100).",
            "bullet",
        )

        add("Macro Recorder (Teach & Repeat)", "h2")
        add(
            "Record physical movements and play them back like a macro. "
            "Recording happens automatically during the telemetry poll — no "
            "extra bus traffic. Playback replays the saved trajectory at the "
            "original speed."
        )
        add("1. Put the joints you want to teach into Teach: ON.", "bullet")
        add("2. Click ● Start Recording.", "bullet")
        add("3. Move the arm physically through the motion you want to teach.", "bullet")
        add("4. Click ■ Stop Recording when done.", "bullet")
        add(
            "5. Click ▶ Playback to replay. Teach mode is switched off and "
            "torque is re-engaged automatically before playback starts.",
            "bullet",
        )
        add("• Stop Playback aborts mid-replay; the arm freezes in place.", "bullet")
        add("• Clear Recording wipes the saved trajectory.", "bullet")
        add(
            "Each recorded snapshot stores: elapsed time, joint label, servo "
            "ID, angle in degrees, and raw position counts. Snapshots occur "
            "roughly every 350 ms (the telemetry poll rate).",
            "bullet",
        )

        add("Troubleshooting", "h2")
        add(
            "• Auto-detect finds nothing: check USB cable, external power to "
            "the adapter (servos need 6–12V — USB alone isn't enough), and "
            "that baud rate matches (default 1,000,000).",
            "bullet",
        )
        add(
            "• Only some servos found: likely an ID collision or a loose "
            "daisy-chain connector. Disconnect them all and re-ID them one by one.",
            "bullet",
        )
        add(
            "• Telemetry shows '?': the servo stopped responding on that "
            "poll. Usually transient — if it persists, check wiring and power.",
            "bullet",
        )
        add(
            "• Playback moves look jerky: the poll rate (350 ms) is the "
            "snapshot interval. Slow physical movements record more smoothly.",
            "bullet",
        )

        text.configure(state="disabled")
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 10))

    def _status(self, msg: str):
        self.v_status.set(msg)

    def destroy(self):
        if hasattr(self, "recorder_panel"):
            if self.recorder_panel._playing:
                self.recorder_panel._stop_playback_flag.set()
        if hasattr(self, "safety_panel"):
            self.safety_panel.stop()
        if hasattr(self, "camera_panel"):
            self.camera_panel.stop_camera()
        self._disconnect()
        super().destroy()
