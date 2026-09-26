/* F405 bring-up: reset HSI 16 MHz, PA5/PB10/PB11, no interrupts or external clock.
 * All three status LEDs stay on. POWER is directly wired to the supply.
 * Register map: ST RM0090. SRAM 0x20000000: magic, seconds, LED mask, fault.
 */
#include <stdint.h>
#define REG32(a) (*(volatile uint32_t *)(a))
__attribute__((section(".diagnostic"))) volatile uint32_t diagnostic[4];

static void delay_ms(uint32_t ms)
{
    while (ms--) {
        while ((REG32(0xE000E010U) & (1U << 16)) == 0U) { }
    }
}

int main(void)
{
    REG32(0xE000ED08U) = 0x08000000U; /* VTOR */
    REG32(0x40023830U) |= 3U; /* RCC AHB1ENR GPIOAEN + GPIOBEN */
    (void)REG32(0x40023830U);
    REG32(0x40020018U) = 1U << 21; /* PA5 initially low */
    REG32(0x40020004U) &= ~(1U << 5); /* push-pull */
    REG32(0x40020008U) &= ~(3U << 10); /* low speed */
    REG32(0x4002000CU) &= ~(3U << 10); /* no pull */
    REG32(0x40020000U) = (REG32(0x40020000U) & ~(3U << 10)) | (1U << 10);
    REG32(0x40020418U) = (3U << 10) << 16; /* PB10/PB11 low */
    REG32(0x40020404U) &= ~(3U << 10);
    REG32(0x40020408U) &= ~(15U << 20);
    REG32(0x4002040CU) &= ~(15U << 20);
    REG32(0x40020400U) = (REG32(0x40020400U) & ~(15U << 20)) | (5U << 20);
    REG32(0xE000E014U) = 16000U - 1U;
    REG32(0xE000E018U) = 0U;
    REG32(0xE000E010U) = 5U; /* SysTick CPU clock, polling, no IRQ */
    diagnostic[0] = 0xF405B11AU;
    REG32(0x40020018U) = 1U << 5;
    REG32(0x40020418U) = 3U << 10;
    diagnostic[2] = 7U;
    for (;;) {
        delay_ms(1000U);
        diagnostic[1]++;
    }
}

void Default_Handler(void)
{
    diagnostic[3] = 0xBADFA017U;
    for (;;) { }
}
