#pragma once
#include <cstdint>

namespace dsd {
namespace central {

struct ArmToken {
    std::uint64_t boot_session;
    std::uint64_t stop_generation;
};

// Adapter supplies debounced button state and one-cycle, validated events.
// Freshness, zero-command validation and link timeouts belong to the adapter.
struct ArmInputs {
    bool estop_loop_ok = false;
    bool links_ok = false;  // GUI, three drive MCUs and odometry; not C620 power.
    bool other_fault = true;
    bool command_zero = false;
    bool stop_request = false;
    bool button_pressed = false;
    bool gui_arm_event = false;
    ArmToken gui_token = {};
    std::uint64_t gui_sequence = 0;
    bool run_event = false;
    ArmToken run_token = {};
    // Strictly increasing motion-message sequence, including zero commands.
    std::uint64_t motion_sequence = 0;
};

struct ArmOutputs {
    bool motor_power_enable = false;
    bool motion_permitted = false;
    bool arm_accepted = false;
    bool arm_rejected = false;
    ArmToken token = {};
};

class ArmController {
public:
    // Nonzero session must be unique on every MCU boot/GUI reconnect.
    explicit ArmController(std::uint64_t boot_session);
    ArmOutputs update(const ArmInputs &input);
private:
    ArmToken token_;
    bool blocked_ = true;
    bool armed_ = false;
    bool running_ = false;
    bool button_released_ = false;
    std::uint64_t last_gui_sequence_ = 0;
    std::uint64_t last_motion_sequence_ = 0;
};

}  // namespace central
}  // namespace dsd
