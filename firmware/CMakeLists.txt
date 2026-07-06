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
    src/control/unit_controller.c
    src/platform/amt22.c
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
