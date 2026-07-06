#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint16_t raw;
    uint16_t position;
    bool check_bits_ok;
} amt22_sample_t;

/* AMT222A-V on SPI3: PC10=SCK, PC11=MISO, PC12=MOSI, PD2=CS_N. */
void amt22_init(void);
bool amt22_read(amt22_sample_t *sample);
