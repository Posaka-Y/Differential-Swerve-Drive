#pragma once

#include <stdbool.h>
#include <stdint.h>

/* Bus assignment per docs/electrical/CARRIER_BOARD_REQUIREMENTS.md:
 * FDCAN_BUS_CENTRAL = FDCAN1 on PA11(RX)/PA12(TX)
 * FDCAN_BUS_C620    = FDCAN2 on PB12(RX)/PB13(TX)
 * Both run classic CAN at 1 Mbps. */
typedef enum {
    FDCAN_BUS_CENTRAL = 0,
    FDCAN_BUS_C620 = 1,
} fdcan_bus_t;

typedef enum {
    FDCAN_MODE_NORMAL,
    /* Internal loopback: TX looped to RX inside the peripheral, pins idle.
     * No transceiver or wiring required. */
    FDCAN_MODE_INTERNAL_LOOPBACK,
} fdcan_mode_t;

typedef struct {
    uint32_t id;
    uint8_t dlc; /* 0-8, classic CAN only */
    bool extended;
    bool remote;
    uint8_t data[8];
} fdcan_frame_t;

bool fdcan_init(fdcan_bus_t bus, fdcan_mode_t mode);

/* Queues one frame. Returns false if the 3-slot TX FIFO is full. */
bool fdcan_send(fdcan_bus_t bus, const fdcan_frame_t *frame);

/* Pops one frame from RX FIFO0. Returns false if empty. */
bool fdcan_receive(fdcan_bus_t bus, fdcan_frame_t *frame);

/* Raw PSR register for diagnostics (LEC[2:0], EP bit5, EW bit6, BO bit7). */
uint32_t fdcan_protocol_status(fdcan_bus_t bus);
