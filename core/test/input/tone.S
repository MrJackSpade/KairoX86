/*
 * KairoX86's sound test machine (KairoX86#117): a floppy boot sector that plays the PC speaker without
 * a pause, a square wave from PIT channel 2 whose pitch steps up each timer tick (18.2 a second) and
 * starts over, so a gap or a crackle in the sound is heard and shows as an underrun in the device's
 * audio output. It shows T and then ignores every key, mouse and joystick input it gets.
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
    movb    $0x0e, %ah
    movb    $'T', %al
    xorw    %bx, %bx
    int     $0x10
    movb    $0xb6, %al          /* PIT channel 2, lobyte/hibyte, mode 3 (square wave) */
    outb    %al, $0x43
    inb     $0x61, %al
    orb     $0x03, %al          /* the speaker on, driven by channel 2 */
    outb    %al, $0x61

restart:
    movw    $4000, %cx          /* about 298 Hz */
step:
    movw    %cx, %ax
    outb    %al, $0x42
    movb    %ah, %al
    outb    %al, $0x42
    hlt                         /* until the next interrupt: the timer, or input */
drain:                          /* keys are taken and dropped: a full BIOS buffer would beep */
    movb    $0x01, %ah
    int     $0x16
    jz      next
    xorb    %ah, %ah
    int     $0x16
    jmp     drain
next:
    subw    $40, %cx
    cmpw    $1000, %cx          /* up to about 1193 Hz */
    jae     step
    jmp     restart

    .org    510
    .byte   0x55, 0xaa
