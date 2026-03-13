#pragma once

#include <cstdint>
#include <mutex>
#include <string>

class ServoControl {
public:
	enum class ServoChannel : uint8_t {
		BASE = 0,
		SHOULDER = 1,
		ELBOW = 2,
		WRIST_PITCH = 3,
		WRIST_ROLL = 4,
		WRIST_YAW = 5,
		GRIPPER = 6,
		CHESS_CLOCK = 7
	};

	ServoControl(
		const std::string& i2cDevice = "/dev/i2c-1", uint8_t address = 0x40
	);

	virtual ~ServoControl() = default;

	void setPWM(float freq_hz);

	void setPWMChannel(uint8_t channel, uint16_t& start, uint16_t& stop);

	// Set pulses in micro seconds
	void setServoPulse_us(uint8_t channel, float pulse_us, float freq_hz);
	void setServoAngle(
		uint8_t channel, float angle, float min_pulse_us = 1000.0f,
		float max_pulse_us = 2000.0f
	);

	void setAllJointAngles(const std::array<float, 7>& targetAngles);
	float getCurrentFreq() const;
	void setCurrentFreq(float freq_hz) const;

	void emergencyStop();
	void shutdown();
	void enable();
	void reset();
	void sleep();
	void wake();

private:
	// From sparkfun datasheet 7.3 Register Definitions
	static constexpr uint8_t MODE1 = 0x00;
	static constexpr uint8_t MODE2 = 0x01;
	static constexpr uint8_t SUBADR1 = 0x02;
	static constexpr uint8_t SUBADR2 = 0x03;
	static constexpr uint8_t SUBADR3 = 0x04;
	static constexpr uint8_t PRESCALE = 0xFE;

	static constexpr uint8_t LED0_ON_L = 0x06;
	static constexpr uint8_t LED0_ON_H = 0x07;
	static constexpr uint8_t LED0_OFF_L = 0x08;
	static constexpr uint8_t LED0_OFF_H = 0x09;

	static constexpr uint8_t ALL_LED_ON_L = 0xFA;
	static constexpr uint8_t ALL_LED_ON_H = 0xFB;
	static constexpr uint8_t ALL_LED_OFF_L = 0xFC;
	static constexpr uint8_t ALL_LED_OFF_H = 0xFD;

	static constexpr uint8_t RESTART = 0x80;
	static constexpr uint8_t SLEEP_BIT = 0x10;
	static constexpr uint8_t ALLCALL = 0x01;
	static constexpr uint8_t INVERT = 0x10;
	static constexpr uint8_t OUTDRV = 0x04;
	static constexpr uint8_t NUM_CHANNELS = 16;
	static constexpr uint16_t PWM_RESOLUTION = 4096;
	static constexpr float DEFAULT_FREQ_HZ = 50.0f;

	float currentFreqHz;
	int file;
	uint8_t addressI2C;
	void write8(uint8_t reg, uint8_t value);
	uint8_t read8(uint8_t reg);

	void setError();
	std::mutex busLock;
};
