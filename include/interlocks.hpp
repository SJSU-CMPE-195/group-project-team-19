#pragma once
#include <string>

class SafetyInterlock {
public:
	enum class Interlock {
		EMERGENCY_STOP,
		MOTION_LIMIT_EXCEED,
		CURRENT_OVERLOAD,
		COMMS_LOSS,
		VISISON_FAULT,
		COLLISION_DETECTED,
		HIGH_TEMP,
		VOLT_FAULT,
		POSITION_ERROR
	};

	enum class Severity {
		WARNING,
		ERROR,
		FAULT,
		CRITICAL
	};

	SafetyInterlock();
	virtual ~SafetyInterlock() = default;

	void setInterlock(
		Interlock interlock, Severity severity, const std::string& description
	);
};
