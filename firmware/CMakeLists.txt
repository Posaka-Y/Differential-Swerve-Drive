cmake_minimum_required(VERSION 3.22)

project(differential_swerve_firmware LANGUAGES C ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(MCU_FLAGS
    -mcpu=cortex-m4
    -mthumb
    -mfpu=fpv4-sp-d16
    -mfloat-abi=hard
)

add_executable(${PROJECT_NAME}.elf
    src/main.c
    src/config/steer_calibration.c
    src/control/unit_controller.c
    src/platform/amt22.c
    src/platform/bench_uart.c
    src/platform/calibration_flash.c
    src/platform/clock.c
    src/platform/fdcan.c
    src/platform/gpio.c
    src/platform/system_stm32g4xx.c
    src/platform/uart.c
    src/protocol/c620.c
    src/platform/startup_stm32g4xx.s
)

target_include_directories(${PROJECT_NAME}.elf PRIVATE include)

target_compile_definitions(${PROJECT_NAME}.elf PRIVATE
    STM32G474xx
    NUCLEO_G474RE
)

target_compile_options(${PROJECT_NAME}.elf PRIVATE
    ${MCU_FLAGS}
    -ffunction-sections
    -fdata-sections
    $<$<COMPILE_LANGUAGE:C>:-fno-common>
    $<$<COMPILE_LANGUAGE:C>:-Wall>
    $<$<COMPILE_LANGUAGE:C>:-Wextra>
    $<$<COMPILE_LANGUAGE:C>:-Wpedantic>
    $<$<CONFIG:Debug>:-Og>
    $<$<CONFIG:Debug>:-g3>
    $<$<CONFIG:Release>:-Os>
    $<$<CONFIG:Release>:-g0>
)

target_link_options(${PROJECT_NAME}.elf PRIVATE
    ${MCU_FLAGS}
    -T${CMAKE_CURRENT_SOURCE_DIR}/linker/STM32G474RETx_FLASH.ld
    -nostdlib
    -Wl,--gc-sections
    -Wl,--print-memory-usage
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.map
)

target_link_libraries(${PROJECT_NAME}.elf PRIVATE gcc)

set_target_properties(${PROJECT_NAME}.elf PROPERTIES
    OUTPUT_NAME ${PROJECT_NAME}
    SUFFIX .elf
)

# POST_BUILD はビルドディレクトリ相対のファイル名だけで記述する。
# 絶対パスを使うと、非ASCIIパス(例: 趣味)が cmd.exe 経由で文字化けして
# objcopy が失敗する。
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex
            $<TARGET_FILE_NAME:${PROJECT_NAME}.elf>
            ${PROJECT_NAME}.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary
            $<TARGET_FILE_NAME:${PROJECT_NAME}.elf>
            ${PROJECT_NAME}.bin
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE_NAME:${PROJECT_NAME}.elf>
    COMMENT "Generating HEX/BIN images and reporting image size"
)

# --- 基板一次確認用の最小ファーム -------------------------------------------
# 自作基板の bring-up で「MCU が起動してコードを走らせている」ことだけを
# 切り分けるための別成果物。周辺回路を一切初期化しないので、CAN/SPI/水晶の
# 実装状態に関係なく動く。本体ファームとはソースを共有せず独立して壊せる。
set(BLINK_TARGET blink)

add_executable(${BLINK_TARGET}.elf
    src/blink/blink_main.c
    src/platform/clock.c
    src/platform/gpio.c
    src/platform/system_stm32g4xx.c
    src/platform/startup_stm32g4xx.s
)

target_include_directories(${BLINK_TARGET}.elf PRIVATE include)

target_compile_definitions(${BLINK_TARGET}.elf PRIVATE
    STM32G474xx
    NUCLEO_G474RE
)

target_compile_options(${BLINK_TARGET}.elf PRIVATE
    ${MCU_FLAGS}
    -ffunction-sections
    -fdata-sections
    $<$<COMPILE_LANGUAGE:C>:-fno-common>
    $<$<COMPILE_LANGUAGE:C>:-Wall>
    $<$<COMPILE_LANGUAGE:C>:-Wextra>
    $<$<COMPILE_LANGUAGE:C>:-Wpedantic>
    $<$<CONFIG:Debug>:-Og>
    $<$<CONFIG:Debug>:-g3>
    $<$<CONFIG:Release>:-Os>
    $<$<CONFIG:Release>:-g0>
)

target_link_options(${BLINK_TARGET}.elf PRIVATE
    ${MCU_FLAGS}
    -T${CMAKE_CURRENT_SOURCE_DIR}/linker/STM32G474RETx_FLASH.ld
    -nostdlib
    -Wl,--gc-sections
    -Wl,--print-memory-usage
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/${BLINK_TARGET}.map
)

target_link_libraries(${BLINK_TARGET}.elf PRIVATE gcc)

set_target_properties(${BLINK_TARGET}.elf PROPERTIES
    OUTPUT_NAME ${BLINK_TARGET}
    SUFFIX .elf
)

# POST_BUILD は本体と同じ理由でビルドディレクトリ相対名だけを使う。
add_custom_command(TARGET ${BLINK_TARGET}.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex
            $<TARGET_FILE_NAME:${BLINK_TARGET}.elf>
            ${BLINK_TARGET}.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary
            $<TARGET_FILE_NAME:${BLINK_TARGET}.elf>
            ${BLINK_TARGET}.bin
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE_NAME:${BLINK_TARGET}.elf>
    COMMENT "Generating blink HEX/BIN images and reporting image size"
)

# Independent STM32F405 image; never link G474 platform/startup into this target.
add_executable(blink_f405.elf src/blink_f405/main.c src/blink_f405/startup.s)
set_target_properties(blink_f405.elf PROPERTIES OUTPUT_NAME blink_f405 SUFFIX .elf)
target_compile_options(blink_f405.elf PRIVATE ${MCU_FLAGS}
    -Wall -Wextra -Wpedantic -Og -g3 -ffunction-sections -fdata-sections)
target_link_options(blink_f405.elf PRIVATE ${MCU_FLAGS}
    -T${CMAKE_CURRENT_SOURCE_DIR}/linker/STM32F405RG_BLINK.ld
    -nostdlib -Wl,--gc-sections -Wl,--print-memory-usage
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/blink_f405.map)
target_link_libraries(blink_f405.elf PRIVATE gcc)
add_custom_command(TARGET blink_f405.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE_NAME:blink_f405.elf> blink_f405.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE_NAME:blink_f405.elf> blink_f405.bin
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE_NAME:blink_f405.elf>)

add_executable(amt102_f405.elf
    src/platform/amt102_f405_bringup.c src/blink_f405/startup.s)
set_target_properties(amt102_f405.elf PROPERTIES OUTPUT_NAME amt102_f405 SUFFIX .elf)
target_compile_options(amt102_f405.elf PRIVATE ${MCU_FLAGS}
    -Wall -Wextra -Wpedantic -Og -g3 -ffunction-sections -fdata-sections)
target_link_options(amt102_f405.elf PRIVATE ${MCU_FLAGS}
    -T${CMAKE_CURRENT_SOURCE_DIR}/linker/STM32F405RG_BLINK.ld
    -nostdlib -Wl,--gc-sections -Wl,--print-memory-usage
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/amt102_f405.map)
target_link_libraries(amt102_f405.elf PRIVATE gcc)
add_custom_command(TARGET amt102_f405.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE_NAME:amt102_f405.elf> amt102_f405.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE_NAME:amt102_f405.elf> amt102_f405.bin
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE_NAME:amt102_f405.elf>)

# Standalone V1 ODOM CAN diagnostics (no application/motor code).
add_executable(can_f405.elf src/platform/can_f405_bringup.c src/blink_f405/startup.s)
set_target_properties(can_f405.elf PROPERTIES OUTPUT_NAME can_f405 SUFFIX .elf)
target_compile_options(can_f405.elf PRIVATE ${MCU_FLAGS}
    -Wall -Wextra -Wpedantic -Og -g3 -ffunction-sections -fdata-sections)
target_link_options(can_f405.elf PRIVATE ${MCU_FLAGS}
    -T${CMAKE_CURRENT_SOURCE_DIR}/linker/STM32F405RG_BLINK.ld
    -nostdlib -Wl,--gc-sections -Wl,--print-memory-usage
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/can_f405.map)
target_link_libraries(can_f405.elf PRIVATE gcc)
add_custom_command(TARGET can_f405.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE_NAME:can_f405.elf> can_f405.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE_NAME:can_f405.elf> can_f405.bin
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE_NAME:can_f405.elf>)
