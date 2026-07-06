#pragma once

#include <stdint.h>

void clock_init(void);
uint32_t clock_frequency_hz(void);
uint32_t clock_millis(void);
void clock_delay_ms(uint32_t duration_ms);
void clock_delay_us(uint32_t duration_us);
void clock_systick_handler(void);
