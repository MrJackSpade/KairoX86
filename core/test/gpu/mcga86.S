/*
 * KairoX86's MCGA test for the PS/2 Model 25 and 30 (KairoX86#283, for #318): the MCGA's own modes set through the
 * BIOS, each held four ticks of the BIOS clock: 640 x 480 x 2 (mode 11h, 38400 bytes at A000:0) and 320 x 200 x 256
 * (mode 13h, 64000 bytes at A000:0), each filled with a pattern, then mode 13h with its DAC's first 64 colours
 * rewritten (3C8h/3C9h). Any machine whose BIOS lacks the modes keeps the mode before. 8086 instructions only (rt86.S).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .text
    .globl  test_main
test_main:
    xorw    %ax, %ax
    movw    %ax, %ds
    /* 640 x 480 x 2 */
    movw    $0x0011, %ax
    int     $0x10
    movw    $0xa000, %ax
    movw    %ax, %es
    movw    $38400, %cx
    movb    $0x51, %bl
    call    fill_pattern
    movw    $4, %ax
    call    wait_ticks
    /* 320 x 200 x 256 */
    movw    $0x0013, %ax
    int     $0x10
    movw    $0xa000, %ax
    movw    %ax, %es
    movw    $64000, %cx
    movb    $0x52, %bl
    call    fill_pattern
    movw    $4, %ax
    call    wait_ticks
    /* The DAC's first 64 colours: red, green and blue from the index */
    xorb    %al, %al
    movw    $0x3c8, %dx
    outb    %al, %dx
    incw    %dx
    xorb    %cl, %cl
1:  movb    %cl, %al
    outb    %al, %dx
    movb    $63, %al
    subb    %cl, %al
    outb    %al, %dx
    movb    %cl, %al
    xorb    $0x2a, %al
    andb    $63, %al
    outb    %al, %dx
    incb    %cl
    cmpb    $64, %cl
    jne     1b
    movw    $4, %ax
    call    wait_ticks
    movw    $0x0003, %ax
    int     $0x10
    xorw    %ax, %ax
    movw    %ax, %es
    ret
