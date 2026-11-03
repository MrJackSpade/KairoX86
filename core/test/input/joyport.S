/*
 * KairoX86's game port test (KairoX86#52): a floppy boot sector that reads the game port (201h) as
 * DOS games do and shows what it reads, so each game port line can be checked on its own.
 *
 * Over and over, at the top left of the screen: "B" and the four buttons B1 to B4 ('1' pressed, '0'
 * not), then for each axis X1, Y1, X2 and Y2 how many reads its one-shot stayed high after a write to
 * 201h started it (four hex digits; FFFF when it never fell: an axis no joystick drives).
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
    movw    $0x0003, %ax        /* 80x25 text */
    int     $0x10

again:
    movb    $0x02, %ah          /* the cursor to the top left */
    xorb    %bh, %bh
    xorw    %dx, %dx
    int     $0x10
    movb    $'B', %al
    call    putc
    movw    $0x201, %dx
    inb     %dx, %al
    movb    %al, %bl            /* the buttons: bits 4 to 7, 0 while pressed */
    movb    $0x10, %bh
1:  movb    $'1', %al
    testb   %bh, %bl
    jz      2f
    movb    $'0', %al
2:  call    putc
    shlb    $1, %bh
    jnz     1b

    movb    $0x01, %bh          /* each axis's bit */
axis:
    movb    $' ', %al
    call    putc
    movw    $0x201, %dx
    outb    %al, %dx            /* start the one-shots */
    xorw    %cx, %cx
3:  inb     %dx, %al
    testb   %bh, %al
    jz      4f
    incw    %cx
    cmpw    $0xffff, %cx
    jne     3b
4:  call    puthex
    /* wait for every one-shot to fall before the next */
    movw    $0x201, %dx
    movw    $0x8000, %si
5:  inb     %dx, %al
    testb   $0x0f, %al
    jz      6f
    decw    %si
    jnz     5b
6:  shlb    $1, %bh
    cmpb    $0x10, %bh
    jne     axis
    jmp     again

/* AL as a character at the cursor (BIOS teletype). */
putc:
    pushw   %bx
    movb    $0x0e, %ah
    xorw    %bx, %bx
    int     $0x10
    popw    %bx
    ret

/* CX as four hex digits. */
puthex:
    pushw   %cx
    movb    $4, %dl
7:  rolw    $4, %cx
    movb    %cl, %al
    andb    $0x0f, %al
    addb    $'0', %al
    cmpb    $'9', %al
    jbe     8f
    addb    $7, %al
8:  pushw   %dx
    call    putc
    popw    %dx
    decb    %dl
    jnz     7b
    popw    %cx
    ret

    .org    510
    .byte   0x55, 0xaa
