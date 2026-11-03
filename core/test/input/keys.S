/*
 * KairoX86's keyboard game stand-ins for the Auto touch mode (KairoX86#43): a floppy boot sector
 * that reads keys through the BIOS (INT 16h) the two ways DOS games do, and shows each key it gets.
 *
 * MODE when it is assembled (core/test/input/make_auto.py):
 *   MODE_WAIT  Get a keystroke (AH=00h), which waits in the BIOS until a key comes.
 *   MODE_POLL  Check for a keystroke (AH=01h) over and over, and get it once there is one.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#define MODE_WAIT 1
#define MODE_POLL 2

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
#if MODE == MODE_WAIT
    movb    $'W', %al
#else
    movb    $'P', %al
#endif
    call    putc

again:
#if MODE == MODE_POLL
    movb    $0x01, %ah
    int     $0x16
    jz      again
#endif
    xorb    %ah, %ah
    int     $0x16
    call    putc
    jmp     again

/* AL as a character at the cursor (BIOS teletype). */
putc:
    movb    $0x0e, %ah
    xorw    %bx, %bx
    int     $0x10
    ret

    .org    510
    .byte   0x55, 0xaa
