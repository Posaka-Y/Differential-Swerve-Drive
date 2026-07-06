#include <stdint.h>

#include "platform/clock.h"
#include "platform/stm32g4xx_min.h"

extern uint32_t _sidata;
extern uint32_t _sdata;
extern uint32_t _edata;
extern uint32_t _sbss;
extern uint32_t _ebss;

void SystemInit(void)
{
    uint32_t *source = &_sidata;
    for (uint32_t *destination = &_sdata; destination < &_edata;) {
        *destination++ = *source++;
    }

    for (uint32_t *destination = &_sbss; destination < &_ebss;) {
        *destination++ = 0U;
    }

    /* Enable CP10 and CP11 for the Cortex-M4F floating-point unit. */
    SCB_CPACR |= 0xFUL << 20;
    __asm volatile("dsb");
    __asm volatile("isb");
}

void SysTick_Handler(void)
{
    clock_systick_handler();
}
