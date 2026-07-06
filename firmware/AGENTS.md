# Firmware editing guide

- Primary test target: STM32G474CE on Matek CAN-G474. Fallback/regression target: STM32G474RET6 on NUCLEO-G474RE.
- Keep board-specific pin maps separate. CAN-G474 uses CAN1 PA11/PA12, CAN2 PB5/PB6, and exposed SPI2 PB13/PB14/PB15 with PB12 as the candidate AMT22 CS; the existing NUCLEO map differs.
- Current behavior: B1 USER (PC13, active high) controls LD2 (PA5, active high).
- The custom board will use an STM32G4-family MCU; keep board pin mapping isolated in `src/platform/gpio.c`.
- Keep hardware-specific code in `src/platform/` and public interfaces in `include/platform/`.
- Keep application policy and control logic out of the platform layer.
- Add every new source file explicitly to `firmware/CMakeLists.txt`.
- Build only under `firmware/build/`; do not generate into source directories.
- Preserve the Cortex-M4F hard-float flags. Recheck linker memory sizes when the custom-board MCU is selected.
- Before handoff, run `firmware/scripts/build.ps1`.
- Match interrupt handlers to exact vector-table slots before enabling an IRQ.
- Read `firmware/docs/BOARD_BRINGUP.md` before hardware tests or programming changes.
- Read `firmware/PROGRESS.md` before continuing work in a new session.
- Treat CLI success as insufficient; verify target-side execution with an observable output or SRAM marker.
