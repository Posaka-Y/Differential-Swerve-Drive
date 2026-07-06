#include "platform/gpio.h"

#include "platform/stm32g4xx_min.h"

enum {
    STATUS_LED_PIN = 5U,
    USER_BUTTON_PIN = 13U,
};

void board_io_init(void)
{
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN | RCC_AHB2ENR_GPIOCEN;
    (void)RCC->AHB2ENR;

    GPIOA->MODER = (GPIOA->MODER & ~(3UL << (STATUS_LED_PIN * 2U))) |
                   (1UL << (STATUS_LED_PIN * 2U));
    GPIOA->OTYPER &= ~(1UL << STATUS_LED_PIN);
    GPIOA->PUPDR &= ~(3UL << (STATUS_LED_PIN * 2U));

    GPIOC->MODER &= ~(3UL << (USER_BUTTON_PIN * 2U));
    GPIOC->PUPDR &= ~(3UL << (USER_BUTTON_PIN * 2U));

    status_led_write(false);
}

void status_led_write(bool enabled)
{
    GPIOA->BSRR = enabled ? (1UL << STATUS_LED_PIN)
                          : (1UL << (STATUS_LED_PIN + 16U));
}

bool user_button_is_pressed(void)
{
    /* NUCLEO-G474RE B1 is low when released and high while pressed. */
    return (GPIOC->IDR & (1UL << USER_BUTTON_PIN)) != 0U;
}
