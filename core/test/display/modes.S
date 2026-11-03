/*
 * KairoX86's native size test (KairoX86#37): a floppy boot sector that sets one video mode through the
 * BIOS and fills the screen with a pattern whose colour changes from each pixel to the next (graphics)
 * or with characters (text), then waits. The core must hand the host the mode's own pixels: one of
 * each pixel the card draws twice.
 *
 * MODE (the BIOS video mode), WIDTH and HEIGHT (its pixels, graphics only) when it is assembled
 * (core/test/display/make_modes.py).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .text
    .globl _start
_start:
    cli
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    %ax, %ss
    movw    $0x7c00, %sp
    sti
    movw    $MODE, %ax
    int     $0x10

#if (MODE <= 3) || (MODE == 7)
    /* Text: the printable characters in turn, over the screen. */
    movw    $2000, %cx
    xorw    %bx, %bx
1:  movw    %bx, %ax
    movb    $0x0e, %ah
    pushw   %bx
    pushw   %cx
    movb    $0x00, %bh
    andb    $0x7f, %al
    orb     $0x20, %al
    int     $0x10
    popw    %cx
    popw    %bx
    incw    %bx
    loop    1b
#else
    /* Graphics: the colour of each pixel is x + y. */
    xorw    %dx, %dx
2:  xorw    %cx, %cx
3:  movw    %cx, %ax
    addw    %dx, %ax
    movb    $0x0c, %ah
    xorb    %bh, %bh
    int     $0x10
    incw    %cx
    cmpw    $WIDTH, %cx
    jne     3b
    incw    %dx
    cmpw    $HEIGHT, %dx
    jne     2b
#endif

4:  hlt
    jmp     4b

    .org    510
    .byte   0x55, 0xaa
