# Project Title

> One-line description of what your project does

## Team

| Name | GitHub | Email |
|------|--------|-------|
| Andy Lazcano | @Alazca | andy.lazcano@sjsu.edu |
| Adrian Par | [@adrianpar1 | Adrian.par@sjsu.edu |
| Philip Figuerres | @PisaFig | philip.figuerres@sjsu.edu |
| Arda Karayan | @DADaBase88 | arda.karayan@sjsu.edu |

**Advisor:** Jun Liu

---

## Problem Statement

Creating autonomous systems that physically interact with dynamic environments requires seamlessly bridging complex artificial intelligence software with low-level mechanical hardware. This project tackles that integration challenge by building a system that must visually interpret a changing game state, calculate complex spatial coordinates, and execute precise physical manipulations without human intervention.

## Solution

Project BLUNDR solves this by deploying a precision 6-DOF pick-and-place robotic arm designed to autonomously play physical chess against a human opponent . The architecture distributes the compute workload, utilizing a Jetson Nano for computer vision and inverse kinematics, which then sends precise movement commands to a Raspberry Pi that handles the physical servo motor control.

### Key Features

- AI-Driven Vision System: Real-time piece detection and chess game logic processing powered by a Jetson Nano.

- Distributed Architecture & Protocol: A custom serial communication protocol ensuring reliable data transfer between the high-level AI processor and the low-level Raspberry Pi motor controller.

- Custom Ground Control Station: A web-based NiceGUI dashboard providing live coordinate telemetry, Cartesian and Joint-space jogging, dynamic teachpoint memory, and system diagnostics.

---

## Demo

[Link to demo video or GIF]

**Live Demo:** [URL if deployed]

---

## Screenshots

| Feature | Screenshot |
|---------|------------|
| [Feature 1] | ![Screenshot](docs/screenshots/feature1.png) |
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
