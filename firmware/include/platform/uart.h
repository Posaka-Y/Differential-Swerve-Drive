#pragma once

#include <stdint.h>

/* LPUART1 on PA2/PA3 (AF12). Routed to the ST-LINK VCP on NUCLEO-G474RE;
 * brought out on the debug header on the custom board. */
void debug_uart_init(uint32_t baud);
void debug_uart_write_char(char c);
void debug_uart_write(const char *text);

/* Minimal printf. Supports %s, %c, %d, %u, %x (32-bit), %%. */
void debug_printf(const char *format, ...);
