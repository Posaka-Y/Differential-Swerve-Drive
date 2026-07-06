#include "platform/amt22.h"

#include "platform/clock.h"
#include "platform/stm32g4xx_min.h"

enum {
    AMT22_SCK_PIN = 10U,
    AMT22_MISO_PIN = 11U,
    AMT22_MOSI_PIN = 12U,
    AMT22_SPI_AF = 6U,
    AMT22_CS_PIN = 2U,
    SPI_WAIT_LIMIT = 100000U,
};

static void chip_select(bool selected)
{
    GPIOD->BSRR = selected ? (1UL << (AMT22_CS_PIN + 16U))
                           : (1UL << AMT22_CS_PIN);
}

static bool spi_transfer(uint8_t tx, uint8_t *rx)
{
    uint32_t timeout = SPI_WAIT_LIMIT;
    while (((SPI3->SR & SPI_SR_TXE) == 0U) && (--timeout != 0U)) {
    }
    if (timeout == 0U) {
        return false;
    }

    *(volatile uint8_t *)&SPI3->DR = tx;

    timeout = SPI_WAIT_LIMIT;
    while (((SPI3->SR & SPI_SR_RXNE) == 0U) && (--timeout != 0U)) {
    }
    if (timeout == 0U) {
        return false;
    }

    *rx = *(volatile uint8_t *)&SPI3->DR;
    return true;
}

static bool parity_check(uint16_t raw)
{
    const uint16_t data = raw & 0x3FFFU;
    bool odd_group = true;
    bool even_group = true;

    for (uint32_t bit = 1U; bit <= 13U; bit += 2U) {
        odd_group ^= ((data >> bit) & 1U) != 0U;
    }
    for (uint32_t bit = 0U; bit <= 12U; bit += 2U) {
        even_group ^= ((data >> bit) & 1U) != 0U;
    }

    return odd_group == (((raw >> 15U) & 1U) != 0U) &&
           even_group == (((raw >> 14U) & 1U) != 0U);
}

void amt22_init(void)
{
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOCEN | RCC_AHB2ENR_GPIODEN;
    RCC->APB1ENR1 |= RCC_APB1ENR1_SPI3EN;
    (void)RCC->APB1ENR1;

    const uint32_t spi_pin_mask = (3UL << (AMT22_SCK_PIN * 2U)) |
                                  (3UL << (AMT22_MISO_PIN * 2U)) |
                                  (3UL << (AMT22_MOSI_PIN * 2U));
    GPIOC->MODER = (GPIOC->MODER & ~spi_pin_mask) |
                   (2UL << (AMT22_SCK_PIN * 2U)) |
                   (2UL << (AMT22_MISO_PIN * 2U)) |
                   (2UL << (AMT22_MOSI_PIN * 2U));
    GPIOC->OTYPER &= ~((1UL << AMT22_SCK_PIN) | (1UL << AMT22_MOSI_PIN));
    GPIOC->OSPEEDR = (GPIOC->OSPEEDR & ~spi_pin_mask) | spi_pin_mask;
    GPIOC->PUPDR &= ~spi_pin_mask;
    GPIOC->AFR[1] = (GPIOC->AFR[1] &
                     ~((0xFUL << ((AMT22_SCK_PIN - 8U) * 4U)) |
                       (0xFUL << ((AMT22_MISO_PIN - 8U) * 4U)) |
                       (0xFUL << ((AMT22_MOSI_PIN - 8U) * 4U)))) |
                    ((uint32_t)AMT22_SPI_AF << ((AMT22_SCK_PIN - 8U) * 4U)) |
                    ((uint32_t)AMT22_SPI_AF << ((AMT22_MISO_PIN - 8U) * 4U)) |
                    ((uint32_t)AMT22_SPI_AF << ((AMT22_MOSI_PIN - 8U) * 4U));

    chip_select(false);
    GPIOD->MODER = (GPIOD->MODER & ~(3UL << (AMT22_CS_PIN * 2U))) |
                   (1UL << (AMT22_CS_PIN * 2U));
    GPIOD->OTYPER &= ~(1UL << AMT22_CS_PIN);
    GPIOD->OSPEEDR |= 3UL << (AMT22_CS_PIN * 2U);
    GPIOD->PUPDR &= ~(3UL << (AMT22_CS_PIN * 2U));

    SPI3->CR1 = 0U;
    SPI3->CR2 = (7UL << SPI_CR2_DS_SHIFT) | SPI_CR2_FRXTH;
    /* PCLK1=16 MHz, BR=3 gives 1 MHz. Mode 0, software-controlled CS. */
    SPI3->CR1 = SPI_CR1_MSTR | (3UL << SPI_CR1_BR_SHIFT) |
                SPI_CR1_SSM | SPI_CR1_SSI | SPI_CR1_SPE;
}

bool amt22_read(amt22_sample_t *sample)
{
    if (sample == 0) {
        return false;
    }

    uint8_t high = 0U;
    uint8_t low = 0U;
    chip_select(true);
    clock_delay_us(3U);
    const bool high_ok = spi_transfer(0x00U, &high);
    clock_delay_us(3U);
    const bool low_ok = spi_transfer(0x00U, &low);
    clock_delay_us(3U);
    chip_select(false);

    if (!high_ok || !low_ok) {
        sample->raw = 0U;
        sample->position = 0U;
        sample->check_bits_ok = false;
        return false;
    }

    sample->raw = ((uint16_t)high << 8U) | low;
    sample->position = (sample->raw & 0x3FFFU) >> 2U;
    sample->check_bits_ok = parity_check(sample->raw);
    return true;
}
