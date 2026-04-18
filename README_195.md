# Project BLUNDR: 6-DOF Autonomous Chess Robot
> A distributed AI-driven robotic system for physical chess gameplay.

![CI Status](https://github.com/SJSU-CMPE-195/group-project-team-19/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-75%25-green)

---

## Team

| Name | GitHub | Email |
|------|--------|-------|
| Andy Lazcano | @Alazca | andy.lazcano@sjsu.edu |
| Adrian Par | @adrianpar1 | Adrian.par@sjsu.edu |
| Philip Figuerres | @PisaFig | philip.figuerres@sjsu.edu |
| Arda Karayan | @DADaBase88 | arda.karayan@sjsu.edu |

**Advisor:** Jun Liu

---

## Problem Statement

While other robotic fields have rapidly advanced, pick-and-place systems remain tightly coupled and overly reliant on deterministic, high-maintenance kinematics. Developing a smarter, adaptable system with minimal configuration will solve these ongoing accuracy and upgradeability limitations.

## Solution

Project BLUNDR solves this by deploying a precision 6-DOF pick-and-place robotic arm designed to autonomously play physical chess against a human opponent . The architecture distributes the compute workload, utilizing a Jetson Nano for computer vision and inverse kinematics, which then sends precise movement commands to a Raspberry Pi that handles the physical servo motor control.

### Key Features

- AI-Driven Vision System: Real-time piece detection and chess game logic processing powered by a Jetson Nano.

- Distributed Architecture & Protocol: A custom serial communication protocol ensuring reliable data transfer between the high-level AI processor and the low-level Raspberry Pi motor controller.

- Custom Ground Control Station: A web-based NiceGUI dashboard providing live coordinate telemetry, Cartesian and Joint-space jogging, dynamic teachpoint memory, and system diagnostics.

---

## Demo

https://drive.google.com/file/d/1UTbnnSRUxdsKaKphtBwa2elWPUMDjW3E/view?usp=sharing

**Live Demo:** https://drive.google.com/file/d/1bCk3d-VIGvpuIWAq40wZlNxnjGsQd002/view?usp=sharing

**Implemention #3 Video and Photo**

**Video Link:** https://drive.google.com/file/d/1BtUN7cK4JLpcRDVsh22IfOT2RAfVONpN/view?usp=drive_link


---

## Engineering Evaluation & Design Iteration

- **Broken Robot Picture
**Photo Link:** https://drive.google.com/file/d/1p-GmkMN5h_E4HDhM3Q8UdOETs0htu-Jo/view?usp=drive_link

<details>
<summary> Following integration testing of the initial prototype, the team identified three critical bottlenecks that necessitated a shift in hardware architecture. </summary>

- **Open-Loop Limitations:** The original PWM servos lacked encoder feedback, creating a deterministic bottleneck where the system could command movement but never verify arrival or handle stalls.

- **VLA/Data Collection Constraints:** Without joint-position feedback, the Jetson Orin could not "record" human-guided demonstrations, making Vision-Language-Action (VLA) training impossible on the current chassis.

- **Power Distribution Instability:** High-resistance jumper modifications for the PDU led to voltage drops and intermittent motor "brown-outs" during high-torque maneuvers.

**Technical Pivot for Expo**

<summary>To resolve these issues for the final Expo, the system is migrating to a "Smart Servo" architecture. </summary>

- **Encoded Hardware:** Migrating to Serial Bus Servos with 12-bit Absolute Encoders. This enables real-time telemetry and "Lead-Through" programming (teaching by physically moving the arm).

- **Full-Duplex Communication:** Transitioning to a TTL Serial Bus protocol. This allows the Raspberry Pi 5 to query each motor for position, temperature, and load status simultaneously.

- **Dedicated PDU:** Implementing a custom Power Distribution PCB to ensure stable 12V delivery to high-load joints (Shoulder/Elbow).

## Handling the CI/CD & Demo

- **CI/CD & Software:** The pipeline and Ground Control Station (GCS) are hardware-agnostic. Successful deployment and stress testing were validated using the SO-100 functional prototype.

- **Simulation vs. Physical:** The GCS features a "Simulation Mode" designed to visualize the intended kinematic state, however the actual physical state, a critical feature for debugging high-DOF systems without encoders.

- **Stress Testing:** The communication layer (UDP over Tailscale) was successfully stress-tested at 20Hz, confirming the Pi 5's ability to handle high-frequency AI vision data regardless of the motor backend.


</details>

---


## Screenshots

| Feature | Screenshot |
|---------|------------|
| Web UI | <img width="1432" height="815" alt="image" src="https://github.com/user-attachments/assets/ae330e57-ca15-404e-ab9c-1b76c988a3e4" /> |
| Web UI2 | <img width="593" height="779" alt="image" src="https://github.com/user-attachments/assets/72807861-7559-4502-9aae-f48a38c66b39" /> |


| Setup| <img width="1094" height="829" alt="image" src="https://github.com/user-attachments/assets/568434ba-f859-42d3-87d8-f50c63b848f7" />
|

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Languages |Python 3.10+, C++ 17 |
| Frameworks |NiceGUI (Frontend), OpenCV (Vision) |
| Communication |UDP Sockets, I2C (PCA9685), Serial |
| Testing |Pytest, Google Test, GitHub Actions (CI/CD) |
| Deployment |Raspberry Pi 5 (Linux), Jetson Nano |

---

## Getting Started

### Prerequisites

- Raspberry Pi OS (Bookworm)

- Python 3.10+

- I2C enabled via raspi-config

### Installation

```bash
# Clone the repository
git clone https://github.com/SJSU-CMPE-195/group-project-team-19.git
cd group-project-team-19 

# Set up virtual environment
python3 -m venv robot_env
source robot_env/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### Running Locally

```bash
# Launch the Ground Control Station
python src/blundr_gcs.py
```

---

## Communication Protocol (UDP)

<details>
<summary> The Jetson Nano communicates with the Raspberry Pi 5 via a custom UDP protocol on Port 5005. </summary>

| Key | Type | Description |
|--------|----------|-------------|
| action | String` | Command type: "move", "home", or "grip" |
| j1 | Float | Target angle for Joint 1 (0.0 to 180.0) |
| speed |Integer | Velocity percentage (10 to 100) |

</details>

---

## Recommended Testing Structure
To fulfill the CMPE 195 testing requirements, we utilize a three-tier testing strategy:

1. **Unit Tests (`tests/unit/`):** Validating individual C++ motion functions and Python UI components.
2. **Integration Tests (`tests/integration/`):** Testing the UDP communication between the Jetson Orin and Raspberry Pi.
3. **Edge Case Tests (`tests/edge_cases/`):** Verifying system behavior during motor stalls, coordinate overflows, and comms loss.

## Evaluation & Stress Testing
We subjected the Pi 5 and I2C bus to a 30-minute high-frequency command stress test.
- **Result:** Successfully handled 12 commands/sec with <1% packet loss.
- **Full Report:** [docs/evaluation/stress-test-results.md](./docs/evaluation/stress-test-results.md)

### Stress Testing
To replicate our performance evaluation results:
1. Ensure the GCS is running (`python src/blundr_gcs.py`)
2. Run the simulation script:
   `python docs/scripts/run_stress_test.py`
3. Performance data can be viewed in [docs/evaluation/stress-test-results.md](./docs/evaluation/stress-test-results.md)

## Hardware Setup
- **Main Brain:** Jetson Orin (Vision / IK)
- **Controller:** Raspberry Pi 5
- **PWM Driver:** SparkFun Pi Servo pHAT (PCA9685)
- **Power:** External 5V 10A DC Power Supply

</details>

---

## Project Structure

```
.
├── .github/workflows/  # CI/CD Pipeline (.yml)
├── include/            # C++ Header files (Interlocks, Motion)
├── src/                # Python/C++ Source code
├── tests/              # Unit, Integration, and Edge Case tests
├── docs/               # Evaluation, Stress tests, Diagrams, and CAD
└── README_195.md
```

---

## Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### Commit Messages

Use clear, descriptive commit messages:
- `Add user authentication endpoint`
- `Fix database connection timeout issue`
- `Update README with setup instructions`

---

## Acknowledgments

- [Resource/Library/Person]
- [Resource/Library/Person]

---

### Hardware Iteration Note (April 2026)

Following initial integration testing, the team identified critical limitations in open-loop PWM control for high-precision chess maneuvers. 

**Current Status:** The software stack (CI/CD, GCS, Comms) is fully validated. The physical hardware is undergoing an upgrade to encoded serial-bus servos to support real-time telemetry and VLA data collection for the final Expo. 

**Validation:** System performance confirmed via SO-100 functional prototype.

---

## License

This project is licensed under the <FILL IN> License - see the [LICENSE](LICENSE) file for details.

---

*CMPE 195A/B - Senior Design Project | San Jose State University | Spring 2026*
