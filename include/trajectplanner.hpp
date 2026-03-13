#pragma once
#include <array>
#include <cstdint>
#include <vector>

class TrajectoryPlanner {
public:
	static constexpr size_t NUM_JOINTS = 6;

	struct Traj_Point {
		float position;
		float velocity;
		float accel;
		float time;
	};

	// TRAPEZOIDAL = fast , CUBIC = smooth
	enum class Traj_Profile {
		TRAPEZOIDAL,
		CUBIC
	};

	struct MultiAxisPoint {
		std::array<float, NUM_JOINTS> positions;
		std::array<float, NUM_JOINTS> velocities;
		std::array<float, NUM_JOINTS> accels;
		float time;
	};

	// Removed jerk but if needed again, float max_jerk = 2000.0f
	TrajectoryPlanner(
		float max_veloctiy = 180.0f, float max_accel = 360.0f,
		float updateRate = 100.0f
	);

	void setMaxVelocity(float max_vel);
	void setMaxAccel(float max_accel);
	// void setMaxJerk(float max_jerk);
	void setUpdateRate(float rate_hz);
	float
	calculateDuration(float distance, float max_vel, float max_accel) const;
	bool isPossible(float start_pos, float end_pos, float duration_sec) const;

private:
	// for RDS51160-24V servos, these are default
	float maxVelocity; // 220.0f deg/s
	float maxAccel;	   // 500.0f deg/s^2
	// float maxJerk;     // 2000.0f deg/s^3
	float updateRate; // 100.0f Hz

	struct TrapezoidalSegments {
		float accel_time;
		float cruise_time;
		float decel_time;
		float cruise_vel;
	};

	TrapezoidalSegments
	calculateTrapSegments(float distance, float max_vel, float max_accel) const;
};
