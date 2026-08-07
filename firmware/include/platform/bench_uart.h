#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    int32_t steer_mdeg;
    int32_t wheel_rpm_milli;
    bool enable;
} bench_uart_command_t;

/* USART1 on PA9(TX)/PC5(RX), AF7. NUCLEO pins are CN10-21(TX) and
 * CN10-6(RX, Arduino D0). The link is 3.3V UART, 115200 8N1. */
void bench_uart_init(uint32_t baud);
bool bench_uart_receive_command(bench_uart_command_t *command);
void bench_uart_send_status(int32_t steer_mdeg, int32_t wheel_rpm_milli,
                            bool active);
uint32_t bench_uart_rx_byte_count(void);
uint32_t bench_uart_rx_error_count(void);
