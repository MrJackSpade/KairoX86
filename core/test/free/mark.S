/*
 * The free machine's boot order test (KairoX86#446, make_free.py): a boot sector that prints its
 * letter (MARK) and halts with interrupts off at 7C00h + 40h * SLOT, so the stop's address says which
 * disk the BIOS booted (floppy, hard disk or CD) whatever segment it jumped in with.
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
    movb    $0x0e, %ah
    movb    $MARK, %al
    xorw    %bx, %bx
    int     $0x10
    cli
    ljmp    $0x0000, $(0x7c00 + 0x40 * SLOT)

    .org    0x40 * SLOT
stop:
    hlt
    jmp     stop

    .org    510
    .byte   0x55, 0xaa
