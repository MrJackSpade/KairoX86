/*
 * KairoX86's IBM 5550 test (KairoX86#283, for #324): its own display hardware, booted by its IPL as a load module
 * (make_tests.py ipl_5550_image; its IPL keeps no tick count at 40:6Ch, so each picture is held by a fixed delay loop,
 * the same in every run). The text plane's 2048 cells at E0000h, every character with attributes cycling through
 * highlight, reverse, underscore, the vertical and horizontal grid lines and blink (never invisible, never wide); then
 * the graphics mode (port 3D8h bit 1), its plane at A0000h filled through word writes; then text again. 8086
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
    /* The display's registers open */
    movw    $0x3d2, %dx
    outb    %al, %dx
    /* Text: each cell its character, its attribute from the table below */
    movw    $0xe000, %ax
    movw    %ax, %es
    xorw    %di, %di
    xorw    %bx, %bx
    movw    $2048, %cx
3:  movb    %bl, %al
    stosb
    movw    %bx, %si
    andw    $7, %si
    movb    %cs:attrs(%si), %al
    stosb
    incw    %bx
    loop    3b
    call    hold
    /* Graphics: the plane through word writes */
    movw    $0x3d8, %dx
    movb    $0x02, %al
    outb    %al, %dx
    movw    $0xa000, %ax
    movw    %ax, %es
    xorw    %di, %di
    xorw    %bx, %bx
    movw    $32768, %cx
4:  movw    %bx, %ax
    xorb    %ah, %al
    rolw    $1, %ax
    xorw    $0x5a3c, %ax
    stosw
    incw    %bx
    loop    4b
    call    hold
    /* Text again */
    movw    $0x3d8, %dx
    xorb    %al, %al
    outb    %al, %dx
    call    hold
    ret

/* The attributes: plain, highlight, reverse, underscore, vertical line, horizontal line, blink, highlight reverse */
attrs:
    .byte   0x00, 0x08, 0x04, 0x40, 0x10, 0x20, 0x80, 0x0c
