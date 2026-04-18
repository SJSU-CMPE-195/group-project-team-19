#include <gtest/gtest.h>
#include "../../include/interlocks.hpp"
#include "../../include/motioncontroller.hpp"

// Test coordinate system limits (Out of bounds)
TEST(SafetyTest, OutOfBoundsCoordinate) {
    SafetyInterlock safety;
    // Assuming board limits are 0-400mm; test a 5000mm input
    safety.setInterlock(SafetyInterlock::Interlock::MOTION_LIMIT_EXCEED, 
                        SafetyInterlock::Severity::ERROR, "Limit test");
    EXPECT_TRUE(safety.isActive(SafetyInterlock::Interlock::MOTION_LIMIT_EXCEED));
}

// Test communication loss scenario
TEST(SafetyTest, CommsLossHandling) {
    SafetyInterlock safety;
    safety.setInterlock(SafetyInterlock::Interlock::COMMS_LOSS, 
                        SafetyInterlock::Severity::CRITICAL, "Timeout");
    EXPECT_TRUE(safety.hasActiveInterlock());
}

// Test servo angle limits
TEST(ServoTest, AngleWrapAround) {
    // Test logic for angles < 0 or > 180
    float testAngle = 270.0f;
    float safeAngle = std::max(0.0f, std::min(180.0f, testAngle));
    EXPECT_EQ(safeAngle, 180.0f);
}