from nicegui import ui
import cv2
import base64
import socket
import json
import threading

# ==========================================
# HARDWARE SETUP (SparkFun Pi Servo pHAT)
# ==========================================
try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo

    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50
    hardware_servos = {'j1': servo.Servo(pca.channels[0]), 'grip': servo.Servo(pca.channels[5])}
    HARDWARE_ONLINE = True
except Exception:
    HARDWARE_ONLINE = False

# ==========================================
# STATE & ORIN COMMS SETUP
# ==========================================
robot_pos = {'x': 0, 'y': 0, 'z': 0, 'j1': 90, 'j2': 90, 'j3': 90, 'j4': 90, 'j5': 90, 'grip': 90}
saved_points = {}
orin_status = {"online": False, "last_seen": 0}

# UDP Config: Pi listens on Port 5005
UDP_IP = "0.0.0.0" # Listen on all network interfaces
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(1.0) # Don't block forever

# ==========================================
# BACKGROUND ORIN LISTENER
# ==========================================
def orin_listener():
    global robot_pos
    while True:
        try:
            data, addr = sock.recvfrom(1024) # Buffer size 1024 bytes
            message = json.loads(data.decode())
            
            # Update Status
            orin_status["online"] = True
            
            # If Orin sends a move command: {"j1": 45, "action": "move"}
            if "j1" in message:
                robot_pos['j1'] = message['j1']
                update_hardware()
                update_displays()
                
        except socket.timeout:
            orin_status["online"] = False
        except Exception as e:
            print(f"UDP Error: {e}")

# Start the listener in a separate thread so it doesn't freeze the UI
threading.Thread(target=orin_listener, daemon=True).start()

# ==========================================
# UI & MOVEMENT LOGIC
# ==========================================
def update_hardware():
    if HARDWARE_ONLINE:
        hardware_servos['j1'].angle = max(0, min(180, robot_pos['j1']))

def update_displays():
    lbl_joint_pos.set_text(f"J1: {int(robot_pos['j1'])}° | J2: {int(robot_pos['j2'])}° | J3: {int(robot_pos['j3'])}°")
    # Update AI status in header
    lbl_nano_status.set_text(f'Nano [AI]: {"ONLINE" if orin_status["online"] else "OFFLINE"}')
    lbl_nano_status.classes(replace='text-green-400' if orin_status['online'] else 'text-red-400')

ui.timer(0.5, update_displays)

# (All your other Jog/Teachpoint functions remain the same as previous)

# ==========================================
# UI LAYOUT
# ==========================================
with ui.header().classes('bg-slate-900 items-center justify-between p-4'):
    ui.label('Blundr Ground Control').classes('text-2xl font-bold text-blue-400')
    with ui.row().classes('gap-4 font-mono'):
        lbl_nano_status = ui.label('Nano [AI]: OFFLINE').classes('text-red-400 font-bold')
        ui.label(f'Pi [Control]: {"ONLINE" if HARDWARE_ONLINE else "SIMULATION"}').classes('text-green-400 font-bold' if HARDWARE_ONLINE else 'text-yellow-400')

# ... (Rest of the UI layout: Camera, Cards, Tabs, etc.)
# (Keep your camera feed and grid sections exactly as they were)

ui.run(title="Blundr GCS", host='0.0.0.0', port=8080)