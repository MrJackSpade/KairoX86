/*
 * KairoX86: the cassette port of the IBM PC 5150 and the PCjr, written for KairoX86 to replace
 * 86Box's GPL-2.0-only cassette code (KairoX86#1).
 *
 * The machine drives the deck's motor relay and its write signal (the PIT's channel 2 output) and
 * reads its read signal. On the real deck a 1 bit is one 1 ms cycle and a 0 bit one 0.5 ms cycle,
 * the cycle starting on the signal's rising edge. A tape image holds either the data bits (8 to a
 * byte, the first in bit 7), which play back as those cycles and record by timing the cycles the
 * machine writes, or 8-bit unsigned samples at the sample rate, the signal itself.
 *
 * Copyright 2026 MrJackSpade.
 *
 * This program is free software; you can redistribute it and/or modify it under the terms of the
 * GNU General Public License as published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 */
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <86box/86box.h>
#include <86box/timer.h>
#include <86box/device.h>
#include <86box/plat.h>
#include <86box/kairo_cassette.h>

/* A 0 bit's half cycle and a 1 bit's, in microseconds. */
#define HALF_0_US 250.0
#define HALF_1_US 500.0
/* A recorded cycle longer than this is a 1; longer than CYCLE_GAP_US it is a gap, not a bit. */
#define CYCLE_SPLIT_US 750.0
#define CYCLE_GAP_US   2000.0
/* PCM levels: the read signal turns on above HIGH and off below LOW; a recorded level writes ON or OFF. */
#define PCM_HIGH 0x88
#define PCM_LOW  0x78
#define PCM_ON   0xc0
#define PCM_OFF  0x40

struct pc_cassette_t {
    FILE         *fp;
    char         *fname;
    int           save;
    int           pcm;
    unsigned long srate;
    unsigned long position;
    unsigned char motor;
    unsigned char out;
    unsigned char inp;
    /* Playing data bits: the bit being played and which half of its cycle is on the signal. */
    int bit;
    int half;
    /* Recording data bits: the last rising edge, and the bits not yet written. */
    uint64_t      edge;
    int           edge_valid;
    unsigned char pending;
    int           pending_bits;
    pc_timer_t    timer;
};

pc_cassette_t *cassette;

char          cassette_fname[MAX_IMAGE_PATH_LEN];
char          cassette_mode[512];
char         *cassette_image_history[CASSETTE_IMAGE_HISTORY];
unsigned long cassette_pos;
unsigned long cassette_srate;
int           cassette_enable;
int           cassette_append;
int           cassette_pcm;
int           cassette_ui_writeprot;

static double
elapsed_us(uint64_t since)
{
    return (double) (tsc - since) / (double) TIMER_USEC;
}

static void
seek_or_fail(pc_cassette_t *cas, long offset)
{
    if (fseek(cas->fp, offset, SEEK_SET) != 0)
        fatal("Cassette: cannot seek to %ld in %s\n", offset, cas->fname);
}

static long
image_size(pc_cassette_t *cas)
{
    if (fseek(cas->fp, 0, SEEK_END) != 0)
        fatal("Cassette: cannot read the size of %s\n", cas->fname);
    return ftell(cas->fp);
}

/* The data bit at the position, or -1 at the end of the tape. */
static int
read_bit(pc_cassette_t *cas)
{
    int byte;

    seek_or_fail(cas, (long) (cas->position >> 3));
    byte = fgetc(cas->fp);
    if (byte == EOF)
        return -1;
    return (byte >> (7 - (cas->position & 7))) & 1;
}

/* Writes the recorded bits not yet written into their byte, over what the tape held there. They are
   always in one byte: record_bit writes them at every byte boundary. */
static void
write_pending(pc_cassette_t *cas)
{
    long          offset;
    int           byte;
    int           shift;
    unsigned long start;

    if (cas->pending_bits > 0) {
        start  = cas->position - (unsigned long) cas->pending_bits;
        offset = (long) (start >> 3);
        seek_or_fail(cas, offset);
        byte = fgetc(cas->fp);
        if (byte == EOF)
            byte = 0;
        shift = 7 - (int) (start & 7);
        for (int i = 0; i < cas->pending_bits && shift >= 0; i++, shift--) {
            int bit = (cas->pending >> (cas->pending_bits - 1 - i)) & 1;
            byte    = (byte & ~(1 << shift)) | (bit << shift);
        }
        seek_or_fail(cas, offset);
        if (fputc(byte, cas->fp) == EOF || fflush(cas->fp) != 0)
            fatal("Cassette: cannot write %s\n", cas->fname);
        cas->pending_bits = 0;
        cas->pending      = 0;
    }
}

static void
record_bit(pc_cassette_t *cas, int bit)
{
    cas->pending = (unsigned char) ((cas->pending << 1) | bit);
    cas->pending_bits++;
    cas->position++;
    if ((cas->position & 7) == 0)
        write_pending(cas);
}

static void
schedule(pc_cassette_t *cas)
{
    double period;

    timer_disable(&cas->timer);
    if (!cas->motor || cas->fp == NULL)
        return;
    if (cas->pcm)
        period = 1000000.0 / (double) cas->srate;
    else if (cas->save)
        return; /* recording data bits follows the write signal's edges, not a clock */
    else {
        if (cas->bit < 0) {
            cas->bit  = read_bit(cas);
            cas->half = 0;
        }
        if (cas->bit < 0) {
            cas->inp = 0;
            return; /* end of the tape */
        }
        period = cas->bit ? HALF_1_US : HALF_0_US;
    }
    timer_on_auto(&cas->timer, period);
}

static void
tick(void *priv)
{
    pc_cassette_t *cas = (pc_cassette_t *) priv;

    if (cas->pcm) {
        if (cas->save) {
            seek_or_fail(cas, (long) cas->position);
            if (fputc(cas->out ? PCM_ON : PCM_OFF, cas->fp) == EOF)
                fatal("Cassette: cannot write %s\n", cas->fname);
            cas->position++;
        } else {
            int sample;

            seek_or_fail(cas, (long) cas->position);
            sample = fgetc(cas->fp);
            if (sample == EOF) {
                cas->inp = 0;
                return; /* end of the tape */
            }
            if (sample > PCM_HIGH)
                cas->inp = 1;
            else if (sample < PCM_LOW)
                cas->inp = 0;
            cas->position++;
        }
    } else {
        /* A cycle is high then low; the next bit starts after the low half. */
        if (cas->half == 0) {
            cas->inp  = 1;
            cas->half = 1;
        } else {
            cas->inp  = 0;
            cas->half = 0;
            cas->position++;
            cas->bit = -1;
        }
    }
    schedule(cas);
}

static void
stop_recording(pc_cassette_t *cas)
{
    if (cas->fp != NULL && cas->save && !cas->pcm)
        write_pending(cas);
    cas->edge_valid = 0;
}

pc_cassette_t *
pc_cas_new(void)
{
    pc_cassette_t *cas = (pc_cassette_t *) calloc(1, sizeof(pc_cassette_t));

    if (cas == NULL)
        fatal("Cassette: out of memory\n");
    cas->srate = 44100;
    cas->bit   = -1;
    timer_add(&cas->timer, tick, cas, 0);
    return cas;
}

void
pc_cas_del(pc_cassette_t *cas)
{
    if (cas == NULL)
        return;
    pc_cas_set_fname(cas, NULL);
    timer_disable(&cas->timer);
    free(cas);
}

int
pc_cas_set_fname(pc_cassette_t *cas, char *fname)
{
    if (cas->fp != NULL) {
        stop_recording(cas);
        fclose(cas->fp);
        cas->fp = NULL;
    }
    free(cas->fname);
    cas->fname    = NULL;
    cas->position = 0;
    cas->bit      = -1;
    cas->inp      = 0;
    timer_disable(&cas->timer);
    if (fname == NULL || fname[0] == '\0')
        return 0;

    cas->fp = plat_fopen(fname, "r+b");
    if (cas->fp == NULL && cas->save)
        cas->fp = plat_fopen(fname, "w+b");
    if (cas->fp == NULL)
        cas->fp = plat_fopen(fname, "rb");
    if (cas->fp == NULL)
        return 1;
    cas->fname = strdup(fname);
    if (cas->fname == NULL)
        fatal("Cassette: out of memory\n");
    schedule(cas);
    return 0;
}

int
pc_cas_get_mode(const pc_cassette_t *cas)
{
    return cas->save;
}

void
pc_cas_set_mode(pc_cassette_t *cas, int save)
{
    save = save && !cassette_ui_writeprot;
    if (save == cas->save)
        return;
    stop_recording(cas);
    cas->save = save;
    cas->bit  = -1;
    schedule(cas);
}

int
pc_cas_get_pcm(const pc_cassette_t *cas)
{
    return cas->pcm;
}

void
pc_cas_set_pcm(pc_cassette_t *cas, int pcm)
{
    stop_recording(cas);
    cas->pcm = !!pcm;
    cas->bit = -1;
    schedule(cas);
}

unsigned long
pc_cas_get_srate(const pc_cassette_t *cas)
{
    return cas->srate;
}

void
pc_cas_set_srate(pc_cassette_t *cas, unsigned long srate)
{
    if (srate == 0)
        fatal("Cassette: a sample rate of 0\n");
    cas->srate = srate;
    schedule(cas);
}

void
pc_cas_rewind(pc_cassette_t *cas)
{
    pc_cas_set_position(cas, 0);
}

void
pc_cas_append(pc_cassette_t *cas)
{
    long size;

    if (cas->fp == NULL)
        return;
    size = image_size(cas);
    pc_cas_set_position(cas, cas->pcm ? (unsigned long) size : (unsigned long) size * 8);
}

unsigned long
pc_cas_get_position(const pc_cassette_t *cas)
{
    return cas->position;
}

int
pc_cas_set_position(pc_cassette_t *cas, unsigned long pos)
{
    stop_recording(cas);
    cas->position = pos;
    cas->bit      = -1;
    schedule(cas);
    return 0;
}

void
pc_cas_set_motor(pc_cassette_t *cas, unsigned char val)
{
    val = !!val;
    if (val == cas->motor)
        return;
    if (!val)
        stop_recording(cas);
    cas->motor = val;
    schedule(cas);
}

unsigned char
pc_cas_get_inp(const pc_cassette_t *cas)
{
    return cas->inp;
}

void
pc_cas_set_out(pc_cassette_t *cas, unsigned char val)
{
    val = !!val;
    if (val == cas->out)
        return;
    cas->out = val;
    if (!val || !cas->motor || cas->fp == NULL || !cas->save || cas->pcm)
        return;
    /* A rising edge ends the cycle the last one started. */
    if (cas->edge_valid) {
        double cycle = elapsed_us(cas->edge);

        if (cycle <= CYCLE_GAP_US)
            record_bit(cas, cycle > CYCLE_SPLIT_US);
    }
    cas->edge       = tsc;
    cas->edge_valid = 1;
}

static void *
cassette_init(const device_t *info)
{
    (void) info;
    cassette = pc_cas_new();
    pc_cas_set_srate(cassette, cassette_srate ? cassette_srate : 44100);
    pc_cas_set_pcm(cassette, cassette_pcm);
    pc_cas_set_mode(cassette, strcmp(cassette_mode, "save") == 0);
    if (cassette_fname[0] != '\0' && pc_cas_set_fname(cassette, cassette_fname) != 0)
        fatal("Cassette: cannot open %s\n", cassette_fname);
    if (cassette_append)
        pc_cas_append(cassette);
    else
        pc_cas_set_position(cassette, cassette_pos);
    return cassette;
}

static void
cassette_close(void *priv)
{
    pc_cassette_t *cas = (pc_cassette_t *) priv;

    cassette_pos = cas->position;
    pc_cas_del(cas);
    cassette = NULL;
}

const device_t cassette_device = {
    .name          = "IBM PC/PCjr Cassette Device",
    .internal_name = "cassette",
    .flags         = 0,
    .local         = 0,
    .init          = cassette_init,
    .close         = cassette_close,
    .reset         = NULL,
    .available     = NULL,
    .speed_changed = NULL,
    .force_redraw  = NULL,
    .config        = NULL
};
