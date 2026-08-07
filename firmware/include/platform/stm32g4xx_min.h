#pragma once

#include <stdint.h>

#define PERIPH_BASE       (0x40000000UL)
#define AHB1PERIPH_BASE   (PERIPH_BASE + 0x00020000UL)
#define AHB2PERIPH_BASE   (PERIPH_BASE + 0x08000000UL)
#define FLASH_R_BASE      (AHB1PERIPH_BASE + 0x2000UL)
#define RCC_BASE          (0x40021000UL)
#define GPIOA_BASE        (AHB2PERIPH_BASE + 0x0000UL)
#define GPIOB_BASE        (AHB2PERIPH_BASE + 0x0400UL)
#define GPIOC_BASE        (AHB2PERIPH_BASE + 0x0800UL)
#define GPIOD_BASE        (AHB2PERIPH_BASE + 0x0C00UL)
#define LPUART1_BASE      (PERIPH_BASE + 0x8000UL)
#define USART1_BASE       (PERIPH_BASE + 0x13800UL)
#define SPI3_BASE         (PERIPH_BASE + 0x3C00UL)
#define FDCAN1_BASE       (PERIPH_BASE + 0x6400UL)
#define FDCAN2_BASE       (PERIPH_BASE + 0x6800UL)
#define FDCAN3_BASE       (PERIPH_BASE + 0x6C00UL)
#define SRAMCAN_BASE      (PERIPH_BASE + 0xA400UL)
#define SCS_BASE          (0xE000E000UL)
#define SYSTICK_BASE      (SCS_BASE + 0x0010UL)
#define SCB_CPACR         (*(volatile uint32_t *)0xE000ED88UL)

typedef struct {
    volatile uint32_t MODER;
    volatile uint32_t OTYPER;
    volatile uint32_t OSPEEDR;
    volatile uint32_t PUPDR;
    volatile uint32_t IDR;
    volatile uint32_t ODR;
    volatile uint32_t BSRR;
    volatile uint32_t LCKR;
    volatile uint32_t AFR[2];
    volatile uint32_t BRR;
} gpio_registers_t;

typedef struct {
    volatile uint32_t CR;
    volatile uint32_t ICSCR;
    volatile uint32_t CFGR;
    volatile uint32_t PLLCFGR;
    uint32_t RESERVED0[2];
    volatile uint32_t CIER;
    volatile uint32_t CIFR;
    volatile uint32_t CICR;
    uint32_t RESERVED1;
    volatile uint32_t AHB1RSTR;
    volatile uint32_t AHB2RSTR;
    volatile uint32_t AHB3RSTR;
    uint32_t RESERVED2;
    volatile uint32_t APB1RSTR1;
    volatile uint32_t APB1RSTR2;
    volatile uint32_t APB2RSTR;
    uint32_t RESERVED3;
    volatile uint32_t AHB1ENR;
    volatile uint32_t AHB2ENR;
    volatile uint32_t AHB3ENR;
    uint32_t RESERVED4;
    volatile uint32_t APB1ENR1;
    volatile uint32_t APB1ENR2;
    volatile uint32_t APB2ENR;
    uint32_t RESERVED5;
    volatile uint32_t AHB1SMENR;
    volatile uint32_t AHB2SMENR;
    volatile uint32_t AHB3SMENR;
    uint32_t RESERVED6;
    volatile uint32_t APB1SMENR1;
    volatile uint32_t APB1SMENR2;
    volatile uint32_t APB2SMENR;
    uint32_t RESERVED7;
    volatile uint32_t CCIPR;
} rcc_registers_t;

typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t CR3;
    volatile uint32_t BRR;
    uint32_t RESERVED0[2];
    volatile uint32_t RQR;
    volatile uint32_t ISR;
    volatile uint32_t ICR;
    volatile uint32_t RDR;
    volatile uint32_t TDR;
    volatile uint32_t PRESC;
} lpuart_registers_t;

typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile const uint32_t SR;
    volatile uint32_t DR;
    volatile uint32_t CRCPR;
    volatile const uint32_t RXCRCR;
    volatile const uint32_t TXCRCR;
    volatile uint32_t I2SCFGR;
    volatile uint32_t I2SPR;
} spi_registers_t;

typedef struct {
    volatile const uint32_t CREL;
    volatile const uint32_t ENDN;
    uint32_t RESERVED0;
    volatile uint32_t DBTP;
    volatile uint32_t TEST;
    volatile uint32_t RWD;
    volatile uint32_t CCCR;
    volatile uint32_t NBTP;
    volatile uint32_t TSCC;
    volatile const uint32_t TSCV;
    volatile uint32_t TOCC;
    volatile const uint32_t TOCV;
    uint32_t RESERVED1[4];
    volatile const uint32_t ECR;
    volatile const uint32_t PSR;
    volatile uint32_t TDCR;
    uint32_t RESERVED2;
    volatile uint32_t IR;
    volatile uint32_t IE;
    volatile uint32_t ILS;
    volatile uint32_t ILE;
    uint32_t RESERVED3[8];
    volatile uint32_t RXGFC;
    volatile uint32_t XIDAM;
    volatile const uint32_t HPMS;
    uint32_t RESERVED4;
    volatile const uint32_t RXF0S;
    volatile uint32_t RXF0A;
    volatile const uint32_t RXF1S;
    volatile uint32_t RXF1A;
    uint32_t RESERVED5[8];
    volatile uint32_t TXBC;
    volatile const uint32_t TXFQS;
    volatile const uint32_t TXBRP;
    volatile uint32_t TXBAR;
    volatile uint32_t TXBCR;
    volatile const uint32_t TXBTO;
    volatile const uint32_t TXBCF;
    volatile uint32_t TXBTIE;
    volatile uint32_t TXBCIE;
    volatile const uint32_t TXEFS;
    volatile uint32_t TXEFA;
    uint32_t RESERVED6[5];
    volatile uint32_t CKDIV;
} fdcan_registers_t;

typedef struct {
    volatile uint32_t CTRL;
    volatile uint32_t LOAD;
    volatile uint32_t VAL;
    volatile const uint32_t CALIB;
} systick_registers_t;

typedef struct {
    volatile uint32_t ACR;
    volatile uint32_t PDKEYR;
    volatile uint32_t KEYR;
    volatile uint32_t OPTKEYR;
    volatile uint32_t SR;
    volatile uint32_t CR;
    volatile uint32_t ECCR;
    uint32_t RESERVED0;
    volatile uint32_t OPTR;
} flash_registers_t;

#define GPIOA   ((gpio_registers_t *)GPIOA_BASE)
#define GPIOB   ((gpio_registers_t *)GPIOB_BASE)
#define GPIOC   ((gpio_registers_t *)GPIOC_BASE)
#define GPIOD   ((gpio_registers_t *)GPIOD_BASE)
#define RCC     ((rcc_registers_t *)RCC_BASE)
#define LPUART1 ((lpuart_registers_t *)LPUART1_BASE)
#define USART1  ((lpuart_registers_t *)USART1_BASE)
#define SPI3    ((spi_registers_t *)SPI3_BASE)
#define FDCAN1  ((fdcan_registers_t *)FDCAN1_BASE)
#define FDCAN2  ((fdcan_registers_t *)FDCAN2_BASE)
#define FDCAN3  ((fdcan_registers_t *)FDCAN3_BASE)
#define SYSTICK ((systick_registers_t *)SYSTICK_BASE)
#define FLASH   ((flash_registers_t *)FLASH_R_BASE)

#define RCC_AHB2ENR_GPIOAEN   (1UL << 0)
#define RCC_AHB2ENR_GPIOBEN   (1UL << 1)
#define RCC_AHB2ENR_GPIOCEN   (1UL << 2)
#define RCC_AHB2ENR_GPIODEN   (1UL << 3)
#define RCC_APB1ENR1_SPI3EN   (1UL << 15)
#define RCC_APB1ENR1_FDCANEN  (1UL << 25)
#define RCC_APB1ENR2_LPUART1EN (1UL << 0)
#define RCC_APB2ENR_USART1EN    (1UL << 14)
/* FDCANSEL[25:24]: 00=HSE, 01=PLLQ, 10=PCLK1 */
#define RCC_CCIPR_FDCANSEL_SHIFT 24U
#define RCC_CCIPR_FDCANSEL_MASK  (3UL << RCC_CCIPR_FDCANSEL_SHIFT)
#define RCC_CCIPR_FDCANSEL_PCLK  (2UL << RCC_CCIPR_FDCANSEL_SHIFT)
#define SYSTICK_CTRL_ENABLE   (1UL << 0)
#define SYSTICK_CTRL_TICKINT  (1UL << 1)
#define SYSTICK_CTRL_CLKSOURCE (1UL << 2)

#define FLASH_SR_EOP       (1UL << 0)
#define FLASH_SR_OPERR     (1UL << 1)
#define FLASH_SR_PROGERR   (1UL << 3)
#define FLASH_SR_WRPERR    (1UL << 4)
#define FLASH_SR_PGAERR    (1UL << 5)
#define FLASH_SR_SIZERR    (1UL << 6)
#define FLASH_SR_PGSERR    (1UL << 7)
#define FLASH_SR_MISERR    (1UL << 8)
#define FLASH_SR_FASTERR   (1UL << 9)
#define FLASH_SR_RDERR     (1UL << 14)
#define FLASH_SR_OPTVERR   (1UL << 15)
#define FLASH_SR_BSY       (1UL << 16)
#define FLASH_SR_ERROR_FLAGS (FLASH_SR_OPERR | FLASH_SR_PROGERR | \
                              FLASH_SR_WRPERR | FLASH_SR_PGAERR | \
                              FLASH_SR_SIZERR | FLASH_SR_PGSERR | \
                              FLASH_SR_MISERR | FLASH_SR_FASTERR | \
                              FLASH_SR_RDERR | FLASH_SR_OPTVERR)
#define FLASH_SR_CLEARABLE_FLAGS (FLASH_SR_EOP | FLASH_SR_ERROR_FLAGS)
#define FLASH_CR_PG        (1UL << 0)
#define FLASH_CR_PER       (1UL << 1)
#define FLASH_CR_PNB_SHIFT 3U
#define FLASH_CR_PNB_MASK  (0x7FUL << FLASH_CR_PNB_SHIFT)
#define FLASH_CR_BKER      (1UL << 11)
#define FLASH_CR_STRT      (1UL << 16)
#define FLASH_CR_LOCK      (1UL << 31)

#define LPUART_CR1_UE   (1UL << 0)
#define LPUART_CR1_RE   (1UL << 2)
#define LPUART_CR1_TE   (1UL << 3)
#define LPUART_ISR_RXNE (1UL << 5)
#define LPUART_ISR_TC   (1UL << 6)
#define LPUART_ISR_TXE  (1UL << 7)

#define USART_CR1_UE    (1UL << 0)
#define USART_CR1_RE    (1UL << 2)
#define USART_CR1_TE    (1UL << 3)
#define USART_CR1_FIFOEN (1UL << 29)
#define USART_ISR_FE    (1UL << 1)
#define USART_ISR_NE    (1UL << 2)
#define USART_ISR_ORE   (1UL << 3)
#define USART_ISR_RXNE  (1UL << 5)
#define USART_ISR_TXE   (1UL << 7)
#define USART_ISR_ERROR_MASK (USART_ISR_FE | USART_ISR_NE | USART_ISR_ORE)
#define USART_ICR_ERROR_CLEAR ((1UL << 1) | (1UL << 2) | (1UL << 3))

#define SPI_CR1_CPHA    (1UL << 0)
#define SPI_CR1_CPOL    (1UL << 1)
#define SPI_CR1_MSTR    (1UL << 2)
#define SPI_CR1_BR_SHIFT 3U
#define SPI_CR1_SPE     (1UL << 6)
#define SPI_CR1_SSI     (1UL << 8)
#define SPI_CR1_SSM     (1UL << 9)
#define SPI_CR2_DS_SHIFT 8U
#define SPI_CR2_FRXTH   (1UL << 12)
#define SPI_SR_RXNE     (1UL << 0)
#define SPI_SR_TXE      (1UL << 1)
#define SPI_SR_BSY      (1UL << 7)

#define FDCAN_CCCR_INIT (1UL << 0)
#define FDCAN_CCCR_CCE  (1UL << 1)
#define FDCAN_CCCR_ASM  (1UL << 2)
#define FDCAN_CCCR_MON  (1UL << 5)
#define FDCAN_CCCR_DAR  (1UL << 6)
#define FDCAN_CCCR_TEST (1UL << 7)
#define FDCAN_TEST_LBCK (1UL << 4)
