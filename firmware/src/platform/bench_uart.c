#include "platform/bench_uart.h"

#include <stddef.h>

#include "platform/clock.h"
#include "platform/stm32g4xx_min.h"

enum {
    BENCH_UART_TX_PIN = 9U,
    BENCH_UART_RX_PIN = 5U,
    BENCH_UART_AF = 7U,
    FRAME_SIZE = 14U,
    FRAME_TYPE_COMMAND = 0x01U,
    FRAME_TYPE_STATUS = 0x81U,
};

static uint8_t receive_frame[FRAME_SIZE];
static uint8_t receive_count;
static uint8_t transmit_sequence;
static uint32_t received_bytes;
static uint32_t receive_errors;

static uint8_t crc8(const uint8_t *data, uint32_t length)
{
    uint8_t crc = 0U;
    for (uint32_t i = 0U; i < length; ++i) {
        crc ^= data[i];
        for (uint32_t bit = 0U; bit < 8U; ++bit) {
            crc = (crc & 0x80U) != 0U
                ? (uint8_t)((crc << 1U) ^ 0x07U)
                : (uint8_t)(crc << 1U);
        }
    }
    return crc;
}

static int32_t read_i32_le(const uint8_t *data)
{
    const uint32_t raw = (uint32_t)data[0] |
                         ((uint32_t)data[1] << 8U) |
                         ((uint32_t)data[2] << 16U) |
                         ((uint32_t)data[3] << 24U);
    return (int32_t)raw;
}

static void write_i32_le(uint8_t *data, int32_t value)
{
    const uint32_t raw = (uint32_t)value;
    data[0] = (uint8_t)raw;
    data[1] = (uint8_t)(raw >> 8U);
    data[2] = (uint8_t)(raw >> 16U);
    data[3] = (uint8_t)(raw >> 24U);
}

static void write_byte(uint8_t value)
{
    while ((USART1->ISR & USART_ISR_TXE) == 0U) {
    }
    USART1->TDR = value;
}

void bench_uart_init(uint32_t baud)
{
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN | RCC_AHB2ENR_GPIOCEN;
    RCC->APB2ENR |= RCC_APB2ENR_USART1EN;
    (void)RCC->APB2ENR;

    GPIOA->MODER = (GPIOA->MODER &
                    ~(3UL << (BENCH_UART_TX_PIN * 2U))) |
                   (2UL << (BENCH_UART_TX_PIN * 2U));
    GPIOC->MODER = (GPIOC->MODER &
                    ~(3UL << (BENCH_UART_RX_PIN * 2U))) |
                   (2UL << (BENCH_UART_RX_PIN * 2U));
    GPIOA->AFR[1] = (GPIOA->AFR[1] &
                     ~(0xFUL << ((BENCH_UART_TX_PIN - 8U) * 4U))) |
                    ((uint32_t)BENCH_UART_AF <<
                     ((BENCH_UART_TX_PIN - 8U) * 4U));
    GPIOC->AFR[0] = (GPIOC->AFR[0] &
                     ~(0xFUL << (BENCH_UART_RX_PIN * 4U))) |
                    ((uint32_t)BENCH_UART_AF <<
                     (BENCH_UART_RX_PIN * 4U));

    USART1->CR1 = 0U;
    USART1->PRESC = 0U;
    USART1->BRR = (clock_frequency_hz() + baud / 2U) / baud;
    USART1->ICR = USART_ICR_ERROR_CLEAR;
    USART1->CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE |
                  USART_CR1_FIFOEN;
    receive_count = 0U;
}

bool bench_uart_receive_command(bench_uart_command_t *command)
{
    if (command == NULL) {
        return false;
    }

    /* A long blocking debug print can overrun the RX FIFO. ORE blocks later
     * reception until explicitly cleared, so recover before testing RXNE. A
     * damaged frame is discarded; the next 20ms command refreshes it. */
    if ((USART1->ISR & USART_ISR_ERROR_MASK) != 0U) {
        USART1->ICR = USART_ICR_ERROR_CLEAR;
        receive_count = 0U;
        ++receive_errors;
    }

    while ((USART1->ISR & USART_ISR_RXNE) != 0U) {
        const uint32_t status = USART1->ISR;
        const uint8_t byte = (uint8_t)USART1->RDR;
        ++received_bytes;
        if ((status & USART_ISR_ERROR_MASK) != 0U) {
            USART1->ICR = USART_ICR_ERROR_CLEAR;
            receive_count = 0U;
            ++receive_errors;
            continue;
        }

        if (receive_count == 0U) {
            if (byte == 0xA5U) {
                receive_frame[receive_count++] = byte;
            }
            continue;
        }
        if (receive_count == 1U && byte != 0x5AU) {
            receive_count = byte == 0xA5U ? 1U : 0U;
            continue;
        }

        receive_frame[receive_count++] = byte;
        if (receive_count < FRAME_SIZE) {
            continue;
        }

        receive_count = 0U;
        if (receive_frame[2] != FRAME_TYPE_COMMAND ||
            crc8(receive_frame, FRAME_SIZE - 1U) !=
                receive_frame[FRAME_SIZE - 1U]) {
            ++receive_errors;
            continue;
        }
        command->steer_mdeg = read_i32_le(&receive_frame[4]);
        command->wheel_rpm_milli = read_i32_le(&receive_frame[8]);
        command->enable = (receive_frame[12] & 1U) != 0U;
        return true;
    }
    return false;
}

uint32_t bench_uart_rx_byte_count(void)
{
    return received_bytes;
}

uint32_t bench_uart_rx_error_count(void)
{
    return receive_errors;
}

void bench_uart_send_status(int32_t steer_mdeg, int32_t wheel_rpm_milli,
                            bool active)
{
    uint8_t frame[FRAME_SIZE] = {
        0xA5U, 0x5AU, FRAME_TYPE_STATUS, transmit_sequence++,
    };
    write_i32_le(&frame[4], steer_mdeg);
    write_i32_le(&frame[8], wheel_rpm_milli);
    frame[12] = active ? 1U : 0U;
    frame[13] = crc8(frame, FRAME_SIZE - 1U);
    for (uint32_t i = 0U; i < FRAME_SIZE; ++i) {
        write_byte(frame[i]);
    }
}
