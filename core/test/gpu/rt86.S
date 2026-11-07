/*
 * The runtime of KairoX86's graphics tests for 8086 machines (KairoX86#283, for #311-#324): the PCjr, PC JX,
 * Tandy, Amstrad, Toshiba and other 8088/8086/80186/286 machines, which runtime.c's 32-bit code cannot run on. A test is
 * an assembly file (<name>.S here) of 8086 instructions only (shifts by 1 or CL, no immediate pushes) whose test_main
 * the entry below calls. The end is runtime.c's: a HLT with interrupts off at the same fixed address, so compare.py's
 * TEST_END holds for both.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .section .text.entry, "ax"
    .globl _start
_start:
    jmp     2f
1:  cli
    hlt
    jmp     1b
2:  cld
    call    test_main
    jmp     1b

    .text
/* wait_ticks: waits for AX ticks of the BIOS clock (40:6Ch) to begin; DS must be 0 */
    .globl  wait_ticks
wait_ticks:
    pushw   %bx
    pushw   %cx
    movw    %ax, %cx
3:  movw    0x046c, %bx
4:  cmpw    0x046c, %bx
    je      4b
    loop    3b
    popw    %cx
    popw    %bx
    ret

/* fill_pattern: fills CX bytes at ES:0 with a pattern of each byte's offset and BL (the salt) */
    .globl  fill_pattern
fill_pattern:
    pushw   %ax
    pushw   %cx
    pushw   %di
    xorw    %di, %di
5:  movw    %di, %ax
    xorb    %ah, %al
    addb    %bl, %al
    rolb    $1, %al
    xorb    %bl, %al
    stosb
    loop    5b
    popw    %di
    popw    %cx
    popw    %ax
    ret
