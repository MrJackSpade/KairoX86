/*
 * KairoX86's character-height test (KairoX86#283, for #316): the BIOS's 80- and 40-column text, the screen filled with
 * every character and attribute, at character heights (CRTC register 9) of 4, 12, 16 and the BIOS's 8, each held a
 * few ticks of the BIOS clock. The 82C425 (Victor V86P) draws as many dots of a cell as its character height, so its
 * cells come out short or run into the next. 8086 instructions only (rt86.S).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .text
/* heights: CRTC register 9 to AL, then held */
height:
    pushw   %ax
    pushw   %dx
    movb    %al, %ah
    movw    $0x3d4, %dx
    movb    $9, %al
    outb    %al, %dx
    incw    %dx
    movb    %ah, %al
    outb    %al, %dx
    movw    $4, %ax
    call    wait_ticks
    popw    %dx
    popw    %ax
    ret

/* fill: every character and attribute over the 4000 bytes at B800:0 */
fill:
    pushw   %ax
    pushw   %cx
    pushw   %di
    movw    $0xb800, %ax
    movw    %ax, %es
    xorw    %di, %di
    xorw    %ax, %ax
    movw    $2000, %cx
1:  stosw
    incb    %al
    addb    $0x1d, %ah
    loop    1b
    popw    %di
    popw    %cx
    popw    %ax
    ret

/* one mode (AX) through the heights */
mode:
    int     $0x10
    call    fill
    movb    $3, %al
    call    height
    movb    $11, %al
    call    height
    movb    $15, %al
    call    height
    movb    $7, %al
    call    height
    ret

    .globl  test_main
test_main:
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    $0x0003, %ax
    call    mode
    movw    $0x0001, %ax
    call    mode
    movw    $0x0003, %ax
    int     $0x10
    ret
