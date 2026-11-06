/*
 * The boot sector of KairoX86's graphics tests (KairoX86#283): loads the test program that follows it on
 * the floppy (sectors 2 on, SECTORS of them, to 0x8000), turns on "unreal mode" (DS, ES, FS and GS with a
 * 4 GB limit, so the program reaches a card's linear framebuffer above 1 MB while it still calls the BIOS),
 * and jumps to the program with DS = ES = 0.
 *
 * SECTORS when it is assembled (core/test/gpu/make_tests.py). A 1.44 MB floppy: 18 sectors a track, 2 heads.
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
    sti
    movb    %dl, drive

    /* Each sector in turn (sector 2 on, CHS from the LBA), to 0x0800:0 on */
    movw    $1, %si                 /* LBA of the next sector */
    movw    $0x0800, %bx
1:  cmpw    $(SECTORS + 1), %si
    je      2f
    movw    %si, %ax
    xorw    %dx, %dx
    movw    $18, %cx
    divw    %cx                     /* ax = track * 2 + head, dx = sector - 1 */
    movb    %dl, %cl
    incb    %cl                     /* sector */
    movb    %al, %dh
    andb    $1, %dh                 /* head */
    shrw    $1, %ax
    movb    %al, %ch                /* cylinder */
    movw    %bx, %es
    xorw    %bx, %bx
    movb    drive, %dl
    movw    $0x0201, %ax
    int     $0x13
    jc      fail
    movw    %es, %bx
    addw    $0x20, %bx              /* the next 512 bytes */
    incw    %si
    jmp     1b

    /* Unreal mode: load each data segment once in protected mode with a flat 4 GB descriptor */
2:  cli
    lgdt    gdt_desc
    movl    %cr0, %eax
    orb     $1, %al
    movl    %eax, %cr0
    jmp     3f
3:  movw    $8, %bx
    movw    %bx, %ds
    movw    %bx, %es
    movw    %bx, %fs
    movw    %bx, %gs
    andb    $0xfe, %al
    movl    %eax, %cr0
    jmp     4f
4:  xorw    %ax, %ax
    movw    %ax, %ds
    movw    %ax, %es
    movw    %ax, %fs
    movw    %ax, %gs
    sti
    ljmp    $0, $0x8000

fail:
    movw    $0x0e46, %ax            /* 'F' on the screen, then stop */
    int     $0x10
5:  hlt
    jmp     5b

    .p2align 3
gdt:
    .quad   0
    .quad   0x00cf92000000ffff      /* flat data: base 0, limit 4 GB, read/write */
gdt_desc:
    .word   gdt_desc - gdt - 1
    .long   gdt
drive:
    .byte   0

    .org    510
    .byte   0x55, 0xaa
