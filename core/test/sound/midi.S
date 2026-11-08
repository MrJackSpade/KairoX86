/*
 * KairoX86's MIDI test machine (KairoX86#306): a floppy boot sector that puts the MPU-401 at 330h in
 * UART mode and plays notes on MIDI channel 2 without end, one every nine timer ticks (about half a
 * second): General MIDI System On (a SysEx, which an MT-32 ignores), the program of a piano, then
 * middle C, E, G and C up an octave, each let go before the next with a note on of velocity 0 under
 * running status (no status byte), as many games write it. Channel 2 is the first part of an MT-32 or
 * CM-32L as it starts and a piano in General MIDI,
 * so the machine's MIDI out device (none, Munt or FluidSynth) is heard, or measured in the sound a
 * run writes. It shows M.
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
    movb    $'M', %al
    xorw    %bx, %bx
    int     $0x10

    /* UART mode: the command at 331h once the MPU-401 takes one; its acknowledgement (FEh) read */
1:  movw    $0x331, %dx
    inb     %dx, %al
    testb   $0x40, %al          /* DRR: the MPU-401 cannot take a byte yet */
    jnz     1b
    movb    $0x3f, %al
    outb    %al, %dx
2:  inb     %dx, %al
    testb   $0x80, %al          /* DSR: no byte to read yet */
    jnz     2b
    movw    $0x330, %dx
    inb     %dx, %al

    movw    $gm_on, %si         /* General MIDI System On */
    movw    $6, %cx
sysex:
    lodsb
    call    send
    loop    sysex
    movb    $0xc1, %al          /* program change, channel 2: acoustic grand piano */
    call    send
    xorb    %al, %al
    call    send

restart:
    movw    $notes, %si
note:
    movb    (%si), %bl
    orb     %bl, %bl
    jz      restart
    movb    $0x91, %al          /* note on, channel 2 */
    call    send
    movb    %bl, %al
    call    send
    movb    $100, %al           /* velocity */
    call    send
    movw    $9, %cx
wait:
    hlt                         /* a timer tick */
    loop    wait
    movb    %bl, %al            /* let go: the note again under running status, velocity 0 */
    call    send
    xorb    %al, %al
    call    send
    incw    %si
    jmp     note

/* Sends %al to the MPU-401's data port once it takes a byte. */
send:
    pushw   %ax
    movw    $0x331, %dx
3:  inb     %dx, %al
    testb   $0x40, %al
    jnz     3b
    popw    %ax
    movw    $0x330, %dx
    outb    %al, %dx
    ret

notes:
    .byte   60, 64, 67, 72, 0
gm_on:
    .byte   0xf0, 0x7e, 0x7f, 0x09, 0x01, 0xf7

    .org    510
    .byte   0x55, 0xaa
