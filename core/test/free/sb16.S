/*
 * The free machine's Sound Blaster test (KairoX86#446, make_free.py): a boot sector that resets the
 * Sound Blaster 16's DSP at 220h, turns its speaker on (D1h) and plays a 500 Hz square wave through
 * its direct DAC (command 10h), each half wave timed by PIT channel 2's output (port 61h bit 5, with
 * the PC speaker itself off). It shows "S" first; a DSP that does not answer its reset shows "X"
 * and halts with interrupts off.
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
    movw    $0x0e53, %ax        /* "S" */
    xorw    %bx, %bx
    int     $0x10

    movw    $0x226, %dx         /* DSP reset: 1, a pause, 0 */
    movb    $1, %al
    outb    %al, %dx
    movw    $100, %cx
1:
    inb     %dx, %al
    loop    1b
    xorb    %al, %al
    outb    %al, %dx
    movw    $0xffff, %cx
ready:
    movw    $0x22e, %dx         /* read buffer status */
    inb     %dx, %al
    testb   $0x80, %al
    jnz     answered
    loop    ready
    jmp     failed
answered:
    movw    $0x22a, %dx
    inb     %dx, %al
    cmpb    $0xaa, %al
    jne     failed

    movb    $0xd1, %ah          /* speaker on */
    call    dsp_write

    movb    $0xb6, %al          /* PIT channel 2, lobyte/hibyte, mode 3: 500 Hz */
    outb    %al, $0x43
    movw    $2386, %ax
    outb    %al, $0x42
    movb    %ah, %al
    outb    %al, $0x42
    inb     $0x61, %al
    andb    $0xfc, %al
    orb     $0x01, %al          /* channel 2's gate on, the PC speaker off */
    outb    %al, $0x61

play:
    inb     $0x61, %al
    movb    $0x40, %bl
    testb   $0x20, %al          /* channel 2's output */
    jz      1f
    movb    $0xc0, %bl
1:
    movb    $0x10, %ah          /* direct DAC: the sample next */
    call    dsp_write
    movb    %bl, %ah
    call    dsp_write
    jmp     play

dsp_write:                      /* AH to the DSP once it takes a byte */
    movw    $0x22c, %dx
1:
    inb     %dx, %al
    testb   $0x80, %al
    jnz     1b
    movb    %ah, %al
    outb    %al, %dx
    ret

failed:
    movw    $0x0e58, %ax        /* "X" */
    xorw    %bx, %bx
    int     $0x10
    cli
1:
    hlt
    jmp     1b

    .org    510
    .byte   0x55, 0xaa
