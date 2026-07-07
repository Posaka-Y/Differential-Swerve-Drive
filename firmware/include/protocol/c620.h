#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "platform/fdcan.h"

typedef struct {
    uint8_t motor_id;
    uint16_t rotor_angle; /* 0-8191 */
    int16_t rpm; /* Motor rotor rpm before the M3508's 19:1 internal reduction. */
    int16_t torque_current;
    uint8_t temperature_c;
} c620_feedback_t;

/* Decodes standard data frames 0x201-0x208 with DLC 8. */
bool c620_decode_feedback(const fdcan_frame_t *frame, c620_feedback_t *feedback);

/* Builds the 0x200 command for motor IDs 1-4. Values are -16384..16384. */
void c620_make_current_command(fdcan_frame_t *frame, int16_t motor1,
                               int16_t motor2, int16_t motor3,
                               int16_t motor4);
