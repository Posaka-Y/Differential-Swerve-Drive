#include "control/arm_controller.h"
#include <limits>

namespace dsd {
namespace central {
namespace {
bool matches(ArmToken a, ArmToken b) {
    return a.boot_session != 0 && a.boot_session == b.boot_session &&
           a.stop_generation == b.stop_generation;
}
}

ArmController::ArmController(std::uint64_t session) : token_{session, 1} {}

ArmOutputs ArmController::update(const ArmInputs &in) {
    const bool blocked = token_.boot_session == 0 || !in.estop_loop_ok ||
                         !in.links_ok || in.other_fault || in.stop_request;
    if (blocked && !blocked_) {
        if (token_.stop_generation == std::numeric_limits<std::uint64_t>::max()) {
            token_.boot_session = 0;  // Fail closed on counter exhaustion.
        } else {
            ++token_.stop_generation;
        }
    }
    blocked_ = blocked;
    ArmOutputs out;
    if (blocked) {
        armed_ = false;
        running_ = false;
        button_released_ = false;
    }

    const bool safe_to_arm = !blocked && in.command_zero;
    const bool button_event = safe_to_arm && in.button_pressed && button_released_;
    // An early/held press is consumed; release must occur while ready to arm.
    button_released_ = safe_to_arm && !in.button_pressed;
    bool gui_event = false;
    if (in.gui_arm_event) {
        gui_event = matches(in.gui_token, token_) &&
                    in.gui_sequence > last_gui_sequence_;
        if (matches(in.gui_token, token_) && in.gui_sequence > last_gui_sequence_) {
            last_gui_sequence_ = in.gui_sequence;
        }
    }
    const bool new_motion = in.motion_sequence > last_motion_sequence_;
    // Capture every observed sequence, including commands received before ARM.
    if (new_motion) last_motion_sequence_ = in.motion_sequence;
    if (button_event || in.gui_arm_event) {
        if (!armed_ && safe_to_arm && (button_event || gui_event)) {
            armed_ = true;
            running_ = false;
            out.arm_accepted = true;
        } else {
            out.arm_rejected = true;
        }
    }
    // Never start movement in the same cycle as ARM, or from an old command.
    if (armed_ && !out.arm_accepted && in.run_event && new_motion &&
        matches(in.run_token, token_)) {
        running_ = true;
    }
    out.motor_power_enable = armed_ && !blocked;
    out.motion_permitted = out.motor_power_enable && running_;
    out.token = token_;
    return out;
}

}  // namespace central
}  // namespace dsd
