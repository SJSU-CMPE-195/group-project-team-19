#pragma once
#include <chrono>
#include <string>

class SafetyInterlock {
public:
	enum class Interlock {
		EMERGENCY_STOP,
		MOTION_LIMIT_EXCEED,
		CURRENT_OVERLOAD,
		COMMS_LOSS,
		VISION_FAULT,
		COLLISION_DETECTED,
		HIGH_TEMP,
		VOLT_FAULT,
		POSITION_ERROR,
		COUNT
	};

	// counts number of interlock types in case needed
	static constexpr size_t INTERLOCK_COUNT =
		static_cast<size_t>(Interlock::COUNT);

	enum class Severity {
		NONE = 0,
		WARNING,
		ERROR,
		FAULT,
		CRITICAL
	};

	struct Event {
		Interlock type = Interlock::COUNT;
		Severity severity = Severity::NONE;
		std::string description;
		std::chrono::steady_clock::time_point timestamp;
		bool acknowledged = false;

		// None zero test for alarm matrix, only true when alarm active
		explicit operator bool() const noexcept {
			return severity != Severity::NONE;
		}
	};

	SafetyInterlock();
	virtual ~SafetyInterlock() = default;

	void setInterlock(
		Interlock interlock, Severity severity, const std::string& description
	);

	bool acknowledge(Interlock interlock);
	void reset();
	bool hasActiveInterlock() const;
	// used for array matrixj
	bool isActive(Interlock interlock) const;
	// readable messages
	static const char* interlockToString(Interlock interlock);
	static const char* severityToString(Severity severity);
};
