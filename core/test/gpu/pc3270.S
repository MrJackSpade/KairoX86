/*
 * KairoX86's 3270 PC APA readback test (KairoX86#283, for #311): the APA board's native modes (port 196h bit 3 over the
 * BIOS's 640 x 200 x 2 and 320 x 200 x 4), the 32K buffer at B800:0 filled with a pattern, with the diagnostic readback
 * armed (port 189h bit 5): held a few ticks of the BIOS clock, its latches (port 188h) then read into 0:0600h so the
 * guest's state carries them. 8086 instructions only (rt86.S).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
    .code16
    .text
/* one mode (AX): native, armed, held, the latches read into [DI] */
apa:
    int     $0x10
    movw    $0xb800, %ax
    movw    %ax, %es
    movw    $0x8000, %cx
    movb    $0x2c, %bl
    call    fill_pattern
    movw    $0x196, %dx
    movb    $0x08, %al
    outb    %al, %dx
    movw    $0x189, %dx
    movb    $0x20, %al
    outb    %al, %dx
    movw    $4, %ax
    call    wait_ticks
    movw    $0x188, %dx
    inb     %dx, %al
    movb    %al, (%di)
    incw    %di
    movw    $0x189, %dx
    xorb    %al, %al
    outb    %al, %dx
    movw    $0x196, %dx
    xorb    %al, %al
    outb    %al, %dx
    ret

    .globl  test_main
test_main:
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    $0x0600, %di
    movw    $0x0006, %ax
    call    apa
    movw    $0x0004, %ax
    call    apa
    movw    $0x0003, %ax
    int     $0x10
    ret
