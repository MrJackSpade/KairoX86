/*
 * KairoX86's raster test (KairoX86#38): a floppy boot sector that changes the picture while the
 * frame is being drawn, as games' raster effects do, so a renderer that draws lines later than the
 * guest scanned them shows the difference.
 *
 * VESA mode 101h (640x480, 256 colours, one byte a pixel: the lines KairoX86's threaded 8bpp
 * renderer draws), its first 64 KB bank (102 lines) filled with colour 1. Every frame, at each
 * horizontal blank, it sets colour 1 to the next shade (a raster bar) and, in that bank, writes the
 * line just scanned with a colour that changes each frame (VRAM written behind the beam).
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
    movw    $0x4f02, %ax        /* VESA: set mode 101h */
    movw    $0x0101, %bx
    int     $0x10
    movw    $0xa000, %ax
    movw    %ax, %es
    xorw    %di, %di
    movw    $0x0101, %ax        /* colour 1 everywhere */
    movw    $32768, %cx         /* the whole bank */
    cld
    rep stosw
    xorb    %bl, %bl            /* the frame's VRAM colour */

frame:
    movw    $0x3da, %dx
1:  inb     %dx, %al            /* wait for vertical retrace */
    testb   $0x08, %al
    jz      1b
2:  inb     %dx, %al            /* and its end: the frame's first line */
    testb   $0x08, %al
    jnz     2b
    incb    %bl
    xorw    %si, %si            /* scanline */
    xorw    %di, %di            /* VRAM offset of the line just scanned */
line:
    movw    $0x3da, %dx
3:  inb     %dx, %al            /* wait for the display enable to drop: horizontal blank */
    testb   $0x01, %al
    jz      3b
    /* colour 1 to the scanline's shade */
    movw    $0x3c8, %dx
    movb    $1, %al
    outb    %al, %dx
    incw    %dx
    movw    %si, %ax
    andb    $0x3f, %al
    outb    %al, %dx            /* red */
    shrb    $1, %al
    outb    %al, %dx            /* green */
    movb    $0x3f, %al
    subb    %ah, %al
    andb    $0x3f, %al
    outb    %al, %dx            /* blue */
    /* in the first bank: 8 pixels of the line just scanned in this frame's colour */
    cmpw    $102, %si
    jae     4f
    movb    %bl, %al
    movb    %bl, %ah
    movw    $4, %cx
    pushw   %di
    rep stosw
    popw    %di
    addw    $640, %di
4:  movw    $0x3da, %dx
5:  inb     %dx, %al            /* wait for the display enable to come back */
    testb   $0x01, %al
    jnz     5b
    incw    %si
    cmpw    $480, %si
    jb      line
    jmp     frame

    .org    510
    .byte   0x55, 0xaa
