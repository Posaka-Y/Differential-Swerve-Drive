#include "config/steer_calibration.h"

enum {
    STEER_CALIBRATION_MAGIC = 0x414D5432UL, /* "AMT2" */
    STEER_CALIBRATION_VERSION = 1U,
    STEER_CALIBRATION_COMMIT = 0x5A45524FUL, /* "ZERO" */
    STEER_CALIBRATION_CRC_LENGTH = 16U,
};

_Static_assert(sizeof(steer_calibration_record_t) ==
                   STEER_CALIBRATION_RECORD_SIZE,
               "calibration record layout changed");

uint32_t steer_calibration_crc32(const void *data, size_t length)
{
    const uint8_t *bytes = (const uint8_t *)data;
    uint32_t crc = 0xFFFFFFFFUL;
    for (size_t i = 0U; i < length; ++i) {
        crc ^= bytes[i];
        for (uint32_t bit = 0U; bit < 8U; ++bit) {
            const uint32_t mask = 0U - (crc & 1U);
            crc = (crc >> 1U) ^ (0xEDB88320UL & mask);
        }
    }
    return ~crc;
}

void steer_calibration_prepare_record(steer_calibration_record_t *record,
                                      uint16_t zero_position_counts,
                                      uint32_t sequence)
{
    record->magic = STEER_CALIBRATION_MAGIC;
    record->version = STEER_CALIBRATION_VERSION;
    record->zero_position_counts =
        zero_position_counts & (STEER_CALIBRATION_COUNTS_PER_REV - 1U);
    record->sequence = sequence;
    record->reserved = 0xFFFFFFFFUL;
    record->crc32 = steer_calibration_crc32(
        record, STEER_CALIBRATION_CRC_LENGTH);
    record->commit = STEER_CALIBRATION_COMMIT;
}

bool steer_calibration_record_is_valid(
    const steer_calibration_record_t *record)
{
    return record->magic == STEER_CALIBRATION_MAGIC &&
           record->version == STEER_CALIBRATION_VERSION &&
           record->zero_position_counts < STEER_CALIBRATION_COUNTS_PER_REV &&
           record->commit == STEER_CALIBRATION_COMMIT &&
           record->crc32 == steer_calibration_crc32(
               record, STEER_CALIBRATION_CRC_LENGTH);
}

static bool record_is_erased(const steer_calibration_record_t *record)
{
    const uint32_t *words = (const uint32_t *)record;
    for (size_t i = 0U; i < sizeof(*record) / sizeof(*words); ++i) {
        if (words[i] != 0xFFFFFFFFUL) {
            return false;
        }
    }
    return true;
}

steer_calibration_scan_t steer_calibration_scan_page(const void *page,
                                                      size_t page_size)
{
    const uint8_t *bytes = (const uint8_t *)page;
    steer_calibration_scan_t result = {
        .calibrated = false,
        .crc_error = false,
        .page_full = true,
        .zero_position_counts = 0U,
        .sequence = 0U,
        .next_record_offset = page_size,
    };

    for (size_t offset = 0U;
         offset + sizeof(steer_calibration_record_t) <= page_size;
         offset += sizeof(steer_calibration_record_t)) {
        const steer_calibration_record_t *record =
            (const steer_calibration_record_t *)(bytes + offset);
        if (record_is_erased(record)) {
            if (result.page_full) {
                result.page_full = false;
                result.next_record_offset = offset;
            }
            continue;
        }
        if (!steer_calibration_record_is_valid(record)) {
            result.crc_error = true;
            continue;
        }
        if (!result.calibrated ||
            (int32_t)(record->sequence - result.sequence) > 0) {
            result.calibrated = true;
            result.zero_position_counts = record->zero_position_counts;
            result.sequence = record->sequence;
        }
    }
    return result;
}

uint16_t steer_calibration_apply(uint16_t raw_position_counts,
                                 uint16_t zero_position_counts)
{
    return (uint16_t)((raw_position_counts - zero_position_counts) &
                      (STEER_CALIBRATION_COUNTS_PER_REV - 1U));
}
