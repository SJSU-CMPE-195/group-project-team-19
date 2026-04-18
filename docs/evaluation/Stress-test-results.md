## Stress Test Results

### Test Configuration
- **Tool:** Manual load simulation and custom Python script
- **Duration:** 30 minutes continuous cycling
- **Conditions:** 100 move commands per minute via UDP
- **Target:** Raspberry Pi 5 / PCA9685 I2C Bus

### Results
| Metric | Value |
| :--- | :--- |
| Avg Response Time (Command to Motion) | 45 ms |
| 95th Percentile | 82 ms |
| Commands per Second (Peak) | 12 cmd/s |
| Error Rate | 0.2% (Dropped UDP Packets) |

### Observations
- **What did you learn?** The I2C bus remains stable at high frequencies, but the Python UI frame rate drops if UDP packet frequency exceeds 20Hz.
- **Where are the bottlenecks?** The main bottleneck is the single-threaded nature of the servo update loop when handling high-speed vision data.
- **What would you optimize?** Moving the I2C writes to a dedicated high-priority C++ thread to decouple hardware motion from the UI rendering.