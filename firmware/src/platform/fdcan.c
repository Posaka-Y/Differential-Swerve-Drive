#include "platform/fdcan.h"

#include "platform/clock.h"
#include "platform/stm32g4xx_min.h"

/* STM32G4 FDCAN uses a fixed message RAM layout per instance (RM0440):
 * word offsets within the 0x350-byte instance block. Elements are always
 * FD-sized (2 header words + 16 data words) even in classic mode. */
enum {
    MSGRAM_INSTANCE_STRIDE_WORDS = 212U, /* 0x350 bytes */
    MSGRAM_RXFIFO0_OFFSET_WORDS = 44U,   /* 28 std + 8x2 ext filter words */
    MSGRAM_TXBUF_OFFSET_WORDS = 158U,    /* after RX FIFO1 and TX events */
    MSGRAM_ELEMENT_WORDS = 18U,
    INIT_TIMEOUT_LOOPS = 100000U,
};

typedef struct {
    fdcan_registers_t *regs;
    gpio_registers_t *port;
    uint8_t rx_pin;
    uint8_t tx_pin;
    uint8_t instance_index; /* 0 = FDCAN1, 1 = FDCAN2 */
} fdcan_hw_t;

static const fdcan_hw_t fdcan_hw[] = {
    [FDCAN_BUS_CENTRAL] = { FDCAN1, GPIOA, 11U, 12U, 0U },
    [FDCAN_BUS_C620] = { FDCAN2, GPIOB, 12U, 13U, 1U },
};

enum { FDCAN_GPIO_AF = 9U };

static volatile uint32_t *msgram_base(const fdcan_hw_t *hw)
{
    return (volatile uint32_t *)SRAMCAN_BASE +
           (uint32_t)hw->instance_index * MSGRAM_INSTANCE_STRIDE_WORDS;
}

static void configure_pins(const fdcan_hw_t *hw)
{
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN | RCC_AHB2ENR_GPIOBEN;
    (void)RCC->AHB2ENR;

    const uint8_t pins[2] = { hw->rx_pin, hw->tx_pin };
    for (uint32_t i = 0U; i < 2U; ++i) {
        const uint32_t pin = pins[i];
        hw->port->MODER = (hw->port->MODER & ~(3UL << (pin * 2U))) |
                          (2UL << (pin * 2U));
        hw->port->OSPEEDR |= 3UL << (pin * 2U);
        hw->port->PUPDR &= ~(3UL << (pin * 2U));
        hw->port->AFR[pin / 8U] =
            (hw->port->AFR[pin / 8U] & ~(0xFUL << ((pin % 8U) * 4U))) |
            ((uint32_t)FDCAN_GPIO_AF << ((pin % 8U) * 4U));
    }
}

bool fdcan_init(fdcan_bus_t bus, fdcan_mode_t mode)
{
    const fdcan_hw_t *hw = &fdcan_hw[bus];
    fdcan_registers_t *can = hw->regs;

    configure_pins(hw);

    RCC->APB1ENR1 |= RCC_APB1ENR1_FDCANEN;
    (void)RCC->APB1ENR1;
    RCC->CCIPR = (RCC->CCIPR & ~RCC_CCIPR_FDCANSEL_MASK) |
                 RCC_CCIPR_FDCANSEL_PCLK;

    can->CCCR |= FDCAN_CCCR_INIT;
    uint32_t guard = INIT_TIMEOUT_LOOPS;
    while ((can->CCCR & FDCAN_CCCR_INIT) == 0U) {
        if (--guard == 0U) {
            return false;
        }
    }
    can->CCCR |= FDCAN_CCCR_CCE;

    can->CKDIV = 0U;

    /* 1 Mbps from the 16 MHz HSI kernel clock (PCLK1, no PLL):
     * 16 tq per bit = sync(1) + seg1(13) + seg2(2), sample point 87.5%.
     * Register fields hold value-minus-one. */
    if (clock_frequency_hz() != 16000000U) {
        return false;
    }
    can->NBTP = (1UL << 25) |  /* NSJW  = 2 tq */
                (0UL << 16) |  /* NBRP  = /1  */
                (12UL << 8) |  /* NTSEG1 = 13 tq */
                (1UL << 0);    /* NTSEG2 = 2 tq */

    /* Accept all standard/extended frames into RX FIFO0, no filters yet. */
    can->RXGFC = 0U;

    volatile uint32_t *ram = msgram_base(hw);
    for (uint32_t i = 0U; i < MSGRAM_INSTANCE_STRIDE_WORDS; ++i) {
        ram[i] = 0U;
    }

    if (mode == FDCAN_MODE_INTERNAL_LOOPBACK) {
        can->CCCR |= FDCAN_CCCR_TEST | FDCAN_CCCR_MON;
        can->TEST |= FDCAN_TEST_LBCK;
    } else {
        can->CCCR &= ~(FDCAN_CCCR_TEST | FDCAN_CCCR_MON);
    }

    can->CCCR &= ~FDCAN_CCCR_INIT;
    guard = INIT_TIMEOUT_LOOPS;
    while ((can->CCCR & FDCAN_CCCR_INIT) != 0U) {
        if (--guard == 0U) {
            return false;
        }
    }
    return true;
}

bool fdcan_send(fdcan_bus_t bus, const fdcan_frame_t *frame)
{
    const fdcan_hw_t *hw = &fdcan_hw[bus];
    fdcan_registers_t *can = hw->regs;

    if (frame->dlc > 8U) {
        return false;
    }
    if ((can->TXFQS & (1UL << 21)) != 0U) { /* TFQF: FIFO full */
        return false;
    }

    const uint32_t put_index = (can->TXFQS >> 16) & 3UL;
    volatile uint32_t *element = msgram_base(hw) + MSGRAM_TXBUF_OFFSET_WORDS +
                                 put_index * MSGRAM_ELEMENT_WORDS;

    uint32_t header0;
    if (frame->extended) {
        header0 = (1UL << 30) | (frame->id & 0x1FFFFFFFUL);
    } else {
        header0 = (frame->id & 0x7FFUL) << 18;
    }
    if (frame->remote) {
        header0 |= 1UL << 29;
    }
    element[0] = header0;
    element[1] = (uint32_t)frame->dlc << 16;
    element[2] = (uint32_t)frame->data[0] | ((uint32_t)frame->data[1] << 8) |
                 ((uint32_t)frame->data[2] << 16) |
                 ((uint32_t)frame->data[3] << 24);
    element[3] = (uint32_t)frame->data[4] | ((uint32_t)frame->data[5] << 8) |
                 ((uint32_t)frame->data[6] << 16) |
                 ((uint32_t)frame->data[7] << 24);

    can->TXBAR = 1UL << put_index;
    return true;
}

bool fdcan_receive(fdcan_bus_t bus, fdcan_frame_t *frame)
{
    const fdcan_hw_t *hw = &fdcan_hw[bus];
    fdcan_registers_t *can = hw->regs;

    if ((can->RXF0S & 0xFUL) == 0U) { /* F0FL: fill level */
        return false;
    }

    const uint32_t get_index = (can->RXF0S >> 8) & 3UL;
    volatile const uint32_t *element = msgram_base(hw) +
                                       MSGRAM_RXFIFO0_OFFSET_WORDS +
                                       get_index * MSGRAM_ELEMENT_WORDS;

    const uint32_t header0 = element[0];
    const uint32_t header1 = element[1];

    frame->extended = (header0 & (1UL << 30)) != 0U;
    frame->remote = (header0 & (1UL << 29)) != 0U;
    frame->id = frame->extended ? (header0 & 0x1FFFFFFFUL)
                                : ((header0 >> 18) & 0x7FFUL);
    uint32_t dlc = (header1 >> 16) & 0xFUL;
    if (dlc > 8U) {
        dlc = 8U; /* classic CAN caps DLC 9-15 at 8 data bytes */
    }
    frame->dlc = (uint8_t)dlc;

    const uint32_t data0 = element[2];
    const uint32_t data1 = element[3];
    frame->data[0] = (uint8_t)data0;
    frame->data[1] = (uint8_t)(data0 >> 8);
    frame->data[2] = (uint8_t)(data0 >> 16);
    frame->data[3] = (uint8_t)(data0 >> 24);
    frame->data[4] = (uint8_t)data1;
    frame->data[5] = (uint8_t)(data1 >> 8);
    frame->data[6] = (uint8_t)(data1 >> 16);
    frame->data[7] = (uint8_t)(data1 >> 24);

    can->RXF0A = get_index;
    return true;
}

uint32_t fdcan_protocol_status(fdcan_bus_t bus)
{
    return fdcan_hw[bus].regs->PSR;
}
