/* Standalone V1 ODOM CAN test. ST RM0090 and cmsis-device-f4 stm32f405xx.h.
 * PA11/12 AF9, TCAN1051V S tied low on PCB. No sensor/motor control.
 * Isolated bench IDs: host 0x6E4 -> echo 0x6E5, heartbeat 0x6E6.
 */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
#define RCC 0x40023800U
#define GA 0x40020000U
#define GB 0x40020400U
#define CAN 0x40006400U
/* magic, phase, uptime, fault, loopback_ok, HSE_ready, tx_ok, tx_fail,
 * rx_count, last_RIR, last_DLC, last_low, last_high, ESR, TSR, MSR,
 * RCC_CR, RCC_CFGR, BTR, rx_pin, fifo_overrun, echo_drop, tx_request,
 * loopback_ESR, GPIO IDR at TX high/low/released, RX weak-pulldown IDR.
 * Remaining words reserved. Live, not atomic snapshot. */
__attribute__((section(".diagnostic"))) volatile uint32_t diagnostic[32];

static int wait_bits(uint32_t addr, uint32_t mask, uint32_t value)
{
    for (uint32_t n = 0; n < 2000000U; ++n)
        if ((R(addr) & mask) == value) return 1;
    return 0;
}
static void fault(uint32_t code)
{
    diagnostic[3] = code;
    R(GB + 0x18) = 1U << 11;
    for (;;) { }
}
static void reset_can(void)
{
    R(RCC + 0x20) |= 1U << 25;
    R(RCC + 0x20) &= ~(1U << 25);
}
static void init_can(uint32_t timing)
{
    /* ABOM, one-shot transmission (NART), initialization, no sleep. */
    R(CAN) = (1U << 6) | (1U << 4) | 1U;
    if (!wait_bits(CAN + 4, 1U, 1U)) fault(1);
    R(CAN + 0x1C) = timing;
    R(CAN + 0x200) = (14U << 8) | 1U;
    R(CAN + 0x21C) = 0;
    R(CAN + 0x204) = 0; /* mask */
    R(CAN + 0x20C) = 1; /* 32-bit filter 0 */
    R(CAN + 0x214) = 0; /* FIFO0 */
    R(CAN + 0x240) = 0;
    R(CAN + 0x244) = 0; /* accept all for diagnostics */
    R(CAN + 0x21C) = 1;
    R(CAN + 0x200) &= ~1U;
    R(CAN) &= ~1U;
    if (!wait_bits(CAN + 4, 1U, 0)) fault(2);
}
static int send(uint32_t id, uint32_t dlc, uint32_t lo, uint32_t hi)
{
    if (!(R(CAN + 8) & (1U << 26))) return 0;
    R(CAN + 0x184) = dlc;
    R(CAN + 0x188) = lo;
    R(CAN + 0x18C) = hi;
    R(CAN + 0x180) = (id << 21) | 1U;
    diagnostic[22]++;
    return 1;
}
static void settle(void)
{
    /* ~tens of us at 8 MHz, far shorter than dominant timeout. */
    for (volatile uint32_t n = 0; n < 16U; ++n) __asm volatile ("nop");
}
static void physical_path_test(void)
{
    /* Isolated bench only, USB-CAN stopped. CAN held in reset state.
     * Briefly drive TX through GPIO and observe RX, then restore AF.
     * This tests electrical feedback, NOT CAN frame communication. */
    R(GA + 0x18) = 1U << 12;
    R(GA) = (R(GA) & ~(3U << 24)) | (1U << 24);
    settle();
    diagnostic[24] = R(GA + 0x10);
    R(GA + 0x18) = 1U << 28;
    settle();
    diagnostic[25] = R(GA + 0x10);
    R(GA + 0x18) = 1U << 12;
    settle();
    diagnostic[26] = R(GA + 0x10);
    /* RX remains an input: a connected push-pull RXD should beat weak pull. */
    R(GA + 0x0C) = (R(GA + 0x0C) & ~(3U << 22)) | (2U << 22);
    settle();
    diagnostic[27] = R(GA + 0x10);
    R(GA + 0x0C) = (R(GA + 0x0C) & ~(3U << 22)) | (1U << 22);
    R(GA) = (R(GA) & ~(3U << 24)) | (2U << 24);
}
int main(void)
{
    R(0xE000ED08U) = 0x08000000U;
    R(RCC + 0x30) |= 3U;
    R(RCC + 0x40) |= 1U << 25;
    (void)R(RCC + 0x40);
    R(GA) = (R(GA) & ~(3U << 10)) | (1U << 10);
    R(GB) = (R(GB) & ~(15U << 20)) | (5U << 20);
    R(GB + 0x18) = 3U << 26;
    /* bxCAN requires a recessive RX level while leaving initialization,
     * including silent-loopback. Set AF/pull before the first init. */
    R(GA + 0x24) = (R(GA + 0x24) & ~0x000FF000U) | 0x00099000U;
    R(GA + 0x0C) = (R(GA + 0x0C) & ~(15U << 22)) | (1U << 22);
    R(GA) = (R(GA) & ~(15U << 22)) | (10U << 22);
    diagnostic[0] = 0xF405CA01U;
    diagnostic[1] = 1;
    /* Silent loopback on reset HSI 16 MHz: 16 TQ, sample point 87.5%. */
    reset_can();
    init_can(0xC01C0000U); /* TS1=13, TS2=2, BRP=1 */
    send(0x6E4, 8, 0x12345678, 0xABCDEF01);
    if (!wait_bits(CAN + 0x0C, 3U, 1U)) fault(3);
    diagnostic[23] = R(CAN + 0x18);
    if (R(CAN + 0x1B0) != (0x6E4U << 21) ||
        (R(CAN + 0x1B4) & 15U) != 8 ||
        R(CAN + 0x1B8) != 0x12345678 || R(CAN + 0x1BC) != 0xABCDEF01)
        fault(4);
    diagnostic[4] = 1;
    reset_can();
    /* External CAN requires crystal clock; do not silently fall back to HSI. */
    diagnostic[1] = 2;
    R(RCC) |= 1U << 16;
    if (!wait_bits(RCC, 1U << 17, 1U << 17)) fault(5);
    diagnostic[5] = 1;
    R(RCC + 8) = 1U; /* HSE SYSCLK, AHB/APB1/APB2 /1: 8 MHz */
    if (!wait_bits(RCC + 8, 12U, 4U)) fault(6);
    physical_path_test();
    /* Configure AF before mode, TX push-pull, RX weak pull-up. */
    R(GA + 0x24) = (R(GA + 0x24) & ~0x000FF000U) | 0x00099000U;
    R(GA + 4) &= ~(1U << 12);
    R(GA + 8) |= 15U << 22;
    R(GA + 0x0C) = (R(GA + 0x0C) & ~(15U << 22)) | (1U << 22);
    R(GA) = (R(GA) & ~(15U << 22)) | (10U << 22);
    init_can(0x00140000U); /* 8 MHz / (1*(1+5+2)) = 1 Mbps, SP=75% */
    diagnostic[22] = 0;
    diagnostic[1] = 3;
    R(0xE000E014U) = 7999;
    R(0xE000E018U) = 0;
    R(0xE000E010U) = 5;
    uint32_t activity = 0;
    for (;;) {
        uint32_t tsr = R(CAN + 8);
        if (tsr & 1U) {
            if (tsr & 2U) diagnostic[6]++; else diagnostic[7]++;
            R(CAN + 8) = 1U; /* clear mailbox0 completion before reuse */
        }
        uint32_t fifo = R(CAN + 0x0C);
        if (fifo & 16U) { diagnostic[20]++; R(CAN + 0x0C) = 16U; }
        if (fifo & 3U) {
            uint32_t id = R(CAN + 0x1B0), dlc = R(CAN + 0x1B4) & 15U;
            uint32_t lo = R(CAN + 0x1B8), hi = R(CAN + 0x1BC);
            diagnostic[8]++;
            diagnostic[9] = id; diagnostic[10] = dlc;
            diagnostic[11] = lo; diagnostic[12] = hi;
            R(CAN + 0x0C) = 32U;
            activity = 200;
            if (id == (0x6E4U << 21) && dlc <= 8)
                if (!send(0x6E5, dlc, lo, hi)) diagnostic[21]++;
        }
        if (R(0xE000E010U) & (1U << 16)) {
            diagnostic[2]++;
            if (activity) activity--;
            if (diagnostic[2] % 1000U == 0)
                send(0x6E6, 8, diagnostic[2], diagnostic[8]);
            R(GA + 0x18) = diagnostic[2] % 1000U < 500U ? 1U << 5 : 1U << 21;
            R(GB + 0x18) = activity ? 1U << 10 : 1U << 26;
            R(GB + 0x18) = (R(CAN + 0x18) & 7U) ? 1U << 11 : 1U << 27;
        }
        diagnostic[13] = R(CAN + 0x18); diagnostic[14] = R(CAN + 8);
        diagnostic[15] = R(CAN + 4); diagnostic[16] = R(RCC);
        diagnostic[17] = R(RCC + 8); diagnostic[18] = R(CAN + 0x1C);
        diagnostic[19] = (R(GA + 0x10) >> 11) & 1U;
    }
}
void Default_Handler(void) { fault(0xBADFA017U); }
