/*
 * KairoX86's horizontal-position test (KairoX86#283, for #321): the BIOS's 80- and 40-column text and its 320 x 200 x
 * 4 graphics, each filled with a pattern, then the picture moved left past the line's start through the CRTC's
 * horizontal sync position (register 2 moved two and then five characters on, clipping the left of the picture on
 * the Tandy 1000), each held a few ticks of the BIOS clock. 8086 instructions only (rt86.S).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .text
/* hsync: CRTC register 2 to AL, then held */
hsync:
    pushw   %ax
    pushw   %dx
    movb    %al, %ah
    movw    $0x3d4, %dx
    movb    $2, %al
    outb    %al, %dx
    incw    %dx
    movb    %ah, %al
    outb    %al, %dx
    movw    $4, %ax
    call    wait_ticks
    popw    %dx
    popw    %ax
    ret

/* one mode (AX), its register 2 the BIOS's (BL) and two and five characters on */
mode:
    int     $0x10
    movw    $0xb800, %ax
    movw    %ax, %es
    movw    $0x4000, %cx
    pushw   %bx
    movb    $0x6b, %bl
    call    fill_pattern
    popw    %bx
    movw    $4, %ax
    call    wait_ticks
    movb    %bl, %al
    addb    $2, %al
    call    hsync
    movb    %bl, %al
    addb    $5, %al
    call    hsync
    movb    %bl, %al
    call    hsync
    ret

    .globl  test_main
test_main:
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    $0x0003, %ax
    movb    $0x5a, %bl
    call    mode
    movw    $0x0001, %ax
    movb    $0x2d, %bl
    call    mode
    movw    $0x0004, %ax
    movb    $0x2d, %bl
    call    mode
    movw    $0x0003, %ax
    int     $0x10
    ret
