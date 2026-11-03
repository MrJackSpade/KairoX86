/*
 * KairoX86's mouse test (KairoX86#50): a floppy boot sector that reads the mouse straight from its
 * port, as DOS games' own mouse code does, and shows what it reads, so the host's pointer can be
 * checked reaching the machine's mouse.
 *
 * MODE when it is assembled (core/test/input/make_mouse.py):
 *   MODE_PS2     The PS/2 mouse on the keyboard controller's auxiliary port (60h/64h), with data
 *                reporting enabled, polled with interrupts off.
 *   MODE_SERIAL  A Microsoft serial mouse on COM1 (3F8h), 1200 baud 7N1, DTR and RTS raised.
 *
 * Over and over, at the top left of the screen: "P" (PS/2) or "S" (serial), the left, right and
 * middle buttons ('1' pressed, '0' not), then the sum of every packet's X and Y motion so far (four
 * hex digits each, from 0000). The serial mouse's Y grows downwards, the PS/2 mouse's upwards.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#define MODE_PS2    1
#define MODE_SERIAL 2

    .code16
    .text
    .globl _start
_start:
    cli
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    %ax, %ss
    movw    $0x7c00, %sp
    movw    $0x0003, %ax        /* 80x25 text */
    int     $0x10
    xorw    %si, %si            /* the X sum */
    xorw    %di, %di            /* the Y sum */
    xorb    %bl, %bl            /* the buttons: bit 0 left, 1 right, 2 middle */

#if MODE == MODE_PS2
    call    flush
    movb    $0x20, %al          /* read the controller's command byte */
    call    command
    call    readbyte
    andb    $0xdc, %al          /* no keyboard or mouse interrupts (bits 0, 1), the mouse's clock on (bit 5) */
    movb    %al, %ah
    movb    $0x60, %al          /* write it back */
    call    command
    movb    %ah, %al
    call    data
    movb    $0xa8, %al          /* the auxiliary port on */
    call    command
    movb    $0xd4, %al          /* to the mouse: enable data reporting */
    call    command
    movb    $0xf4, %al
    call    data
1:  call    readbyte            /* its acknowledge */
    cmpb    $0xfa, %al
    jne     1b
#else
    movw    $0x3fb, %dx
    movb    $0x80, %al          /* the divisor latch */
    outb    %al, %dx
    movw    $0x3f8, %dx
    movb    $96, %al            /* 115200 / 96: 1200 baud */
    outb    %al, %dx
    incw    %dx
    xorb    %al, %al
    outb    %al, %dx
    movw    $0x3fb, %dx
    movb    $0x02, %al          /* 7 data bits, no parity, 1 stop bit */
    outb    %al, %dx
    movw    $0x3f9, %dx
    xorb    %al, %al            /* no interrupts */
    outb    %al, %dx
    movw    $0x3fc, %dx
    movb    $0x03, %al          /* DTR and RTS: the mouse powers up and sends "M" */
    outb    %al, %dx
#endif

    xorw    %bp, %bp            /* bytes of the packet so far */
show:
    movb    $0x02, %ah          /* the cursor to the top left */
    xorb    %bh, %bh
    xorw    %dx, %dx
    int     $0x10
#if MODE == MODE_PS2
    movb    $'P', %al
#else
    movb    $'S', %al
#endif
    call    putc
    movb    $0x01, %bh
2:  movb    $'1', %al
    testb   %bh, %bl
    jnz     3f
    movb    $'0', %al
3:  call    putc
    shlb    $1, %bh
    cmpb    $0x08, %bh
    jne     2b
    movw    %si, %cx
    call    puthex
    movw    %di, %cx
    call    puthex

next:
#if MODE == MODE_PS2
    inb     $0x64, %al
    testb   $0x01, %al
    jz      next
    movb    %al, %ah
    inb     $0x60, %al
    testb   $0x20, %ah          /* a keyboard byte: not the mouse's */
    jz      next
    testw   %bp, %bp
    jnz     5f
    testb   $0x08, %al          /* a packet's first byte always has bit 3 */
    jz      next
#else
    movw    $0x3fd, %dx
    inb     %dx, %al
    testb   $0x01, %al
    jz      next
    movw    $0x3f8, %dx
    inb     %dx, %al
    testb   $0x40, %al          /* a packet's first byte, and only it, has bit 6 */
    jz      4f
    xorw    %bp, %bp
    jmp     5f
4:  testw   %bp, %bp            /* a byte before any packet's first */
    jz      next
#endif
5:  movb    %al, packet(%bp)
    incw    %bp
    cmpw    $3, %bp
    jne     next
    xorw    %bp, %bp

#if MODE == MODE_PS2
    movb    packet, %bl
    movb    %bl, %ah
    andb    $0x07, %bl          /* left, right, middle */
    movb    packet+1, %al       /* X: a 9-bit two's complement with its sign in bit 4 */
    cbw
    testb   $0x10, %ah
    jnz     6f
    xorb    %ah, %ah
    jmp     7f
6:  movb    $0xff, %ah
7:  addw    %ax, %si
    movb    packet, %ah
    movb    packet+2, %al       /* Y: its sign in bit 5 */
    testb   $0x20, %ah
    jnz     8f
    xorb    %ah, %ah
    jmp     9f
8:  movb    $0xff, %ah
9:  addw    %ax, %di
#else
    movb    packet, %ah
    xorb    %bl, %bl            /* left in bit 5, right in bit 4 */
    testb   $0x20, %ah
    jz      6f
    orb     $0x01, %bl
6:  testb   $0x10, %ah
    jz      7f
    orb     $0x02, %bl
7:  movb    %ah, %al            /* X: its top two bits in bits 0 and 1 */
    shlb    $6, %al
    orb     packet+1, %al
    cbw
    addw    %ax, %si
    movb    packet, %al         /* Y: its top two bits in bits 2 and 3 */
    shlb    $4, %al
    andb    $0xc0, %al
    orb     packet+2, %al
    cbw
    addw    %ax, %di
#endif
    jmp     show

#if MODE == MODE_PS2
/* Waits until the controller takes a byte, then sends AL as a command (64h) or data (60h). */
command:
    pushw   %ax
1:  inb     $0x64, %al
    testb   $0x02, %al
    jnz     1b
    popw    %ax
    outb    %al, $0x64
    ret
data:
    pushw   %ax
1:  inb     $0x64, %al
    testb   $0x02, %al
    jnz     1b
    popw    %ax
    outb    %al, $0x60
    ret
/* Waits for the controller's next byte, into AL. */
readbyte:
1:  inb     $0x64, %al
    testb   $0x01, %al
    jz      1b
    inb     $0x60, %al
    ret
/* Drops what the controller already holds. */
flush:
1:  inb     $0x64, %al
    testb   $0x01, %al
    jz      2f
    inb     $0x60, %al
    jmp     1b
2:  ret
#endif

/* AL as a character at the cursor (BIOS teletype). */
putc:
    pushw   %bx
    movb    $0x0e, %ah
    xorw    %bx, %bx
    int     $0x10
    popw    %bx
    ret

/* A space, then CX as four hex digits. */
puthex:
    movb    $' ', %al
    call    putc
    movb    $4, %dl
1:  rolw    $4, %cx
    movb    %cl, %al
    andb    $0x0f, %al
    addb    $'0', %al
    cmpb    $'9', %al
    jbe     2f
    addb    $7, %al
2:  pushw   %dx
    call    putc
    popw    %dx
    decb    %dl
    jnz     1b
    ret

packet:
    .byte   0, 0, 0

    .org    510
    .byte   0x55, 0xaa
