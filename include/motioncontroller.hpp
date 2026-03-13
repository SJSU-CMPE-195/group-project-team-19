#pragma once
#include "servocontroller.hpp"
#include "trajectplanner.hpp"
#include <chrono>

class MotionController {
public:
	void moveToPosition();
	void moveAlongPath();
	void emergencyStop();
	void startMove();
	void pauseMove();
	void resumeMove();
	bool isMoveComplete() const;
};
