/*
 * KairoX86's raw keyboard test machine (KairoX86#114): a floppy boot sector that takes the keyboard
 * interrupt (IRQ 1, INT 9) itself and shows every byte the keyboard sends, in hex and a space: a
 * key's make code when it goes down and its break code (the make code + 80h) when it comes up. A key
 * the guest never sees released shows a make code with no break code after it.
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
    movw    $0x0003, %ax        /* 80x25 text */
    int     $0x10
    movw    $irq1, 0x24         /* INT 9's vector, at 0000:0024 */
    movw    %ds, 0x26
    sti
    movb    $'R', %al
    call    putc

again:
    hlt                         /* until an interrupt, as the keyboard's */
    movb    head, %al
    cmpb    tail, %al
    je      again
    xorb    %bh, %bh
    movb    tail, %bl
    movb    buffer(%bx), %dl
    incb    %bl
    andb    $0x0f, %bl
    movb    %bl, tail
    movb    %dl, %al
    shrb    $4, %al
    call    puthex
    movb    %dl, %al
    andb    $0x0f, %al
    call    puthex
    movb    $' ', %al
    call    putc
    jmp     again

/* The keyboard's byte from port 60h into the 16-byte ring; then the end of interrupt. */
irq1:
    pushw   %ax
    pushw   %bx
    pushw   %ds
    xorw    %ax, %ax
    movw    %ax, %ds
    inb     $0x60, %al
    xorb    %bh, %bh
    movb    head, %bl
    movb    %al, buffer(%bx)
    incb    %bl
    andb    $0x0f, %bl
    movb    %bl, head
    movb    $0x20, %al
    outb    %al, $0x20
    popw    %ds
    popw    %bx
    popw    %ax
    iret

/* AL's low four bits as a hex digit at the cursor. */
puthex:
    addb    $'0', %al
    cmpb    $'9', %al
    jbe     1f
    addb    $7, %al
1:  call    putc
    ret

/* AL as a character at the cursor (BIOS teletype). */
putc:
    pushw   %bx
    movb    $0x0e, %ah
    xorw    %bx, %bx
    int     $0x10
    popw    %bx
    ret

head:   .byte 0
tail:   .byte 0
buffer: .fill 16, 1, 0

    .org    510
    .byte   0x55, 0xaa
