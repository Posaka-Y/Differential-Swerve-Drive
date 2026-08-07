ENTRY(Reset_Handler)

MEMORY
{
  /* Keep the final 2 KiB page out of the firmware image. It is an append-only
     AMT software-zero store and must survive ordinary firmware updates. */
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 510K
  CALIB (r)   : ORIGIN = 0x0807F800, LENGTH = 2K
  /* G474RE has 96 KiB contiguous SRAM at 0x20000000 plus 32 KiB CCM SRAM. */
  RAM   (xrw) : ORIGIN = 0x20000000, LENGTH = 96K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);
_calibration_flash_start = ORIGIN(CALIB);
_Min_Heap_Size = 0;
_Min_Stack_Size = 0x400;

SECTIONS
{
  .isr_vector : { . = ALIGN(4); KEEP(*(.isr_vector)) . = ALIGN(4); } > FLASH
  .text :
  {
    . = ALIGN(4);
    *(.text .text* .rodata .rodata*)
    KEEP(*(.init)) KEEP(*(.fini))
    . = ALIGN(4);
    _etext = .;
  } > FLASH
  .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } > FLASH
  .ARM.exidx : { __exidx_start = .; *(.ARM.exidx*) __exidx_end = .; } > FLASH

  _sidata = LOADADDR(.data);
  .data :
  {
    . = ALIGN(4); _sdata = .;
    *(.data .data*)
    . = ALIGN(4); _edata = .;
  } > RAM AT > FLASH
  .bss (NOLOAD) :
  {
    . = ALIGN(4); _sbss = .;
    *(.bss .bss* COMMON)
    . = ALIGN(4); _ebss = .;
  } > RAM
  ._user_heap_stack (NOLOAD) :
  {
    . = ALIGN(8); PROVIDE(end = .); PROVIDE(_end = .);
    . += _Min_Heap_Size; . += _Min_Stack_Size; . = ALIGN(8);
  } > RAM
  /DISCARD/ : { *(.note.GNU-stack) *(.gnu_debuglink) }
}

ASSERT(_estack >= ADDR(._user_heap_stack) + SIZEOF(._user_heap_stack), "RAM overflow")
ASSERT(_etext <= ORIGIN(CALIB), "FLASH overlaps calibration page")
