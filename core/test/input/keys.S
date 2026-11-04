/*
 * KairoX86's keyboard game stand-ins for the Auto touch mode (KairoX86#43): a floppy boot sector
 * that reads keys through the BIOS (INT 16h) the two ways DOS games do, and shows each key it gets.
 *
 * MODE when it is assembled (core/test/input/make_auto.py):
 *   MODE_WAIT  Get a keystroke (AH=00h), which waits in the BIOS until a key comes.
 *   MODE_POLL  Check for a keystroke (AH=01h) over and over, and get it once there is one.
 *   MODE_SCAN  As MODE_WAIT, showing each key's scan code in hex and a space, for keys with no
 *              character (the cursor keys) as for the rest (core/test/input/make_keys.py, KairoX86#95).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#define MODE_WAIT 1
#define MODE_POLL 2
#define MODE_SCAN 3

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
#elif MODE == MODE_SCAN
    movb    $'S', %al
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
#if MODE == MODE_SCAN
    movb    %ah, %dl
    shrb    $4, %ah
    movb    %ah, %al
    call    puthex
    movb    %dl, %al
    andb    $0x0f, %al
    call    puthex
    movb    $' ', %al
#endif
    call    putc
    jmp     again

#if MODE == MODE_SCAN
/* AL's low four bits as a hex digit at the cursor. */
puthex:
    addb    $'0', %al
    cmpb    $'9', %al
    jbe     1f
    addb    $7, %al
1:  call    putc
    ret
#endif

/* AL as a character at the cursor (BIOS teletype). */
putc:
    movb    $0x0e, %ah
    xorw    %bx, %bx
    int     $0x10
    ret

    .org    510
    .byte   0x55, 0xaa
