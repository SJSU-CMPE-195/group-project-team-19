# Project Title

> One-line description of what your project does

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

**Live Demo:** [URL if deployed]

---

## Screenshots

| Feature | Screenshot |
|---------|------------|
| Web UI | <img width="1432" height="815" alt="image" src="https://github.com/user-attachments/assets/ae330e57-ca15-404e-ab9c-1b76c988a3e4" /> |
| Web UI2 | <img width="593" height="779" alt="image" src="https://github.com/user-attachments/assets/72807861-7559-4502-9aae-f48a38c66b39" /> |


| [Feature 2] | ![Screenshot](docs/screenshots/feature2.png) |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Frontend | |
| Backend | |
| Database | |
| Deployment | |

---

## Getting Started

### Prerequisites

- [Prerequisite 1] v.X.X+
- [Prerequisite 2] v.X.X+

### Installation

```bash
# Clone the repository
git clone https://github.com/[org]/[repo].git
cd [repo]

# Install dependencies
[install command]

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run database migrations (if applicable)
[migration command]
```

### Running Locally

```bash
# Development mode
[dev command]

# The app will be available at http://localhost:XXXX
```

### Running Tests

```bash
[test command]
```

---

## API Reference

<details>
<summary>Click to expand API endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/resource` | Get all resources |
| GET | `/api/resource/:id` | Get resource by ID |
| POST | `/api/resource` | Create new resource |
| PUT | `/api/resource/:id` | Update resource |
| DELETE | `/api/resource/:id` | Delete resource |

</details>

---

## Project Structure

```
.
├── [folder]/           # Description
├── src/                # Source code files
├── tests/              # Test files
├── docs/               # Documentation files
└── README.md
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

## License

This project is licensed under the <FILL IN> License - see the [LICENSE](LICENSE) file for details.

---

*CMPE 195A/B - Senior Design Project | San Jose State University | Spring 2026*
