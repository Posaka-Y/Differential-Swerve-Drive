#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum {
    STEER_CALIBRATION_COUNTS_PER_REV = 4096U,
    STEER_CALIBRATION_RECORD_SIZE = 24U,
};

typedef struct {
    uint32_t magic;
    uint16_t version;
    uint16_t zero_position_counts;
    uint32_t sequence;
    uint32_t reserved;
    uint32_t crc32;
    uint32_t commit;
} steer_calibration_record_t;

typedef struct {
    bool calibrated;
    bool crc_error;
    bool page_full;
    uint16_t zero_position_counts;
    uint32_t sequence;
    size_t next_record_offset;
} steer_calibration_scan_t;

uint32_t steer_calibration_crc32(const void *data, size_t length);
void steer_calibration_prepare_record(steer_calibration_record_t *record,
                                      uint16_t zero_position_counts,
                                      uint32_t sequence);
bool steer_calibration_record_is_valid(
    const steer_calibration_record_t *record);
steer_calibration_scan_t steer_calibration_scan_page(const void *page,
                                                      size_t page_size);
uint16_t steer_calibration_apply(uint16_t raw_position_counts,
                                 uint16_t zero_position_counts);
