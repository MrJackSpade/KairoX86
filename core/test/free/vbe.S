/*
 * The free machine's VBE test (KairoX86#446, make_free.py): a boot sector that sets VESA mode 101h
 * (640x480, 256 colours) through the video BIOS's VBE (INT 10h AX=4F02h) and fills it through window
 * A, 64 KB at a time (AX=4F05h, its position in units of the mode's window granularity, AX=4F01h),
 * with a pattern of each pixel's offset in its 64 KB (its high byte) and which 64 KB it is in. The
 * same picture on SeaVGABIOS and on a card's own BIOS shows the free BIOS sets the mode, its window
 * and its palette as a VBE BIOS does. A failed call shows "V" in text mode and halts with
 * interrupts off.
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
    movw    %ax, %es
    movw    %ax, %ss
    movw    $0x7c00, %sp
    sti
    movw    $0x4f01, %ax        /* the mode's information, at 0000:8000 */
    movw    $0x0101, %cx
    movw    $0x8000, %di
    int     $0x10
    cmpw    $0x004f, %ax
    jne     failed
    movw    0x8004, %bx         /* its window granularity, KB */
    testw   %bx, %bx
    jz      failed
    movw    $64, %ax
    xorw    %dx, %dx
    divw    %bx
    movw    %ax, step           /* window positions per 64 KB */
    movw    $0x4f02, %ax
    movw    $0x0101, %bx
    int     $0x10
    cmpw    $0x004f, %ax
    jne     failed
    movw    $0xa000, %ax
    movw    %ax, %es
    xorw    %si, %si            /* which 64 KB */
bank:
    movw    %si, %ax
    mulw    step
    movw    %ax, %dx            /* its window position */
    movw    $0x4f05, %ax
    xorw    %bx, %bx            /* window A, set */
    int     $0x10
    cmpw    $0x004f, %ax
    jne     failed
    xorw    %di, %di
    movw    %si, %dx
    shlb    $5, %dl
fill:
    movw    %di, %ax
    movb    %ah, %al            /* the offset's high byte */
    addb    %dl, %al            /* and which 64 KB */
    stosb
    testw   %di, %di
    jnz     fill
    incw    %si
    cmpw    $5, %si             /* 640x480 is 4.7 times 64 KB */
    jb      bank
wait:
    hlt
    jmp     wait

failed:
    movw    $0x0003, %ax
    int     $0x10
    movw    $0x0e56, %ax        /* "V" */
    xorw    %bx, %bx
    int     $0x10
    cli
1:
    hlt
    jmp     1b

step:
    .word   0

    .org    510
    .byte   0x55, 0xaa
