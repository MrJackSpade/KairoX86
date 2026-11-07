/*
 * KairoX86's Tandy 2000 test (KairoX86#283, for #322): its own video hardware, with no IBM-compatible BIOS calls (its
 * BIOS keeps no tick count at 40:6Ch, so each picture is held by a fixed delay loop instead, the same in every run):
 * 80 x 25 text from main RAM (the base at port 101h set to 01h: the cells at 0:EC00h), every character and attribute
 * (reverse, intensity, blink, blank), then the colour option's 640 x 400 graphics (port 1A0h bit 5 on), its three planes
 * each filled through the window at E000:0 (plane select bits 0-2) with the eight pens set (180h-18Eh). 8086
 * instructions only (rt86.S).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .text
/* hold: a fixed delay, the same in every run */
hold:
    pushw   %cx
    pushw   %dx
    movw    $40, %dx
1:  movw    $0xffff, %cx
2:  loop    2b
    decw    %dx
    jnz     1b
    popw    %dx
    popw    %cx
    ret

    .globl  test_main
test_main:
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    %ax, %es
    /* Text: the cells from 0:EC00h */
    movw    $0x101, %dx
    movb    $0x01, %al
    outb    %al, %dx
    movw    $0xec00, %di
    xorw    %bx, %bx
    movw    $2000, %cx
3:  movb    %bl, %al
    stosb
    movb    %bl, %al
    xorb    %bh, %al
    rolb    $1, %al
    stosb
    incw    %bx
    loop    3b
    call    hold
    /* The pens: 0, then 15 down */
    movw    $0x180, %dx
    xorb    %al, %al
    movb    $8, %cl
4:  outb    %al, %dx
    addw    $2, %dx
    addb    $0x0d, %al
    andb    $0x0f, %al
    decb    %cl
    jnz     4b
    /* Graphics: each plane through the window */
    movw    $0xe000, %ax
    movw    %ax, %es
    movw    $1, %si                 /* the plane's select bit */
    movb    $0x41, %bl              /* its salt (fill_pattern's) */
5:  movw    $0x1a0, %dx
    movw    %si, %ax
    orb     $0x20, %al
    outb    %al, %dx
    movw    $32000, %cx
    call    fill_pattern
    incb    %bl
    shlw    $1, %si
    cmpw    $8, %si
    jne     5b
    call    hold
    /* Text again */
    movw    $0x1a0, %dx
    xorb    %al, %al
    outb    %al, %dx
    xorw    %ax, %ax
    movw    %ax, %es
    call    hold
    ret
