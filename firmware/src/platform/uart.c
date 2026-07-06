#include "platform/uart.h"

#include <stdarg.h>
#include <stdbool.h>

#include "platform/clock.h"
#include "platform/stm32g4xx_min.h"

enum {
    DEBUG_UART_TX_PIN = 2U, /* PA2, AF12 */
    DEBUG_UART_RX_PIN = 3U, /* PA3, AF12 */
    DEBUG_UART_AF = 12U,
};

void debug_uart_init(uint32_t baud)
{
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN;
    RCC->APB1ENR2 |= RCC_APB1ENR2_LPUART1EN;
    (void)RCC->APB1ENR2;

    GPIOA->MODER = (GPIOA->MODER &
                    ~((3UL << (DEBUG_UART_TX_PIN * 2U)) |
                      (3UL << (DEBUG_UART_RX_PIN * 2U)))) |
                   (2UL << (DEBUG_UART_TX_PIN * 2U)) |
                   (2UL << (DEBUG_UART_RX_PIN * 2U));
    GPIOA->AFR[0] = (GPIOA->AFR[0] &
                     ~((0xFUL << (DEBUG_UART_TX_PIN * 4U)) |
                       (0xFUL << (DEBUG_UART_RX_PIN * 4U)))) |
                    ((uint32_t)DEBUG_UART_AF << (DEBUG_UART_TX_PIN * 4U)) |
                    ((uint32_t)DEBUG_UART_AF << (DEBUG_UART_RX_PIN * 4U));

    LPUART1->CR1 = 0U;
    LPUART1->PRESC = 0U;
    /* LPUART baud generator: BRR = 256 * f_ck / baud (RM0440). */
    LPUART1->BRR = (uint32_t)(((uint64_t)clock_frequency_hz() * 256U + baud / 2U) / baud);
    LPUART1->CR1 = LPUART_CR1_UE | LPUART_CR1_TE | LPUART_CR1_RE;
}

void debug_uart_write_char(char c)
{
    while ((LPUART1->ISR & LPUART_ISR_TXE) == 0U) {
    }
    LPUART1->TDR = (uint32_t)(uint8_t)c;
}

void debug_uart_write(const char *text)
{
    while (*text != '\0') {
        if (*text == '\n') {
            debug_uart_write_char('\r');
        }
        debug_uart_write_char(*text++);
    }
}

static void write_unsigned(uint32_t value, uint32_t base)
{
    char digits[11];
    uint32_t count = 0U;

    do {
        const uint32_t digit = value % base;
        digits[count++] = (char)(digit < 10U ? ('0' + digit) : ('a' + digit - 10U));
        value /= base;
    } while (value != 0U);

    while (count > 0U) {
        debug_uart_write_char(digits[--count]);
    }
}

void debug_printf(const char *format, ...)
{
    va_list args;
    va_start(args, format);

    for (; *format != '\0'; ++format) {
        if (*format != '%') {
            if (*format == '\n') {
                debug_uart_write_char('\r');
            }
            debug_uart_write_char(*format);
            continue;
        }

        ++format;
        switch (*format) {
        case 's': {
            const char *text = va_arg(args, const char *);
            debug_uart_write(text != 0 ? text : "(null)");
            break;
        }
        case 'c':
            debug_uart_write_char((char)va_arg(args, int));
            break;
        case 'd': {
            int32_t value = va_arg(args, int32_t);
            if (value < 0) {
                debug_uart_write_char('-');
                value = -value;
            }
            write_unsigned((uint32_t)value, 10U);
            break;
        }
        case 'u':
            write_unsigned(va_arg(args, uint32_t), 10U);
            break;
        case 'x':
            write_unsigned(va_arg(args, uint32_t), 16U);
            break;
        case '%':
            debug_uart_write_char('%');
            break;
        default:
            debug_uart_write_char('%');
            debug_uart_write_char(*format);
            break;
        }
    }

    va_end(args);
}
