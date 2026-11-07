/*
 * KairoX86's CGA-class test for 8086 machines (KairoX86#283, for #313, #316, #317, #319, #320, #321, #323 and the
 * Compaq Portable III's plasma, #312): each video mode set through the machine's BIOS, 32 KB at B800:0 filled with a
 * pattern, every picture held four ticks of the BIOS clock: 40- and 80-column text (modes 1 and 3) with the cursor
 * shown, 320 x 200 x 4 (mode 4) in both palettes, 640 x 200 x 2 (mode 6), and the PCjr and Tandy modes 160 x 200 x 16,
 * 320 x 200 x 16 and 640 x 200 x 4 (8, 9 and 0Ah); a BIOS without a mode keeps the one before, as it would for any
 * program. 8086 instructions only (rt86.S).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .text
    .globl  test_main
test_main:
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    $modes, %si
1:  movb    (%si), %al
    cmpb    $0xff, %al
    je      9f
    xorb    %ah, %ah
    int     $0x10                   /* the mode */
    movw    $0x0200, %ax            /* the cursor at row 5, column 9 */
    xorb    %bh, %bh
    movw    $0x0509, %dx
    int     $0x10
    movw    $0xb800, %ax
    movw    %ax, %es
    movw    $0x8000, %cx
    movb    1(%si), %bl             /* the salt */
    call    fill_pattern
    xorw    %ax, %ax
    movw    %ax, %es
    movw    $4, %ax
    call    wait_ticks
    cmpb    $4, (%si)               /* mode 4 again in its other palette */
    jne     2f
    movw    $0x0b01, %ax
    movw    $0x0101, %bx
    int     $0x10
    movw    $4, %ax
    call    wait_ticks
2:  addw    $2, %si
    jmp     1b
9:  movw    $0x0003, %ax
    int     $0x10
    ret

    .data
modes:
    .byte   0x01, 0x31, 0x03, 0x32, 0x04, 0x33, 0x06, 0x34, 0x08, 0x35, 0x09, 0x36, 0x0a, 0x37, 0xff
