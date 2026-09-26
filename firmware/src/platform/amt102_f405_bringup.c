/* Standalone ODOM bring-up, STM32F405, reset HSI=16MHz.
 * ST RM0090 / ST cmsis-device-f4 stm32f405xx.h register layout.
 * J4=PA0/1 TIM2 AF1; J5=PA6/7 TIM3 AF2; J6=PB6/7 TIM4 AF2.
 * Only LEDs and encoder inputs are configured. Observe through SWD.
 */
#include <stdint.h>
#define REG32(a) (*(volatile uint32_t *)(a))
#define GPIOA 0x40020000U
#define GPIOB 0x40020400U
#define RCC   0x40023800U
/* 0 magic, 1 sequence (even=stable), 2 uptime ms, 3 fault,
 * 4..6 raw 16-bit CNT, 7..9 modulo-32-bit signed accumulated counts,
 * 10..12 sampled AB (bit0=A, bit1=B), 13..15 samples with count changes.
 */
__attribute__((section(".diagnostic"))) volatile uint32_t diagnostic[16];
static const uint32_t timers[3] = {0x40000000U, 0x40000400U, 0x40000800U};

static void pin_mode(uint32_t port, uint32_t pin, uint32_t mode, uint32_t af)
{
    uint32_t shift = pin * 2U;
    REG32(port) = (REG32(port) & ~(3U << shift)) | (mode << shift);
    REG32(port + 0x0CU) = (REG32(port + 0x0CU) & ~(3U << shift)) |
                          ((mode == 2U ? 2U : 0U) << shift); /* AF input pulldown */
    uint32_t afr = port + 0x20U + (pin / 8U) * 4U;
    shift = (pin % 8U) * 4U;
    REG32(afr) = (REG32(afr) & ~(15U << shift)) | (af << shift);
}

int main(void)
{
    uint16_t previous[3] = {0U, 0U, 0U};
    uint32_t movement_until = 0U;
    REG32(0xE000ED08U) = 0x08000000U;
    REG32(RCC + 0x30U) |= 3U;
    REG32(RCC + 0x40U) |= 7U; /* TIM2,3,4 */
    (void)REG32(RCC + 0x40U);
    REG32(RCC + 0x20U) |= 7U;
    REG32(RCC + 0x20U) &= ~7U;
    pin_mode(GPIOA, 5U, 1U, 0U);
    pin_mode(GPIOB, 10U, 1U, 0U);
    pin_mode(GPIOB, 11U, 1U, 0U);
    REG32(GPIOB + 0x18U) = 3U << 26; /* COMM/ERR off */
    pin_mode(GPIOA, 0U, 2U, 1U);
    pin_mode(GPIOA, 1U, 2U, 1U);
    pin_mode(GPIOA, 6U, 2U, 2U);
    pin_mode(GPIOA, 7U, 2U, 2U);
    pin_mode(GPIOB, 6U, 2U, 2U);
    pin_mode(GPIOB, 7U, 2U, 2U);
    for (uint32_t i = 0U; i < 3U; ++i) {
        uint32_t t = timers[i];
        REG32(t + 0x28U) = 0U; /* PSC */
        REG32(t + 0x2CU) = 65535U; /* same wrap for all channels */
        REG32(t + 0x18U) = 0x3131U; /* direct TI1/TI2, 8 sample filter at fCK_INT */
        REG32(t + 0x20U) = 0x11U; /* non-inverted CC1/CC2 enabled */
        REG32(t + 0x08U) = 3U; /* encoder mode 3, x4 */
        REG32(t + 0x14U) = 1U; /* UG */
        REG32(t + 0x24U) = 0U;
        REG32(t + 0x10U) = 0U;
        REG32(t) = 1U; /* CEN */
    }
    REG32(0xE000E014U) = 15999U;
    REG32(0xE000E018U) = 0U;
    REG32(0xE000E010U) = 5U; /* poll every ms, no IRQ */
    diagnostic[0] = 0xF405A102U;
    for (;;) {
        while ((REG32(0xE000E010U) & (1U << 16)) == 0U) { }
        diagnostic[1]++;
        diagnostic[2]++;
        for (uint32_t i = 0U; i < 3U; ++i) {
            uint16_t raw = (uint16_t)REG32(timers[i] + 0x24U);
            uint32_t diff = (uint16_t)(raw - previous[i]);
            /* modulo arithmetic handles reverse and 16-bit timer wrap. */
            uint32_t delta = diff < 32768U ? diff : diff - 65536U;
            diagnostic[4U + i] = raw;
            diagnostic[7U + i] += delta;
            if (diff != 0U) {
                diagnostic[13U + i]++;
                movement_until = diagnostic[2] + 200U;
            }
            previous[i] = raw;
        }
        uint32_t a = REG32(GPIOA + 0x10U);
        diagnostic[10] = a & 3U;
        diagnostic[11] = (a >> 6) & 3U;
        diagnostic[12] = (REG32(GPIOB + 0x10U) >> 6) & 3U;
        diagnostic[1]++;
        REG32(GPIOA + 0x18U) = diagnostic[2] % 1000U < 500U ? 1U << 5 : 1U << 21;
        uint32_t remaining = movement_until - diagnostic[2];
        REG32(GPIOB + 0x18U) = remaining != 0U && remaining < 0x80000000U ?
                               1U << 10 : 1U << 26;
    }
}

void Default_Handler(void)
{
    diagnostic[3] = 0xBADFA017U;
    REG32(GPIOB + 0x18U) = 1U << 11;
    for (;;) { }
}
