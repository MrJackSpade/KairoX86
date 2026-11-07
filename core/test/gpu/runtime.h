/*
 * What KairoX86's graphics tests share (KairoX86#283): the program starts at 0x8000 in real mode with
 * flat 4 GB data segments (core/test/gpu/loader.S), built with clang -m16, so a pointer is a linear address,
 * below 1 MB or a card's framebuffer above it, and the BIOS can still be called.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#pragma once

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

static inline void outb(u16 port, u8 v) { __asm__ volatile("outb %0, %1" : : "a"(v), "Nd"(port)); }
static inline void outw(u16 port, u16 v) { __asm__ volatile("outw %0, %1" : : "a"(v), "Nd"(port)); }
static inline void outl(u16 port, u32 v) { __asm__ volatile("outl %0, %1" : : "a"(v), "Nd"(port)); }
static inline u8 inb(u16 port) { u8 v; __asm__ volatile("inb %1, %0" : "=a"(v) : "Nd"(port)); return v; }
static inline u16 inw(u16 port) { u16 v; __asm__ volatile("inw %1, %0" : "=a"(v) : "Nd"(port)); return v; }
static inline u32 inl(u16 port) { u32 v; __asm__ volatile("inl %1, %0" : "=a"(v) : "Nd"(port)); return v; }

/* Unreal mode again (runtime.c): DS, ES, FS and GS with a 4 GB limit, as the loader left them. A BIOS that uses
   protected or unreal mode itself (the Trident TGUI's mode set) leaves them at 64K, and every access above that faults. */
void unreal(void);

/* INT 10h with AX, BX, CX, DX and DI (ES = 0, so ES:DI is a linear address below 64 KB); returns AX, and BX in *bx_out.
   Unreal mode is restored after it. */
static inline u16 int10(u16 ax, u16 bx, u16 cx, u16 dx, u16 di, u16 *bx_out) {
    u16 rax, rbx;
    __asm__ volatile("pushl %%ebp\n\tint $0x10\n\tpopl %%ebp"
                     : "=a"(rax), "=b"(rbx), "+c"(cx), "+d"(dx), "+D"(di)
                     : "a"(ax), "b"(bx)
                     : "memory", "esi", "cc");
    unreal();
    if (bx_out) *bx_out = rbx;
    return rax;
}

/* The CRTC's status port (3DAh colour, 3BAh mono): waits for n vertical retraces to begin */
void wait_frames(u16 status_port, int n);

/* Waits for n ticks of the BIOS clock (40:6Ch, 18.2 a second) to begin: a hold that works on any card,
   with or without a CRTC (the HD44780 LCD has none, so no retrace to wait for) */
static inline void wait_ticks(int n) {
    for (int i = 0; i < n; i++) {
        const u32 now = *(volatile u32 *) 0x46c;
        while (*(volatile u32 *) 0x46c == now) {
        }
    }
}

/* The status port of the CRTC the BIOS drives now: its base (40:63h) + 6 */
static inline u16 crtc_status(void) { return (u16) (*(volatile u16 *) 0x463 + 6); }

/* The card's class, from what its BIOS answers (runtime.c) */
enum { CARD_MDA, CARD_CGA, CARD_EGA_MONO, CARD_EGA, CARD_VGA };
int card_class(void);
/* Whether the card is a VGA */
int is_vga(void);

/* The VBE BIOS's information blocks (VBE 2.0), at fixed addresses below 64 KB so ES:DI (ES = 0) reaches them */
struct vbe_info {
    char signature[4];
    u16  version;
    u32  oem;
    u32  caps;
    u32  modes; /* far pointer: offset low, segment high */
    u16  memory;
    u8   rest[492];
} __attribute__((packed));

struct vbe_mode_info {
    u16 attributes;
    u8  window_a, window_b;
    u16 granularity, window_size, segment_a, segment_b;
    u32 window_func;
    u16 pitch;
    u16 width, height;
    u8  char_w, char_h, planes, bpp, banks, model, bank_size, image_pages, reserved0;
    u8  red_size, red_pos, green_size, green_pos, blue_size, blue_pos, rsv_size, rsv_pos, direct_info;
    u32 framebuffer;
    u8  rest[212];
} __attribute__((packed));

#define VBE_INFO  ((struct vbe_info *) 0x6000)
#define VBE_MODE  ((struct vbe_mode_info *) 0x6200)
#define VBE_MODES ((u16 *) 0x6400)

/* The VBE BIOS's mode list, copied to VBE_MODES before any other call can change it: how many (-1: no VBE) */
int vbe_modes(void);
/* The first listed mode width x height of bpp bits a pixel with a linear frame buffer, its information in
   VBE_MODE (bpp 15 also takes a 16-bit mode whose green is 5 bits): its number, or 0 when none is */
u16 vbe_find(u16 width, u16 height, u8 bpp);

/* A 32-bit pattern value for a pixel: changes from each pixel to the next across and down, so a
   misplaced, dropped or doubled pixel shows in the picture */
static inline u32 pattern(u32 x, u32 y, u32 salt) {
    u32 v = x * 0x9e3779b1u ^ y * 0x85ebca77u ^ salt * 0xc2b2ae3du;
    return v ^ (v >> 15);
}

/* The program's code, called by the runtime's entry; when it returns, the machine waits on its last picture */
void test_main(void);
