#pragma once

#ifndef DSD_UART_TX_GPIO
#define DSD_UART_TX_GPIO 17
#endif

#ifndef DSD_UART_RX_GPIO
#define DSD_UART_RX_GPIO 22
#endif

#ifndef DSD_UNIT_ID
#define DSD_UNIT_ID 1
#endif

#ifndef DSD_CONTROLLER_TIMEOUT_MS
#define DSD_CONTROLLER_TIMEOUT_MS 150
#endif

#ifndef DSD_UNIT_STATUS_TIMEOUT_MS
#define DSD_UNIT_STATUS_TIMEOUT_MS 250
#endif

#ifndef DSD_UART_PERIOD_MS
#define DSD_UART_PERIOD_MS 20
#endif

#ifndef DSD_TELEMETRY_PERIOD_MS
#define DSD_TELEMETRY_PERIOD_MS 50
#endif

#ifndef DSD_OFFLINE_LOG_FLUSH_PERIOD_MS
#define DSD_OFFLINE_LOG_FLUSH_PERIOD_MS 1000
#endif

#ifndef DSD_MAX_WHEEL_RPM
#define DSD_MAX_WHEEL_RPM 500.0f
#endif

#ifndef DSD_MIN_WHEEL_RPM_LIMIT
#define DSD_MIN_WHEEL_RPM_LIMIT 250.0f
#endif

#ifndef DSD_MAX_WHEEL_RPM_LIMIT
#define DSD_MAX_WHEEL_RPM_LIMIT 1300.0f
#endif

#ifndef DSD_WHEEL_RPM_LIMIT_STEP
#define DSD_WHEEL_RPM_LIMIT_STEP 250.0f
#endif

#ifndef DSD_MAX_STEER_DEG
#define DSD_MAX_STEER_DEG 90.0f
#endif

#ifndef DSD_STICK_DEADZONE
#define DSD_STICK_DEADZONE 0.10f
#endif

#ifndef DSD_STICK_LINEAR_MIX
#define DSD_STICK_LINEAR_MIX 0.35f
#endif

// Initial commissioning lock. Change to 1 only after Bluetooth input, UART
// CRC/status reception and lifted-wheel safety checks all pass.
#ifndef DSD_MOTOR_ENABLE_ALLOWED
#define DSD_MOTOR_ENABLE_ALLOWED 1
#endif

// One-shot commissioning option. Set back to 0 after a successful pairing so
// the controller can reconnect after reset.
#ifndef DSD_FORGET_BLUETOOTH_KEYS_ON_BOOT
#define DSD_FORGET_BLUETOOTH_KEYS_ON_BOOT 0
#endif
