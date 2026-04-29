# ── STS/SMS register addresses ──────────────────────────────────────────────
_TORQUE_ENABLE     = 40
_GOAL_POSITION_L   = 42
_GOAL_SPEED_L      = 46   # Goal Speed register (RAM); 0 = max speed / no limit
_TORQUE_LIMIT_L    = 48   # Torque Limit register (RAM, 2 bytes LE)
                          # 0..1000 scale where 1000 = 100% of rated torque.
                          # RAM means it resets on power-cycle — Apply must be
                          # re-run on reconnect. This is intentional: a faulty
                          # config can be cleared by power-cycling the bus.
_DEFAULT_SPEED     = 1000
_PRESENT_POS_L     = 56   # 2 bytes
_PRESENT_SPEED_L   = 58   # 2 bytes
_PRESENT_LOAD_L    = 60   # 2 bytes
_PRESENT_VOLTAGE   = 62   # 1 byte
_PRESENT_TEMP      = 63   # 1 byte
_PRESENT_CURRENT_L = 69   # 2 bytes
_SERVO_ID_ADDR     = 5    # ID register (EEPROM)
_LOCK_ADDR         = 55   # EEPROM lock register

_COUNTS        = 4096
_DEG_PER_COUNT = 360.0 / _COUNTS
_COUNT_PER_DEG = _COUNTS / 360.0

_MAX_GOAL_SPEED = 32767   # Goal Speed register: positive half of signed 16-bit

_BAUD_OPTIONS  = [1_000_000, 500_000, 250_000, 115_200, 57_600]
_DEFAULT_BAUD  = 1_000_000
_TELEMETRY_MS  = 350
_DEFAULT_NUDGE = 5.0

_DEFAULT_MAX_LOAD_PCT   = 80.0
_DEFAULT_MAX_CURRENT_MA = 1500
_DEFAULT_MAX_TEMP_C     = 70

# Torque limit scaling for STS3215 (rated 50 kg-cm, hard ceiling 45 kg-cm).
# Per-joint defaults reflect the load each link actually carries; base/wrist
# stages get more headroom than the wrist+gripper stages downstream.
_TORQUE_LIMIT_L_REG       = _TORQUE_LIMIT_L  # alias for clarity in SafetyPanel
_SERVO_RATED_KGCM         = 50.0
_TORQUE_HARD_CEILING_KGCM = 45.0
_DEFAULT_TORQUE_KGCM = {
    "Pan":     40.0,
    "Tilt":    40.0,
    "Joint 3": 40.0,
    "Joint 4": 30.0,
    "Joint 5": 25.0,
}
_DEFAULT_TORQUE_FALLBACK_KGCM = 40.0

# Default labels for the 5 servo panels (3 columns × 2 rows, last cell empty)
_DEFAULT_LABELS = ["Pan", "Tilt", "Joint 3", "Joint 4", "Joint 5"]
_NUM_SERVOS    = len(_DEFAULT_LABELS)
_GRID_COLS     = 3
_GRID_ROWS     = 2