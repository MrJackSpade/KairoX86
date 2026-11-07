/*
 * KairoX86's IBM Professional Graphics Controller test (KairoX86#283, for #268 and #261): on a PGC (its self-test
 * signature, 5Ah 55h at C63FCh), its native display on and its drawing processor fed ASCII commands through the
 * input FIFO (C6000h, its pointers at C6300h and C6301h), every picture drawn by it, in passes each held four ticks
 * of the BIOS clock: lines in every direction and line pattern, the draw modes (write, invert, XOR, AND), rectangles
 * outlined and filled with area patterns, circles and ellipses, polygons, flood fills and boundary fills, on the
 * ImageManager 1024 (model 02h at C63FAh) block moves, then text (in hex mode). The processor draws at fixed points
 * in emulated time (#310), so a full FIFO holds the test up alike in every run. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

#define MAP ((volatile u8 *) 0xc6000u)

static void send_bytes(const u8 *b, u32 n) {
    for (u32 i = 0; i < n; i++) {
        const u8 wr = MAP[0x300];
        while ((u8) (wr + 1) == MAP[0x301]) {
        }
        MAP[wr]    = b[i];
        MAP[0x300] = (u8) (wr + 1);
    }
}

static void send(const char *s) {
    u32 n = 0;
    while (s[n])
        n++;
    send_bytes((const u8 *) s, n);
}

/* Text, in hex mode (ASCII mode's TEXT takes no delimiter character): coordinates as an integer and a fraction word */
/* The ImageManager 1024's block moves (blkmov_row), in each draw mode, from a picture of lines and fills */
static const char *const im1024_pass =
    "CLEARS 9 PRMFIL 1 COLOR 12 MOVE 10,10 RECT 150,120 COLOR 14 MOVE 60,40 CIRCLE 40 PRMFIL 0 COLOR 15 MOVE 0,0 "
    "DRAW 160,130 BLKMOV 0,0,160,130,200,0 LINFUN 1 BLKMOV 0,0,160,130,400,0 LINFUN 2 BLKMOV 0,0,160,130,180,150 "
    "LINFUN 3 BLKMOV 0,0,160,130,380,150 LINFUN 0 BLKMOV 100,60,300,200,120,300 ";

#define C(v) (u8) ((v) & 0xff), (u8) ((v) >> 8), 0, 0
static const u8 text_pass[] = {
    0x0f, 7, 0x06, 15,                                  /* CLEARS 7, COLOR 15 */
    0x81, C(16), 0x10, C(20), C(400),                   /* TSIZE 16, MOVE 20,400 */
    0x80, 0x27, 'P', 'G', 'C', ' ', 'G', 'P', 'U', ' ', '0', '1', '2', '3', 0x27,
    0x81, C(32), 0x10, C(40), C(250),
    0x80, 0x27, 'A', 'B', 'C', 'a', 'b', 'c', 0x27,
    0x85, 2, 2, 0x81, C(8), 0x10, C(320), C(100),       /* TJUST 2 2: centred */
    0x80, 0x27, 'c', 'e', 'n', 't', 'r', 'e', 'd', '!', 0x27,
    0x85, 1, 1, 0xd2,                                   /* TJUST 1 1, CA: ASCII again */
};

static const char *const passes[] = {
    /* Lines every way, with line patterns */
    "CLEARS 1 COLOR 14 MOVE 320,240 DRAW 620,250 MOVE 320,240 DRAW 330,470 MOVE 320,240 DRAW 10,230 MOVE 320,240 "
    "DRAW 300,5 COLOR 12 LINPAT -3856 MOVE 20,20 DRAW 600,460 LINPAT 21845 MOVE 20,460 DRAW 610,30 LINPAT -1 ",
    /* The draw modes over a filled field */
    "CLEARS 2 PRMFIL 1 COLOR 9 MOVE 40,40 RECT 600,440 LINFUN 1 MOVE 100,100 RECT 300,300 LINFUN 2 COLOR 60 "
    "MOVE 200,150 RECT 500,400 LINFUN 3 COLOR 51 MOVE 250,50 RECT 560,250 LINFUN 0 PRMFIL 0 ",
    /* Rectangles outlined and filled with area patterns */
    "CLEARS 3 COLOR 15 MOVE 10,10 RECT 200,150 PRMFIL 1 AREAPT -21846 21845 -21846 21845 -21846 21845 -21846 21845 "
    "-21846 21845 -21846 21845 -21846 21845 -21846 21845 COLOR 13 MOVE 220,40 RECT 620,300 PRMFIL 0 ",
    "CLEARS 4 PRMFIL 1 AREAPT -256 -256 -256 -256 -256 -256 -256 -256 255 255 255 255 255 255 255 255 COLOR 10 "
    "MOVE 30,200 RECTR 400,200 AREAPT -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 PRMFIL 0 ",
    /* Circles and ellipses, outlined and filled */
    "CLEARS 5 COLOR 11 MOVE 160,240 CIRCLE 120 MOVE 480,240 PRMFIL 1 CIRCLE 100 COLOR 6 MOVE 320,100 ELIPSE 200,60 "
    "MOVE 320,380 PRMFIL 0 ELIPSE 80,90 ",
    /* Polygons, filled and outlined (the PGC's POLY draws nothing yet: KairoX86#308) */
    "CLEARS 6 COLOR 12 PRMFIL 1 POLY 5 50,50 300,80 250,400 120,300 20,200 PRMFIL 0 COLOR 14 "
    "POLY 6 350,50 600,60 620,300 500,450 400,300 330,200 ",
    /* Flood and boundary fills */
    "CLEARS 8 COLOR 14 MOVE 100,100 RECT 300,300 MOVE 200,200 AREABC 14 COLOR 3 FLOOD 9 COLOR 15 "
    "MOVE 400,100 CIRCLE 80 MOVE 400,100 COLOR 4 AREABC 15 ",
};

void test_main(void) {
    __asm__ volatile("fninit");
    if ((MAP[0x3fc] != 0x5a) || (MAP[0x3fd] != 0x55))
        return;
    send("DISPLA 0 VWPORT 0,639,0,479 WINDOW 0,639,0,479 "); /* the world the raster, pixel for pixel */
    wait_ticks(4);
    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        send(passes[p]);
        wait_ticks(4);
    }
    if (MAP[0x3fa] == 0x02) { /* the ImageManager 1024 */
        send(im1024_pass);
        wait_ticks(4);
    }
    send("CX ");
    send_bytes(text_pass, sizeof(text_pass));
    wait_ticks(4);
}
