/*
 * KairoX86: the cassette port of the IBM PC 5150 and the PCjr, written for KairoX86 to replace
 * 86Box's GPL-2.0-only cassette code (KairoX86#1). Same calls and settings as the code it replaces.
 *
 * Copyright 2026 MrJackSpade.
 *
 * This program is free software; you can redistribute it and/or modify it under the terms of the
 * GNU General Public License as published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 */
#ifndef KAIRO_CASSETTE_H
#define KAIRO_CASSETTE_H

#include <stdint.h>

/* The tape deck: its file, mode, position and the signal on its input and output. */
typedef struct pc_cassette_t pc_cassette_t;

pc_cassette_t *pc_cas_new(void);
void           pc_cas_del(pc_cassette_t *cas);

/* Opens the tape image fname (NULL closes it). Returns 0, or 1 when it cannot be opened. */
int pc_cas_set_fname(pc_cassette_t *cas, char *fname);

/* 1 when the deck records, 0 when it plays. */
int  pc_cas_get_mode(const pc_cassette_t *cas);
void pc_cas_set_mode(pc_cassette_t *cas, int save);

/* 1 when the image holds 8-bit unsigned samples at the sample rate, 0 when it holds data bits. */
int           pc_cas_get_pcm(const pc_cassette_t *cas);
void          pc_cas_set_pcm(pc_cassette_t *cas, int pcm);
unsigned long pc_cas_get_srate(const pc_cassette_t *cas);
void          pc_cas_set_srate(pc_cassette_t *cas, unsigned long srate);

/* The position on the tape, in bits (data images) or samples (PCM images). */
void          pc_cas_rewind(pc_cassette_t *cas);
void          pc_cas_append(pc_cassette_t *cas);
unsigned long pc_cas_get_position(const pc_cassette_t *cas);
int           pc_cas_set_position(pc_cassette_t *cas, unsigned long pos);

/* The machine's side: the motor relay, the read signal and the write signal. */
void          pc_cas_set_motor(pc_cassette_t *cas, unsigned char val);
unsigned char pc_cas_get_inp(const pc_cassette_t *cas);
void          pc_cas_set_out(pc_cassette_t *cas, unsigned char val);

#define CASSETTE_IMAGE_HISTORY 10

extern pc_cassette_t *cassette;

extern char          cassette_fname[MAX_IMAGE_PATH_LEN];
extern char          cassette_mode[512];
extern char         *cassette_image_history[CASSETTE_IMAGE_HISTORY];
extern unsigned long cassette_pos;
extern unsigned long cassette_srate;
extern int           cassette_enable;
extern int           cassette_append;
extern int           cassette_pcm;
extern int           cassette_ui_writeprot;

extern const device_t cassette_device;

#endif /* KAIRO_CASSETTE_H */
