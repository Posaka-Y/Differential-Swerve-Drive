#include "protocol/c620.h"

static uint16_t read_u16_be(const uint8_t *data)
{
    return ((uint16_t)data[0] << 8U) | data[1];
}

bool c620_decode_feedback(const fdcan_frame_t *frame, c620_feedback_t *feedback)
{
    if (frame == 0 || feedback == 0 || frame->extended || frame->remote ||
        frame->dlc != 8U || frame->id < 0x201U || frame->id > 0x208U) {
        return false;
    }

    feedback->motor_id = (uint8_t)(frame->id - 0x200U);
    feedback->rotor_angle = read_u16_be(&frame->data[0]);
    feedback->rpm = (int16_t)read_u16_be(&frame->data[2]);
    feedback->torque_current = (int16_t)read_u16_be(&frame->data[4]);
    feedback->temperature_c = frame->data[6];
    return true;
}

static void write_i16_be(uint8_t *data, int16_t value)
{
    const uint16_t raw = (uint16_t)value;
    data[0] = (uint8_t)(raw >> 8U);
    data[1] = (uint8_t)raw;
}

void c620_make_current_command(fdcan_frame_t *frame, int16_t motor1,
                               int16_t motor2, int16_t motor3,
                               int16_t motor4)
{
    frame->id = 0x200U;
    frame->dlc = 8U;
    frame->extended = false;
    frame->remote = false;
    write_i16_be(&frame->data[0], motor1);
    write_i16_be(&frame->data[2], motor2);
    write_i16_be(&frame->data[4], motor3);
    write_i16_be(&frame->data[6], motor4);
}
