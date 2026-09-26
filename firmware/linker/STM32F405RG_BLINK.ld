ENTRY(Reset_Handler)
MEMORY
{
    /* Blink is confined to sector 0; remaining flash is not part of image. */
    FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 16K
    RAM (xrw) : ORIGIN = 0x20000000, LENGTH = 128K
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS
{
    .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
    .text : { *(.text*) *(.rodata*) . = ALIGN(4); } > FLASH
    .ARM.exidx : { *(.ARM.exidx*) } > FLASH
    .diagnostic (NOLOAD) : {
        _sbss = .; KEEP(*(.diagnostic))
    } > RAM
    .bss (NOLOAD) : {
        *(.bss*) *(COMMON) . = ALIGN(4); _ebss = .;
    } > RAM
    _sidata = LOADADDR(.data);
    .data : { _sdata = .; *(.data*) . = ALIGN(4); _edata = .; } > RAM AT > FLASH
    /DISCARD/ : { *(.note.GNU-stack) }
}
ASSERT(_edata + 1024 <= _estack, "RAM overflow")
