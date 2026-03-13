#pragma once

#include <cstdint>
#include <functional>
#include <queue>
#include <string>
#include <vector>

/**
 * @enum CommandType
 * @brief types of commands from jetson
 */
enum class CommandType {
	UNKNOWN,
	MOVE_JOINT,
	MOVE_CARTESIAN,
	GRIPPER_CONTROL,
	GET_STATUS,
	EMERGENCY_STOP,
	RESET_FAULT,
	CALIBRATE
};

/**
 * @struct Command
 * @brief parsed command structure
 */
struct Command {
	CommandType type;
	std::string joint;
	float position;
	float speed;
	float x, y, z; // For cartesian commands
	bool gripperOpen;
	uint32_t timestamp;
};

/**
 * @struct RobotStatus
 * @brief current robot status for reporting
 */
struct RobotStatus {
	std::string state; // "idle", "moving", "fault", "estop"
	struct JointStatus {
		std::string name;
		float position;
		float velocity;
		bool atTarget;
	};
	std::vector<JointStatus> joints;
	std::string faultMsg;
};

/**
 * @class SerialUSBManager
 * @brief manages serial communication with jetson orin nano
 *
 * handles json parsing, command queueing, and status reporting.
 * non-blocking operation suitable for real-time control loop.
 */
class SerialUSBManager {
public:
	/**
	 * @brief constructor
	 * @param device serial device path (e.g., "/dev/ttyUSB0")
	 * @param baudrate baud rate (typically 115200 or 921600)
	 */
	SerialUSBManager(
		const std::string& device = "/dev/ttyUSB0", uint32_t baudrate = 115200
	);

	/**
	 * @brief destructor
	 */
	~SerialUSBManager();

	/**
	 * @brief initialize serial port
	 * @return true if successful
	 */
	bool initialize();

	/**
	 * @brief update function - call in main loop
	 * checks for incoming data, parses commands
	 * @return number of commands received this update
	 */
	uint32_t update();

	/**
	 * @brief check if command is available
	 * @return true if command is in queue
	 */
	bool hasCommand() const;

	/**
	 * @brief get next command from queue
	 * @param cmd reference to command struct to fill
	 * @return true if command was retrieved
	 */
	bool getCommand(Command& cmd);

	/**
	 * @brief send status update to jetson
	 * @param status robotstatus structure
	 */
	void sendStatus(const RobotStatus& status);

	/**
	 * @brief send acknowledgment response
	 * @param success true for success, false for error
	 * @param message optional message string
	 */
	void sendAck(bool success, const std::string& message = "");

	/**
	 * @brief send raw json string
	 * @param json json string to send
	 */
	void sendJSON(const std::string& json);

	/**
	 * @brief check if serial connection is active
	 * @return true if connected
	 */
	bool isConnected() const {
		return connected_;
	}

	/**
	 * @brief get number of bytes available to read
	 * @return bytes available
	 */
	uint32_t bytesAvailable() const;

	/**
	 * @brief register callback for incoming commands
	 * @param callback function to call when command received
	 */
	void onCommand(std::function<void(const Command&)> callback) {
		commandCallback_ = callback;
	}

	/**
	 * @brief enable debug logging
	 * @param enable true to enable debug prints
	 */
	void setDebug(bool enable) {
		debug_ = enable;
	}

private:
	// configuration
	std::string device_;
	uint32_t baudrate_;
	int serialFd_;
	bool connected_;
	bool debug_;

	// receive buffer
	std::string receiveBuffer_;
	std::queue<Command> commandQueue_;

	// callback
	std::function<void(const Command&)> commandCallback_;

	// helper methods
	bool openPort();
	void closePort();
	void processIncomingData();
	bool parseJSON(const std::string& jsonStr, Command& cmd);
	std::string buildStatusJSON(const RobotStatus& status);
	void logDebug(const std::string& message);

	// constants
	static constexpr size_t MAX_BUFFER_SIZE = 4096;
	static constexpr size_t MAX_QUEUE_SIZE = 32;
};
