#include "serialmanager.hpp"
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <sstream>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

SerialUSBManager::SerialUSBManager(const std::string& device, uint32_t baudrate)
	: device_(device), baudrate_(baudrate), serialFd_(-1), connected_(false),
	  debug_(true) {
}

SerialUSBManager::~SerialUSBManager() {
	closePort();
}

bool SerialUSBManager::initialize() {
	std::cout << "[SerialUSB] Initializing..." << std::endl;
	std::cout << "  Device: " << device_ << std::endl;
	std::cout << "  Baudrate: " << baudrate_ << std::endl;

	return openPort();
}

bool SerialUSBManager::openPort() {
	// open serial port
	serialFd_ = open(device_.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);

	if (serialFd_ < 0) {
		std::cerr << "[SerialUSB] Failed to open " << device_ << std::endl;
		return false;
	}

	// configure serial port
	struct termios tty;
	if (tcgetattr(serialFd_, &tty) != 0) {
		std::cerr << "[SerialUSB] Failed to get serial attributes" << std::endl;
		close(serialFd_);
		serialFd_ = -1;
		return false;
	}

	// set baud rate
	speed_t speed;
	switch (baudrate_) {
	case 9600:
		speed = B9600;
		break;
	case 19200:
		speed = B19200;
		break;
	case 38400:
		speed = B38400;
		break;
	case 57600:
		speed = B57600;
		break;
	case 115200:
		speed = B115200;
		break;
	case 230400:
		speed = B230400;
		break;
	case 460800:
		speed = B460800;
		break;
	case 921600:
		speed = B921600;
		break;
	default:
		speed = B115200;
		break;
	}

	cfsetospeed(&tty, speed);
	cfsetispeed(&tty, speed);

	// 8n1 mode
	tty.c_cflag &= ~PARENB; // no parity
	tty.c_cflag &= ~CSTOPB; // 1 stop bit
	tty.c_cflag &= ~CSIZE;
	tty.c_cflag |= CS8;			   // 8 bits per byte
	tty.c_cflag &= ~CRTSCTS;	   // no hardware flow control
	tty.c_cflag |= CREAD | CLOCAL; // enable receiver, ignore modem control

	// raw mode
	tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
	tty.c_iflag &= ~(IXON | IXOFF | IXANY);
	tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL);
	tty.c_oflag &= ~OPOST;

	// non-blocking read
	tty.c_cc[VMIN] = 0;
	tty.c_cc[VTIME] = 0;

	// apply settings
	if (tcsetattr(serialFd_, TCSANOW, &tty) != 0) {
		std::cerr << "[SerialUSB] Failed to set serial attributes" << std::endl;
		close(serialFd_);
		serialFd_ = -1;
		return false;
	}

	connected_ = true;
	std::cout << "[SerialUSB] Connected successfully" << std::endl;

	return true;
}

void SerialUSBManager::closePort() {
	if (serialFd_ >= 0) {
		close(serialFd_);
		serialFd_ = -1;
		connected_ = false;
		std::cout << "[SerialUSB] Port closed" << std::endl;
	}
}

uint32_t SerialUSBManager::update() {
	if (!connected_)
		return 0;

	processIncomingData();

	return commandQueue_.size();
}

void SerialUSBManager::processIncomingData() {
	char buffer[256];
	ssize_t bytesRead = read(serialFd_, buffer, sizeof(buffer) - 1);

	if (bytesRead > 0) {
		buffer[bytesRead] = '\0';
		receiveBuffer_ += std::string(buffer);

		// look for complete json messages (terminated by newline)
		size_t pos;
		while ((pos = receiveBuffer_.find('\n')) != std::string::npos) {
			std::string jsonStr = receiveBuffer_.substr(0, pos);
			receiveBuffer_.erase(0, pos + 1);

			if (!jsonStr.empty()) {
				logDebug("Received: " + jsonStr);

				Command cmd;
				if (parseJSON(jsonStr, cmd)) {
					if (commandQueue_.size() < MAX_QUEUE_SIZE) {
						commandQueue_.push(cmd);

						if (commandCallback_) {
							commandCallback_(cmd);
						}
					} else {
						std::cerr << "[SerialUSB] Command queue full!"
								  << std::endl;
					}
				}
			}
		}

		// prevent buffer overflow
		if (receiveBuffer_.size() > MAX_BUFFER_SIZE) {
			std::cerr << "[SerialUSB] Buffer overflow - clearing" << std::endl;
			receiveBuffer_.clear();
		}
	}
}

bool SerialUSBManager::parseJSON(const std::string& jsonStr, Command& cmd) {
	// simple json parser (for production, use nlohmann/json or similar)
	// this is a basic implementation for demonstration

	cmd.type = CommandType::UNKNOWN;
	cmd.timestamp = 0;

	// extract command type
	size_t cmdPos = jsonStr.find("\"cmd\"");
	if (cmdPos != std::string::npos) {
		size_t colonPos = jsonStr.find(":", cmdPos);
		size_t quotePos1 = jsonStr.find("\"", colonPos);
		size_t quotePos2 = jsonStr.find("\"", quotePos1 + 1);

		if (quotePos1 != std::string::npos && quotePos2 != std::string::npos) {
			std::string cmdType =
				jsonStr.substr(quotePos1 + 1, quotePos2 - quotePos1 - 1);

			if (cmdType == "move") {
				cmd.type = CommandType::MOVE_JOINT;
			} else if (cmdType == "move_cart") {
				cmd.type = CommandType::MOVE_CARTESIAN;
			} else if (cmdType == "gripper") {
				cmd.type = CommandType::GRIPPER_CONTROL;
			} else if (cmdType == "status") {
				cmd.type = CommandType::GET_STATUS;
			} else if (cmdType == "estop") {
				cmd.type = CommandType::EMERGENCY_STOP;
			} else if (cmdType == "reset") {
				cmd.type = CommandType::RESET_FAULT;
			} else if (cmdType == "calibrate") {
				cmd.type = CommandType::CALIBRATE;
			}
		}
	}

	// extract joint name (if present)
	size_t jointPos = jsonStr.find("\"joint\"");
	if (jointPos != std::string::npos) {
		size_t colonPos = jsonStr.find(":", jointPos);
		size_t quotePos1 = jsonStr.find("\"", colonPos);
		size_t quotePos2 = jsonStr.find("\"", quotePos1 + 1);

		if (quotePos1 != std::string::npos && quotePos2 != std::string::npos) {
			cmd.joint =
				jsonStr.substr(quotePos1 + 1, quotePos2 - quotePos1 - 1);
		}
	}

	// extract numeric values (position, speed, etc.)
	size_t posPos = jsonStr.find("\"position\"");
	if (posPos != std::string::npos) {
		size_t colonPos = jsonStr.find(":", posPos);
		cmd.position = std::stof(jsonStr.substr(colonPos + 1));
	}

	size_t speedPos = jsonStr.find("\"speed\"");
	if (speedPos != std::string::npos) {
		size_t colonPos = jsonStr.find(":", speedPos);
		cmd.speed = std::stof(jsonStr.substr(colonPos + 1));
	}

	return (cmd.type != CommandType::UNKNOWN);
}

bool SerialUSBManager::hasCommand() const {
	return !commandQueue_.empty();
}

bool SerialUSBManager::getCommand(Command& cmd) {
	if (commandQueue_.empty()) {
		return false;
	}

	cmd = commandQueue_.front();
	commandQueue_.pop();
	return true;
}

void SerialUSBManager::sendStatus(const RobotStatus& status) {
	if (!connected_)
		return;

	std::string json = buildStatusJSON(status);
	sendJSON(json);
}

void SerialUSBManager::sendAck(bool success, const std::string& message) {
	std::ostringstream oss;
	oss << "{\"status\":\"" << (success ? "ok" : "error") << "\"";
	if (!message.empty()) {
		oss << ",\"msg\":\"" << message << "\"";
	}
	oss << "}\n";

	sendJSON(oss.str());
}

void SerialUSBManager::sendJSON(const std::string& json) {
	if (!connected_)
		return;

	std::string msg = json;
	if (msg.back() != '\n') {
		msg += '\n';
	}

	ssize_t written = write(serialFd_, msg.c_str(), msg.length());

	if (written < 0) {
		std::cerr << "[SerialUSB] Write error" << std::endl;
	} else {
		logDebug("Sent: " + msg);
	}
}

uint32_t SerialUSBManager::bytesAvailable() const {
	if (!connected_)
		return 0;

	int bytes;
	ioctl(serialFd_, FIONREAD, &bytes);
	return bytes;
}

std::string SerialUSBManager::buildStatusJSON(const RobotStatus& status) {
	std::ostringstream oss;
	oss << "{\"state\":\"" << status.state << "\",\"joints\":{";

	for (size_t i = 0; i < status.joints.size(); i++) {
		const auto& joint = status.joints[i];
		if (i > 0)
			oss << ",";
		oss << "\"" << joint.name << "\":{" << "\"pos\":" << joint.position
			<< ","
			<< "\"vel\":" << joint.velocity << ","
			<< "\"atTarget\":" << (joint.atTarget ? "true" : "false") << "}";
	}

	oss << "}";

	if (!status.faultMsg.empty()) {
		oss << ",\"fault\":\"" << status.faultMsg << "\"";
	}

	oss << "}\n";

	return oss.str();
}

void SerialUSBManager::logDebug(const std::string& message) {
	if (debug_) {
		std::cout << "[SerialUSB] " << message << std::endl;
	}
}
