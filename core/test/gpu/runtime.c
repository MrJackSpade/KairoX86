/*
 * The graphics tests' entry and helpers (KairoX86#283, runtime.h).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

void end_screen(void);

/* The test's end at a fixed address, 0000:8002: a HLT with interrupts off, after which the machine
   stops ("The PC halted ... (at 0000:8003)", the HLT's next instruction), so the batch (compare.py,
   TEST_END) knows the program ran to its end on any card, whatever its last picture. */
__asm__(".section .text.entry\n"
        ".globl _start\n"
        "_start:\n"
        "    jmp 2f\n"
        "1:  cli\n"
        "    hlt\n"
        "    jmp 1b\n"
        "2:  cld\n"
        "    calll test_main\n"
        "    calll end_screen\n"
        "    jmp 1b\n");

/* Unreal mode, as the loader enters it (loader.S): each data segment loaded once in protected mode with a flat 4 GB
   descriptor, then 0 again in real mode; the interrupt flag kept */
__asm__(".text\n"
        ".globl unreal\n"
        "unreal:\n"
        "    pushfl\n"
        "    cli\n"
        "    pushl %eax\n"
        "    pushl %ebx\n"
        "    lgdtl unreal_desc\n"
        "    movl %cr0, %eax\n"
        "    orb $1, %al\n"
        "    movl %eax, %cr0\n"
        "    jmp 1f\n"
        "1:  movw $8, %bx\n"
        "    movw %bx, %ds\n"
        "    movw %bx, %es\n"
        "    movw %bx, %fs\n"
        "    movw %bx, %gs\n"
        "    andb $0xfe, %al\n"
        "    movl %eax, %cr0\n"
        "    jmp 2f\n"
        "2:  xorw %bx, %bx\n"
        "    movw %bx, %ds\n"
        "    movw %bx, %es\n"
        "    movw %bx, %fs\n"
        "    movw %bx, %gs\n"
        "    popl %ebx\n"
        "    popl %eax\n"
        "    popfl\n"
        "    retl\n"
        "    .p2align 3\n"
        "unreal_gdt:\n"
        "    .quad 0\n"
        "    .quad 0x00cf92000000ffff\n"
        "unreal_desc:\n"
        "    .word 15\n"
        "    .long unreal_gdt\n");

int card_class(void) {
    /* VGA: the display combination call (INT 10h 1A00h), which only a VGA's BIOS has */
    u16 bx = 0;
    const u16 al = int10(0x1a00, 0, 0, 0, 0, &bx) & 0xff;
    if (al == 0x1a && ((u8) bx == 7 || (u8) bx == 8))
        return CARD_VGA;
    /* EGA: its information call (INT 10h 12h, BL 10h) changes BL; BH 1 is a mono display */
    bx = 0;
    int10(0x1200, 0x0010, 0, 0, 0, &bx);
    if ((u8) bx != 0x10)
        return (bx >> 8) ? CARD_EGA_MONO : CARD_EGA;
    /* MDA (Hercules too) or CGA: the BIOS's initial video mode in the equipment word, 3 for mono */
    return ((*(volatile u16 *) 0x410 >> 4) & 3) == 3 ? CARD_MDA : CARD_CGA;
}

int is_vga(void) {
    return card_class() == CARD_VGA;
}

/* The end screen every test finishes on: a mode of the card's class drawn with (x + 3y) modulo its
   colours. VGA: mode 13h with 256 distinct palette entries. Colour EGA: mode 0Dh. CGA: mode 4. Mono
   cards: mode 7, every cell's character and attribute from the cell's place. */
void end_screen(void) {
    const int card = card_class();
    if (card == CARD_VGA) {
        int10(0x0013, 0, 0, 0, 0, 0);
        outb(0x3c8, 0);
        for (u32 i = 0; i < 256; i++) {
            /* 256 distinct 6-bit colours: i's bits spread over red, green and blue */
            outb(0x3c9, (u8) ((i & 7) << 3));
            outb(0x3c9, (u8) (((i >> 3) & 7) << 3));
            outb(0x3c9, (u8) (((i >> 6) & 3) << 4));
        }
        u8 *screen = (u8 *) 0xa0000;
        for (u32 y = 0; y < 200; y++)
            for (u32 x = 0; x < 320; x++)
                screen[y * 320 + x] = (u8) (x + 3 * y);
    } else if (card == CARD_EGA) {
        int10(0x000d, 0, 0, 0, 0, 0);
        /* Planar: plane p of a pixel is bit p of its colour */
        u8 *screen = (u8 *) 0xa0000;
        for (u32 plane = 0; plane < 4; plane++) {
            outw(0x3c4, (u16) (0x0002 | ((1u << plane) << 8)));
            for (u32 y = 0; y < 200; y++)
                for (u32 bx8 = 0; bx8 < 40; bx8++) {
                    u8 v = 0;
                    for (u32 b = 0; b < 8; b++)
                        v |= (u8) (((((bx8 * 8 + b) + 3 * y) >> plane) & 1) << (7 - b));
                    screen[y * 40 + bx8] = v;
                }
        }
        outw(0x3c4, 0x0f02);
    } else if (card == CARD_CGA) {
        int10(0x0004, 0, 0, 0, 0, 0);
        /* Two bits a pixel, even lines at B8000h, odd ones 8 KB on */
        u8 *screen = (u8 *) 0xb8000;
        for (u32 y = 0; y < 200; y++)
            for (u32 bx4 = 0; bx4 < 80; bx4++) {
                u8 v = 0;
                for (u32 p = 0; p < 4; p++)
                    v |= (u8) ((((bx4 * 4 + p) + 3 * y) & 3) << (6 - 2 * p));
                screen[(y & 1) * 0x2000 + (y >> 1) * 80 + bx4] = v;
            }
    } else {
        int10(0x0007, 0, 0, 0, 0, 0);
        u8 *screen = (u8 *) 0xb0000;
        for (u32 y = 0; y < 25; y++)
            for (u32 x = 0; x < 80; x++) {
                screen[(y * 80 + x) * 2]     = (u8) (x + 3 * y);
                screen[(y * 80 + x) * 2 + 1] = (u8) ((x + 3 * y) & 0x7f);
            }
    }
}

void wait_frames(u16 status_port, int n) {
    for (int i = 0; i < n; i++) {
        while (inb(status_port) & 8) {
        }
        while (!(inb(status_port) & 8)) {
        }
    }
}


int vbe_modes(void) {
    VBE_INFO->signature[0] = 'V';
    VBE_INFO->signature[1] = 'B';
    VBE_INFO->signature[2] = 'E';
    VBE_INFO->signature[3] = '2';
    if (int10(0x4f00, 0, 0, 0, 0x6000, 0) != 0x004f)
        return -1;
    const u16 *list = (const u16 *) (((VBE_INFO->modes >> 16) << 4) + (VBE_INFO->modes & 0xffff));
    int count = 0;
    while (count < 255 && list[count] != 0xffff) {
        VBE_MODES[count] = list[count];
        count++;
    }
    return count;
}

u16 vbe_find(u16 width, u16 height, u8 bpp) {
    const int count = vbe_modes();
    for (int i = 0; i < count; i++) {
        const u16 mode = VBE_MODES[i];
        if (int10(0x4f01, 0, mode, 0, 0x6200, 0) != 0x004f)
            continue;
        const struct vbe_mode_info *m = VBE_MODE;
        if (((m->attributes & 0x81) != 0x81) || !m->framebuffer || (m->width != width) || (m->height != height))
            continue;
        if ((m->bpp == bpp) || ((bpp == 15) && (m->bpp == 16) && (m->green_size == 5)))
            return mode;
    }
    return 0;
}
