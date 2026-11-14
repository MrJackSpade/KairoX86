/*
 * KairoX86's free machine (kairo_pc.h): an Intel 440FX with a PIIX4, a PS/2 keyboard controller, a
 * floppy controller, two serial ports and a parallel port, five PCI slots, booting SeaBIOS. It takes
 * any processor from the 486 to the Pentium II and Celeron, so one board serves every era the app's
 * presets cover; nothing on it needs firmware from the player.
 *
 * At every start it fills the CMOS bytes SeaBIOS and the guest read (memory sizes, floppy types,
 * the processor count) and hands SeaBIOS the machine through fw_cfg: its memory map (etc/e820), boot
 * order (bootorder, from 86box.cfg's [KairoX86] boot_order), and ACPI and SMBIOS tables.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include "cpu.h"
#include <86box/timer.h>
#include <86box/io.h>
#include <86box/device.h>
#include <86box/chipset.h>
#include <86box/keyboard.h>
#include <86box/mem.h>
#include <86box/nvr.h>
#include <86box/pci.h>
#include <86box/rom.h>
#include <86box/fdd.h>
#include <86box/fdc.h>
#include <86box/fdc_ext.h>
#include <86box/serial.h>
#include <86box/lpt.h>
#include <86box/hdd.h>
#include <86box/cdrom.h>
#include <86box/config.h>
#include <86box/machine.h>
#include <86box/kairo_pc.h>

/* fw_cfg's fixed keys (SeaBIOS's paravirt.c) */
#define FW_CFG_NOGRAPHIC      0x0004
#define FW_CFG_NB_CPUS        0x0005
#define FW_CFG_NUMA           0x000d
#define FW_CFG_BOOT_MENU      0x000e
#define FW_CFG_MAX_CPUS       0x000f
#define FW_CFG_ACPI_TABLES    0x8000
#define FW_CFG_SMBIOS_ENTRIES 0x8001
#define FW_CFG_IRQ0_OVERRIDE  0x8002
#define FW_CFG_E820_TABLE     0x8003

/* The CMOS floppy type of an 86Box drive type, 0 for none (or one the BIOS has no code for). */
static uint8_t
cmos_floppy_type(int drive)
{
    static const struct {
        const char *name;
        uint8_t     type;
    } types[] = {
        { "525_2dd", 1 }, { "525_2hd", 2 }, { "35_2dd", 3 }, { "35_2hd", 4 }, { "35_2ed", 5 },
    };
    const char *name = fdd_get_internal_name(fdd_get_type(&drives[drive]));

    for (size_t i = 0; i < sizeof(types) / sizeof(types[0]); i++) {
        if (!strcmp(name, types[i].name))
            return types[i].type;
    }
    return 0;
}

/* The CMOS bytes QEMU's machines set and SeaBIOS (and DOS-era software) read. */
static void
kairo_pc_cmos(nvr_t *nvr, uint32_t ram_kb)
{
    const uint8_t  a     = cmos_floppy_type(0);
    const uint8_t  b     = cmos_floppy_type(1);
    const uint32_t ext   = (ram_kb > 1024) ? ram_kb - 1024 : 0;
    const uint32_t above = (ram_kb > 16384) ? (ram_kb - 16384) / 64 : 0;

    nvr->regs[0x10] = (a << 4) | b;
    /* Equipment: floppy drives present and their count, a VGA display, a coprocessor. */
    nvr->regs[0x14] = ((a || b) ? 0x01 : 0x00) | ((a && b) ? 0x40 : 0x00) | 0x02;
    nvr->regs[0x15] = 640 & 0xff;
    nvr->regs[0x16] = 640 >> 8;
    nvr->regs[0x17] = nvr->regs[0x30] = (uint8_t) ((ext > 0xffff) ? 0xff : ext & 0xff);
    nvr->regs[0x18] = nvr->regs[0x31] = (uint8_t) ((ext > 0xffff) ? 0xff : ext >> 8);
    nvr->regs[0x34] = (uint8_t) ((above > 0xffff) ? 0xff : above & 0xff);
    nvr->regs[0x35] = (uint8_t) ((above > 0xffff) ? 0xff : above >> 8);
    nvr->regs[0x5b] = nvr->regs[0x5c] = nvr->regs[0x5d] = 0; /* nothing above 4 GB */
    nvr->regs[0x5f] = 0;                                     /* one processor (count - 1) */
}

/* The device paths SeaBIOS boots by (its boot.c), for the drives 86box.cfg's boot order names. */
static int
ide_path(char *out, size_t len, int channel)
{
    /* The PIIX4's IDE function (01.1): two channels, master and slave. */
    if (channel >= 4)
        return 0;
    snprintf(out, len, "/pci@i0cf8/*@1,1/drive@%x/disk@%x\n", channel >> 1, channel & 1);
    return 1;
}

static void
kairo_pc_bootorder(kairo_fw_cfg_t *cfg)
{
    char        order[64];
    char        text[512] = "";
    const char *setting = config_kairo_string("boot_order", "a,cd,c");

    snprintf(order, sizeof(order), "%s", setting);
    for (char *item = strtok(order, ","); item != NULL; item = strtok(NULL, ",")) {
        char line[96] = "";
        if (!strcmp(item, "a"))
            snprintf(line, sizeof(line), "/pci@i0cf8/isa@1/fdc@03f0/floppy@0\n");
        else if (!strcmp(item, "c")) {
            for (int i = 0; i < HDD_NUM; i++) {
                if ((hdd[i].bus_type == HDD_BUS_IDE) && ide_path(line, sizeof(line), hdd[i].ide_channel))
                    break;
            }
        } else if (!strcmp(item, "cd")) {
            for (int i = 0; i < CDROM_NUM; i++) {
                if ((cdrom[i].bus_type == CDROM_BUS_ATAPI) && ide_path(line, sizeof(line), cdrom[i].ide_channel))
                    break;
            }
        } else
            fatal("KairoX86 PC: boot_order names \"%s\"; it takes a, c and cd\n", item);
        if ((strlen(text) + strlen(line)) >= sizeof(text))
            fatal("KairoX86 PC: boot_order is too long\n");
        strcat(text, line);
    }
    kairo_fw_cfg_add_file(cfg, "bootorder", text, (uint32_t) strlen(text));
}

static void
kairo_pc_fw_cfg(kairo_fw_cfg_t *cfg, uint32_t ram_kb)
{
    const uint16_t one       = 1;
    const uint16_t zero16    = 0;
    const uint64_t zero64    = 0;
    const uint32_t zero32    = 0;
    const uint8_t  irq0      = 0;
    const uint32_t ram_bytes = ram_kb * 1024;

    kairo_fw_cfg_add(cfg, FW_CFG_NOGRAPHIC, &zero16, sizeof(zero16));
    kairo_fw_cfg_add(cfg, FW_CFG_NB_CPUS, &one, sizeof(one));
    kairo_fw_cfg_add(cfg, FW_CFG_MAX_CPUS, &one, sizeof(one));
    kairo_fw_cfg_add(cfg, FW_CFG_NUMA, &zero64, sizeof(zero64));
    kairo_fw_cfg_add(cfg, FW_CFG_BOOT_MENU, &zero16, sizeof(zero16));
    kairo_fw_cfg_add(cfg, FW_CFG_ACPI_TABLES, &zero16, sizeof(zero16));
    kairo_fw_cfg_add(cfg, FW_CFG_SMBIOS_ENTRIES, &zero16, sizeof(zero16));
    /* No I/O APIC: the timer is IRQ 0 on the PIC, not overridden. */
    kairo_fw_cfg_add(cfg, FW_CFG_IRQ0_OVERRIDE, &irq0, sizeof(irq0));
    kairo_fw_cfg_add(cfg, FW_CFG_E820_TABLE, &zero32, sizeof(zero32));

    /* The memory map: all the RAM, from 0 (SeaBIOS carves out its own areas). */
    {
        kairo_buf_t e820 = { 0 };
        kairo_buf_u64(&e820, 0);
        kairo_buf_u64(&e820, ram_bytes);
        kairo_buf_u32(&e820, 1); /* RAM */
        kairo_fw_cfg_add_file(cfg, "etc/e820", e820.data, e820.len);
        kairo_buf_free(&e820);
    }

    kairo_pc_bootorder(cfg);
    kairo_pc_acpi_tables(cfg, ram_bytes);
    kairo_pc_smbios_tables(cfg, ram_kb);
}

int
machine_at_kairo_pc_init(const machine_t *model)
{
    int ret;

    ret = bios_load_linear(KAIRO_PC_BIOS_PATH, 0x000c0000, 262144, 0);

    if (bios_only || !ret)
        return ret;

    machine_at_common_init(model);

    /* One A20 state, as on QEMU's PC: SeaBIOS turns A20 on through port 92h, and DOS
       memory managers then turn it off through the keyboard controller. */
    mem_a20_single = 1;

    pci_init(PCI_CONFIG_TYPE_1);
    pci_register_slot(0x00, PCI_CARD_NORTHBRIDGE, 0, 0, 0, 0);
    pci_register_slot(0x01, PCI_CARD_SOUTHBRIDGE, 1, 2, 3, 4);
    for (int slot = KAIRO_PC_FIRST_SLOT; slot < (KAIRO_PC_FIRST_SLOT + KAIRO_PC_SLOTS); slot++) {
        /* Pin p of device d is PIRQ ((d - 1 + p) & 3): SeaBIOS's $PIR and the DSDT's _PRT. */
        pci_register_slot(slot, PCI_CARD_NORMAL, ((slot - 1) & 3) + 1, (slot & 3) + 1,
                          ((slot + 1) & 3) + 1, ((slot + 2) & 3) + 1);
    }

    device_add(&i440fx_device);
    device_add(&piix4_device);
    device_add_params(machine_get_kbc_device(machine), (void *) model->kbc_params);

    if (fdc_current[0] == FDC_INTERNAL)
        device_add(&fdc_at_device);
    device_add_inst(&ns16550_device, 1);
    device_add_inst(&ns16550_device, 2);
    {
        lpt_t *lpt = device_add_inst(&lpt_port_device, 1);
        lpt_port_setup(lpt, LPT1_ADDR);
        lpt_port_irq(lpt, LPT1_IRQ);
    }

    /* The PIIX4's RTC holds the CMOS, loaded when it was added. */
    kairo_pc_cmos(nvr_get_current(), mem_size);

    kairo_pc_fw_cfg(device_add(&kairo_fw_cfg_device), mem_size);

    return ret;
}
