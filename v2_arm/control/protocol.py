import struct
import threading
import time

import serial

from constants import (
    _DEFAULT_BAUD,
    _TORQUE_ENABLE,
    _GOAL_POSITION_L,
    _GOAL_SPEED_L,
    _PRESENT_POS_L,
    _PRESENT_CURRENT_L,
    _SERVO_ID_ADDR,
    _LOCK_ADDR,
)


# ── STS packet helpers ───────────────────────────────────────────────────────


def _checksum(body: list[int]) -> int:
    return (~sum(body)) & 0xFF


def _build(servo_id: int, instr: int, params: list[int]) -> bytes:
    length = len(params) + 2
    body = [servo_id, length, instr] + params
    return bytes([0xFF, 0xFF] + body + [_checksum(body)])


def _parse(data: bytes):
    """Return (error, params_bytes) or None on bad/missing packet."""
    if len(data) < 6 or data[0] != 0xFF or data[1] != 0xFF:
        return None
    length = data[3]
    if len(data) < 4 + length:
        return None
    body = list(data[2 : 3 + length])  # ID + LEN + ERROR + params (no checksum)
    if _checksum(body) != data[3 + length]:
        return None
    return data[4], data[5 : 3 + length]


# ── ServoPort ────────────────────────────────────────────────────────────────


class ServoPort:
    """Thread-safe STS/SMS half-duplex serial communication."""

    def __init__(self, port: str, baud: int = _DEFAULT_BAUD):
        self.ser = serial.Serial(
            port, baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
        )
        self._lock = threading.Lock()

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass

    def _tx_rx(self, pkt: bytes, resp_params: int):
        """Send a packet and read back the response."""
        response_len = 6 + resp_params
        with self._lock:
            self.ser.reset_input_buffer()
            self.ser.write(pkt)
            self.ser.flush()
            time.sleep(len(pkt) * 10 / self.ser.baudrate + 0.002)
            waiting = self.ser.in_waiting
            print(f"[DBG tx_rx] sent {len(pkt)}B: {pkt.hex()}  |  in_waiting={waiting}  |  reading {response_len}B", flush=True)
            raw = self.ser.read(response_len)
            print(f"[DBG tx_rx] got {len(raw)}B: {raw.hex() if raw else '(empty)'}", flush=True)
        result = _parse(raw)
        print(f"[DBG tx_rx] parse → {result}", flush=True)
        return result

    def _write_only(self, pkt: bytes):
        """Send a packet; do not wait for a response."""
        with self._lock:
            self.ser.reset_input_buffer()
            self.ser.write(pkt)
            self.ser.flush()
            time.sleep(len(pkt) * 10 / self.ser.baudrate + 0.002)
            time.sleep(0.003)
            drained = self.ser.in_waiting
            self.ser.reset_input_buffer()
            print(f"[DBG write_only] sent {len(pkt)}B: {pkt.hex()}  |  drained {drained}B from echo", flush=True)

    def ping(self, servo_id: int):
        return self._tx_rx(_build(servo_id, 0x01, []), 0)

    def read_bytes(self, servo_id: int, address: int, length: int):
        result = self._tx_rx(_build(servo_id, 0x02, [address, length]), length)
        if result is None:
            return None
        error, params = result
        return params if not error else None

    def write_bytes(self, servo_id: int, address: int, data: list[int]):
        self._write_only(_build(servo_id, 0x03, [address] + list(data)))

    def set_torque(self, servo_id: int, enable: bool):
        self.write_bytes(servo_id, _TORQUE_ENABLE, [1 if enable else 0])

    def move_to(self, servo_id: int, counts: int):
        self.write_bytes(servo_id, _GOAL_POSITION_L,
                         [counts & 0xFF, (counts >> 8) & 0xFF])

    def set_speed(self, servo_id: int, speed: int):
        self.write_bytes(servo_id, _GOAL_SPEED_L,
                         [speed & 0xFF, (speed >> 8) & 0xFF])

    def get_telemetry(self, servo_id: int):
        raw = self.read_bytes(servo_id, _PRESENT_POS_L, 8)
        if raw is None or len(raw) < 8:
            return None

        pos_raw   = struct.unpack_from('<H', raw, 0)[0] & 0x0FFF
        speed_raw = struct.unpack_from('<H', raw, 2)[0]
        load_raw  = struct.unpack_from('<H', raw, 4)[0]
        voltage   = raw[6]
        temp      = raw[7]

        speed    = speed_raw if speed_raw <= 32767 else speed_raw - 65536
        load_pct = (load_raw & 0x3FF) / 1023.0 * 100.0

        curr_raw = self.read_bytes(servo_id, _PRESENT_CURRENT_L, 2)
        current  = struct.unpack_from('<H', curr_raw)[0] if curr_raw and len(curr_raw) >= 2 else 0

        return {
            'pos_counts':    pos_raw,
            'speed':         speed,
            'load_pct':      load_pct,
            'voltage_v':     voltage / 10.0,
            'temperature_c': temp,
            'current_ma':    current,
        }

    def change_id(self, current_id: int, new_id: int):
        """Write new ID to EEPROM. Call only with one servo on the bus."""
        self.write_bytes(current_id, _LOCK_ADDR, [0])
        time.sleep(0.1)
        self.write_bytes(current_id, _SERVO_ID_ADDR, [new_id])
        time.sleep(0.1)
        self.write_bytes(new_id, _LOCK_ADDR, [1])