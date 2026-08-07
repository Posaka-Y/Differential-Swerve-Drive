#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "config/steer_calibration.h"

enum { TEST_PAGE_SIZE = 2048U };

static void write_record(uint8_t *page, size_t slot, uint16_t zero,
                         uint32_t sequence)
{
    steer_calibration_record_t record;
    steer_calibration_prepare_record(&record, zero, sequence);
    memcpy(page + slot * sizeof(record), &record, sizeof(record));
}

static void test_empty_and_apply(void)
{
    uint8_t page[TEST_PAGE_SIZE];
    memset(page, 0xFF, sizeof(page));
    const steer_calibration_scan_t scan =
        steer_calibration_scan_page(page, sizeof(page));
    assert(!scan.calibrated);
    assert(!scan.crc_error);
    assert(!scan.page_full);
    assert(scan.next_record_offset == 0U);
    assert(steer_calibration_apply(100U, 100U) == 0U);
    assert(steer_calibration_apply(50U, 100U) == 4046U);
}

static void test_latest_valid_record(void)
{
    uint8_t page[TEST_PAGE_SIZE];
    memset(page, 0xFF, sizeof(page));
    write_record(page, 0U, 100U, 1U);
    write_record(page, 1U, 2500U, 2U);
    const steer_calibration_scan_t scan =
        steer_calibration_scan_page(page, sizeof(page));
    assert(scan.calibrated);
    assert(scan.zero_position_counts == 2500U);
    assert(scan.sequence == 2U);
    assert(scan.next_record_offset == 2U * STEER_CALIBRATION_RECORD_SIZE);
}

static void test_torn_record_keeps_previous(void)
{
    uint8_t page[TEST_PAGE_SIZE];
    memset(page, 0xFF, sizeof(page));
    write_record(page, 0U, 321U, 7U);
    steer_calibration_record_t torn;
    steer_calibration_prepare_record(&torn, 999U, 8U);
    memcpy(page + sizeof(torn), &torn, 16U);
    const steer_calibration_scan_t scan =
        steer_calibration_scan_page(page, sizeof(page));
    assert(scan.calibrated);
    assert(scan.zero_position_counts == 321U);
    assert(scan.sequence == 7U);
    assert(scan.crc_error);
    assert(scan.next_record_offset == 2U * STEER_CALIBRATION_RECORD_SIZE);
}

static void test_crc_corruption_rejected(void)
{
    uint8_t page[TEST_PAGE_SIZE];
    memset(page, 0xFF, sizeof(page));
    write_record(page, 0U, 1000U, 1U);
    page[7] ^= 0x01U;
    const steer_calibration_scan_t scan =
        steer_calibration_scan_page(page, sizeof(page));
    assert(!scan.calibrated);
    assert(scan.crc_error);
}

int main(void)
{
    test_empty_and_apply();
    test_latest_valid_record();
    test_torn_record_keeps_previous();
    test_crc_corruption_rejected();
    puts("steer_calibration_test: PASS");
    return 0;
}
