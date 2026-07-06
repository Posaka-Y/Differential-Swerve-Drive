#include "platform/clock.h"

#include "platform/stm32g4xx_min.h"

enum { HSI_CLOCK_HZ = 16000000U };

static volatile uint32_t milliseconds;

void clock_init(void)
{
    /* Reset state uses the 16 MHz HSI. Configure SysTick for 1 ms ticks. */
    SYSTICK->LOAD = (HSI_CLOCK_HZ / 1000U) - 1U;
    SYSTICK->VAL = 0U;
    SYSTICK->CTRL = SYSTICK_CTRL_CLKSOURCE | SYSTICK_CTRL_TICKINT |
                    SYSTICK_CTRL_ENABLE;
}

uint32_t clock_frequency_hz(void)
{
    return HSI_CLOCK_HZ;
}

uint32_t clock_millis(void)
{
    return milliseconds;
}

void clock_delay_ms(uint32_t duration_ms)
{
    const uint32_t start = clock_millis();
    while ((uint32_t)(clock_millis() - start) < duration_ms) {
        __asm volatile("wfi");
    }
}

void clock_delay_us(uint32_t duration_us)
{
    const uint32_t period_ticks = SYSTICK->LOAD + 1U;
    const uint32_t required_ticks = duration_us * (HSI_CLOCK_HZ / 1000000U);
    const uint32_t start = SYSTICK->VAL;
    uint32_t elapsed = 0U;

    /* Intended for sub-millisecond peripheral timing delays. */
    while (elapsed < required_ticks) {
        const uint32_t current = SYSTICK->VAL;
        elapsed = start >= current ? start - current
                                   : start + period_ticks - current;
    }
}

void clock_systick_handler(void)
{
    ++milliseconds;
}
