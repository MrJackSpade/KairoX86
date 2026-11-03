/*
 * KairoX86's direct touch test (KairoX86#44): a floppy boot sector holding a DOS mouse game and its
 * mouse driver at their simplest. The driver (INT 33h) keeps a position: "set the position" (AX=04h)
 * stores CX and DX, "get the position and buttons" (AX=03h) gives them back with BX, and the spans
 * (AX=07h, 08h) are taken and ignored. The game asks for the position over and over and shows it at
 * the top left: "M", then X and Y as four hex digits each, then the buttons.
 *
 * MODE when it is assembled (core/test/input/make_place.py):
 *   MODE_TEXT   80x25 text, the driver's span left at its default (640x200).
 *   MODE_RANGE  80x25 text, the game setting the span to X 0-999 and Y 0-499.
 *   MODE_VGA    320x200 in 256 colours (mode 13h), the default span (640x200).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#define MODE_TEXT  1
#define MODE_RANGE 2
#define MODE_VGA   3

    .code16
    .text
    .globl _start
_start:
    cli
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    %ax, %ss
    movw    $0x7c00, %sp
    movw    $driver, 0x33 * 4   /* the mouse driver's vector */
    movw    $0, 0x33 * 4 + 2
    sti
#if MODE == MODE_VGA
    movw    $0x0013, %ax
#else
    movw    $0x0003, %ax
#endif
    int     $0x10
#if MODE == MODE_RANGE
    movw    $0x07, %ax
    xorw    %cx, %cx
    movw    $999, %dx
    int     $0x33
    movw    $0x08, %ax
    xorw    %cx, %cx
    movw    $499, %dx
    int     $0x33
#endif

again:
    movw    $0x03, %ax          /* get the position and buttons */
    int     $0x33
    pushw   %bx
    pushw   %dx
    pushw   %cx
    movb    $0x02, %ah          /* the cursor to the top left */
    xorb    %bh, %bh
    xorw    %dx, %dx
    int     $0x10
    movb    $'M', %al
    call    putc
    popw    %cx
    call    puthex
    popw    %cx
    call    puthex
    popw    %cx
    call    puthex
    jmp     again

/* The mouse driver. */
driver:
    cmpw    $0x03, %ax
    jne     1f
    movw    pos_x, %cx
    movw    pos_y, %dx
    xorw    %bx, %bx
    iret
1:  cmpw    $0x04, %ax
    jne     2f
    movw    %cx, pos_x
    movw    %dx, pos_y
2:  iret

/* AL as a character at the cursor (BIOS teletype). */
putc:
    pushw   %bx
    movb    $0x0e, %ah
    movw    $0x000f, %bx        /* page 0, white in graphics modes */
    int     $0x10
    popw    %bx
    ret

/* A space, then CX as four hex digits. */
puthex:
    movb    $' ', %al
    call    putc
    movb    $4, %dl
1:  rolw    $4, %cx
    movb    %cl, %al
    andb    $0x0f, %al
    addb    $'0', %al
    cmpb    $'9', %al
    jbe     2f
    addb    $7, %al
2:  pushw   %dx
    call    putc
    popw    %dx
    decb    %dl
    jnz     1b
    ret

pos_x:
    .word   0
pos_y:
    .word   0

    .org    510
    .byte   0x55, 0xaa
