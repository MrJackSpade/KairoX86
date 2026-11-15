/*
 * The SMBIOS tables of KairoX86's free machine (kairo_pc.h), built from the machine as configured
 * and handed to SeaBIOS through fw_cfg: etc/smbios/smbios-anchor (a version 2.4 entry point whose
 * table address, length and counts SeaBIOS fills in) and etc/smbios/smbios-tables (the structures:
 * system, chassis, processor, the memory array, its device and mapping, boot status and the end).
 * SeaBIOS adds its own BIOS information (type 0) in front (its biostables.c).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/device.h>
#include "cpu.h"
#include <86box/kairo_pc.h>

/* A structure's formatted part starts here; its strings follow it, then a double NUL. */
static uint32_t
smbios_start(kairo_buf_t *t, uint8_t type, uint8_t length, uint16_t handle)
{
    const uint32_t at = kairo_buf_u8(t, type);
    kairo_buf_u8(t, length);
    kairo_buf_u16(t, handle);
    return at;
}

static void
smbios_end(kairo_buf_t *t, uint32_t at, uint8_t length, const char *const *strings, int count)
{
    if ((t->len - at) != length)
        fatal("KairoX86 PC: SMBIOS type %u is %u bytes, not %u\n", t->data[at], t->len - at, length);
    for (int i = 0; i < count; i++)
        kairo_buf_put(t, strings[i], (uint32_t) strlen(strings[i]) + 1);
    if (count == 0)
        kairo_buf_u8(t, 0);
    kairo_buf_u8(t, 0);
}

void
kairo_pc_smbios_tables(kairo_fw_cfg_t *cfg, uint32_t ram_kb)
{
    kairo_buf_t t = { 0 }, anchor = { 0 };
    uint32_t    at;
    int         structures = 0;
    const uint32_t mhz = cpu_s->rspeed / 1000000;

    /* Type 1: system information */
    {
        static const char *const s[] = { "KairoX86", "KairoX86 PC", "1.0" };
        /* SMBIOS 2.1's length: SKU and family (2.4) are left out */
        at = smbios_start(&t, 1, 0x19, 0x0100);
        kairo_buf_u8(&t, 1);      /* manufacturer */
        kairo_buf_u8(&t, 2);      /* product */
        kairo_buf_u8(&t, 3);      /* version */
        kairo_buf_u8(&t, 0);      /* serial number */
        kairo_buf_zero(&t, 16);   /* UUID */
        kairo_buf_u8(&t, 0x06);   /* wake-up type: power switch */
        smbios_end(&t, at, 0x19, s, 3);
        structures++;
    }

    /* Type 3: chassis */
    {
        static const char *const s[] = { "KairoX86" };
        at = smbios_start(&t, 3, 0x0d, 0x0300);
        kairo_buf_u8(&t, 1);      /* manufacturer */
        kairo_buf_u8(&t, 0x03);   /* desktop */
        kairo_buf_u8(&t, 0);      /* version */
        kairo_buf_u8(&t, 0);      /* serial number */
        kairo_buf_u8(&t, 0);      /* asset tag */
        kairo_buf_u8(&t, 0x03);   /* boot-up state: safe */
        kairo_buf_u8(&t, 0x03);   /* power supply state: safe */
        kairo_buf_u8(&t, 0x03);   /* thermal state: safe */
        kairo_buf_u8(&t, 0x02);   /* security status: unknown */
        smbios_end(&t, at, 0x0d, s, 1);
        structures++;
    }

    /* Type 4: the processor, as 86Box runs it */
    {
        const char *const s[] = { "CPU0", "KairoX86", cpu_s->name };
        at = smbios_start(&t, 4, 0x20, 0x0400);
        kairo_buf_u8(&t, 1);                       /* socket designation */
        kairo_buf_u8(&t, 0x03);                    /* central processor */
        kairo_buf_u8(&t, 0x02);                    /* family: unknown */
        kairo_buf_u8(&t, 2);                       /* manufacturer */
        kairo_buf_u32(&t, cpu_s->cpuid_model);     /* processor ID: CPUID 1 EAX */
        kairo_buf_u32(&t, 0);                      /* and the feature flags (EDX): not given */
        kairo_buf_u8(&t, 3);                       /* version */
        kairo_buf_u8(&t, 0);                       /* voltage */
        kairo_buf_u16(&t, 0);                      /* external clock */
        kairo_buf_u16(&t, (uint16_t) mhz);         /* max speed */
        kairo_buf_u16(&t, (uint16_t) mhz);         /* current speed */
        kairo_buf_u8(&t, 0x41);                    /* populated, enabled */
        kairo_buf_u8(&t, 0x01);                    /* upgrade: other */
        kairo_buf_u16(&t, 0xffff);                 /* no L1, L2, L3 cache structures */
        kairo_buf_u16(&t, 0xffff);
        kairo_buf_u16(&t, 0xffff);
        smbios_end(&t, at, 0x20, s, 3);
        structures++;
    }

    /* Type 16: the memory array */
    {
        at = smbios_start(&t, 16, 0x0f, 0x1000);
        kairo_buf_u8(&t, 0x03);                    /* location: system board */
        kairo_buf_u8(&t, 0x03);                    /* use: system memory */
        kairo_buf_u8(&t, 0x03);                    /* error correction: none */
        kairo_buf_u32(&t, ram_kb);                 /* maximum capacity, KB */
        kairo_buf_u16(&t, 0xfffe);                 /* no error information */
        kairo_buf_u16(&t, 1);                      /* devices */
        smbios_end(&t, at, 0x0f, NULL, 0);
        structures++;
    }

    /* Type 17: its one memory device */
    {
        static const char *const s[] = { "DIMM 0" };
        const uint32_t mb = ram_kb / 1024;
        at = smbios_start(&t, 17, 0x15, 0x1100);
        kairo_buf_u16(&t, 0x1000);                 /* array */
        kairo_buf_u16(&t, 0xfffe);                 /* no error information */
        kairo_buf_u16(&t, 64);                     /* total width */
        kairo_buf_u16(&t, 64);                     /* data width */
        kairo_buf_u16(&t, (uint16_t) (mb ? mb : 1)); /* size, MB */
        kairo_buf_u8(&t, 0x09);                    /* form factor: DIMM */
        kairo_buf_u8(&t, 0);                       /* not in a set */
        kairo_buf_u8(&t, 1);                       /* device locator */
        kairo_buf_u8(&t, 0);                       /* bank locator */
        kairo_buf_u8(&t, 0x07);                    /* type: RAM */
        kairo_buf_u16(&t, 0x0002);                 /* type detail: unknown */
        smbios_end(&t, at, 0x15, s, 1);
        structures++;
    }

    /* Type 19: where the array is mapped */
    {
        at = smbios_start(&t, 19, 0x0f, 0x1300);
        kairo_buf_u32(&t, 0);                      /* start, KB */
        kairo_buf_u32(&t, ram_kb - 1);             /* end, KB */
        kairo_buf_u16(&t, 0x1000);                 /* array */
        kairo_buf_u8(&t, 1);                       /* partition width */
        smbios_end(&t, at, 0x0f, NULL, 0);
        structures++;
    }

    /* Type 32: boot status */
    {
        at = smbios_start(&t, 32, 0x0b, 0x2000);
        kairo_buf_zero(&t, 6);
        kairo_buf_u8(&t, 0);                       /* no errors */
        smbios_end(&t, at, 0x0b, NULL, 0);
        structures++;
    }

    /* Type 127: the end */
    at = smbios_start(&t, 127, 4, 0x7f00);
    smbios_end(&t, at, 4, NULL, 0);
    structures++;

    /* The 2.x entry point; SeaBIOS sets the table's address, length, counts and checksums. */
    kairo_buf_put(&anchor, "_SM_", 4);
    kairo_buf_u8(&anchor, 0);      /* checksum */
    kairo_buf_u8(&anchor, 0x1f);   /* length */
    kairo_buf_u8(&anchor, 2);      /* version 2.4 */
    kairo_buf_u8(&anchor, 4);
    kairo_buf_u16(&anchor, 0);     /* max structure size */
    kairo_buf_u8(&anchor, 0);      /* revision */
    kairo_buf_zero(&anchor, 5);
    kairo_buf_put(&anchor, "_DMI_", 5);
    kairo_buf_u8(&anchor, 0);      /* intermediate checksum */
    kairo_buf_u16(&anchor, (uint16_t) t.len);
    kairo_buf_u32(&anchor, 0);     /* table address */
    kairo_buf_u16(&anchor, (uint16_t) structures);
    kairo_buf_u8(&anchor, 0x24);   /* BCD revision */

    kairo_fw_cfg_add_file(cfg, "etc/smbios/smbios-tables", t.data, t.len);
    kairo_fw_cfg_add_file(cfg, "etc/smbios/smbios-anchor", anchor.data, anchor.len);
    kairo_buf_free(&t);
    kairo_buf_free(&anchor);
}
