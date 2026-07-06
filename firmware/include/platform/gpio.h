#pragma once

#include <stdbool.h>

void board_io_init(void);
void status_led_write(bool enabled);
bool user_button_is_pressed(void);
