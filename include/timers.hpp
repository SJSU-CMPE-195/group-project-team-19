#pragma once

class SafetyTimer {
public:
	SafetyTimer();
	void startWatchdog(float timeout_sec);
	void resetWatchdog();
	void stopWatchdog();

	bool isWatchdogActive() const;
	void setMotionTimeout();
	void startMotionTimer();
	void stopMotionTimer();
	float getMotionTimerElapsed();
	void update();

private:
	bool watchdogActive;
	float watchdogTimeoutSec;
	bool motionTimerActive;
	float motionTimeoutSec;
};
