#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    bool calibrated;
    bool crc_error;
    bool page_full;
    uint16_t zero_position_counts;
    uint32_t sequence;
} calibration_flash_status_t;

void calibration_flash_init(void);
calibration_flash_status_t calibration_flash_status(void);
bool calibration_flash_save_zero(uint16_t raw_position_counts);
bool calibration_flash_clear(void);
