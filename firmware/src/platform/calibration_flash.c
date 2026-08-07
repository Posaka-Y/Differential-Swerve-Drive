#include "platform/calibration_flash.h"

#include <stddef.h>
#include <stdint.h>

#include "config/steer_calibration.h"
#include "platform/stm32g4xx_min.h"

enum {
    CALIBRATION_FLASH_PAGE_SIZE = 2048U,
    CALIBRATION_FLASH_BANK2_PAGE = 127U,
    FLASH_OPERATION_TIMEOUT = 2000000U,
};

extern uint8_t _calibration_flash_start;

static calibration_flash_status_t current_status;
static size_t next_record_offset;

static const uint8_t *calibration_page(void)
{
    return (const uint8_t *)&_calibration_flash_start;
}

static void refresh_status(void)
{
    const steer_calibration_scan_t scan = steer_calibration_scan_page(
        calibration_page(), CALIBRATION_FLASH_PAGE_SIZE);
    current_status.calibrated = scan.calibrated;
    current_status.crc_error = scan.crc_error;
    current_status.page_full = scan.page_full;
    current_status.zero_position_counts = scan.zero_position_counts;
    current_status.sequence = scan.sequence;
    next_record_offset = scan.next_record_offset;
}

void calibration_flash_init(void)
{
    refresh_status();
}

calibration_flash_status_t calibration_flash_status(void)
{
    return current_status;
}

static bool flash_wait_ready(void)
{
    uint32_t timeout = FLASH_OPERATION_TIMEOUT;
    while ((FLASH->SR & FLASH_SR_BSY) != 0U && timeout > 0U) {
        --timeout;
    }
    return timeout > 0U;
}

static void flash_clear_status(void)
{
    FLASH->SR = FLASH_SR_CLEARABLE_FLAGS;
}

static bool flash_unlock(void)
{
    if ((FLASH->CR & FLASH_CR_LOCK) == 0U) {
        return true;
    }
    FLASH->KEYR = 0x45670123UL;
    FLASH->KEYR = 0xCDEF89ABUL;
    return (FLASH->CR & FLASH_CR_LOCK) == 0U;
}

static void flash_lock(void)
{
    FLASH->CR |= FLASH_CR_LOCK;
}

static bool flash_operation_ok(void)
{
    return (FLASH->SR & FLASH_SR_ERROR_FLAGS) == 0U;
}

static bool flash_program_doubleword(volatile uint32_t *destination,
                                     const uint32_t *source)
{
    if (!flash_wait_ready()) {
        return false;
    }
    flash_clear_status();
    FLASH->CR |= FLASH_CR_PG;
    destination[0] = source[0];
    __asm volatile("isb" ::: "memory");
    destination[1] = source[1];
    const bool ready = flash_wait_ready();
    FLASH->CR &= ~FLASH_CR_PG;
    return ready && flash_operation_ok() &&
           destination[0] == source[0] && destination[1] == source[1];
}

static bool flash_erase_calibration_page(void)
{
    if (!flash_wait_ready()) {
        return false;
    }
    flash_clear_status();
    FLASH->CR = (FLASH->CR & ~(FLASH_CR_PNB_MASK | FLASH_CR_BKER)) |
                FLASH_CR_PER | FLASH_CR_BKER |
                (CALIBRATION_FLASH_BANK2_PAGE << FLASH_CR_PNB_SHIFT);
    FLASH->CR |= FLASH_CR_STRT;
    const bool ready = flash_wait_ready();
    FLASH->CR &= ~(FLASH_CR_PER | FLASH_CR_PNB_MASK | FLASH_CR_BKER);
    return ready && flash_operation_ok();
}

bool calibration_flash_save_zero(uint16_t raw_position_counts)
{
    if (current_status.page_full ||
        raw_position_counts >= STEER_CALIBRATION_COUNTS_PER_REV) {
        return false;
    }

    steer_calibration_record_t record;
    steer_calibration_prepare_record(
        &record, raw_position_counts,
        current_status.calibrated ? current_status.sequence + 1U : 1U);

    volatile uint32_t *destination = (volatile uint32_t *)(
        (uintptr_t)calibration_page() + next_record_offset);
    const uint32_t *source = (const uint32_t *)&record;
    bool ok = flash_unlock();
    for (size_t word = 0U; ok && word < sizeof(record) / sizeof(uint32_t);
         word += 2U) {
        ok = flash_program_doubleword(&destination[word], &source[word]);
    }
    flash_lock();
    refresh_status();
    return ok && current_status.calibrated &&
           current_status.zero_position_counts == raw_position_counts;
}

bool calibration_flash_clear(void)
{
    bool ok = flash_unlock();
    if (ok) {
        ok = flash_erase_calibration_page();
    }
    flash_lock();
    refresh_status();
    return ok && !current_status.calibrated && !current_status.crc_error &&
           !current_status.page_full;
}
