/*
 * KairoX86's free machine (KairoX86 issue "free machine"): a PC built from 86Box's Intel 440FX and
 * PIIX4 emulation that boots on SeaBIOS, which the app ships, so it needs no firmware from the
 * player. SeaBIOS runs on it as it runs on QEMU's "pc" machine: the host bridge carries QEMU's
 * subsystem ID, a firmware configuration device (fw_cfg) hands it the machine's RAM, boot order,
 * ACPI and SMBIOS tables, and its APM port enables ACPI as QEMU's PIIX4 does.
 *
 * Everything here is KairoX86's own code, written from SeaBIOS's side of the interface (its
 * src/fw/paravirt.c, romfile_loader.h and biostables.c, LGPL-3.0) and the ACPI and SMBIOS
 * specifications; none of it comes from QEMU.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef EMU_KAIRO_PC_H
#define EMU_KAIRO_PC_H

#include <stdint.h>

/* The firmware the machine boots, at its place in the ROM set (the app ships it). */
#define KAIRO_PC_BIOS_PATH "roms/machines/kairo_pc/seabios.bin"

/* The I/O base SeaBIOS gives the PIIX4's power management registers when the tables come from
   fw_cfg, and the SMBus registers' (SeaBIOS's pciinit.c). The ACPI tables describe these. */
#define KAIRO_PC_PM_BASE    0x0600
#define KAIRO_PC_SMBUS_BASE 0x0700

/* The PCI slots, by device number: SeaBIOS's interrupt routing table and the DSDT's _PRT both route
   device d's pin p (0 = INTA#) to PIRQ ((d - 1 + p) & 3), the PIIX's routing registers 60h-63h. */
#define KAIRO_PC_FIRST_SLOT 0x02
#define KAIRO_PC_SLOTS      5

/* A growing byte buffer the tables are built in. */
typedef struct kairo_buf_t {
    uint8_t *data;
    uint32_t len;
    uint32_t cap;
} kairo_buf_t;

extern void     kairo_buf_free(kairo_buf_t *b);
extern uint32_t kairo_buf_put(kairo_buf_t *b, const void *data, uint32_t len);
extern uint32_t kairo_buf_zero(kairo_buf_t *b, uint32_t len);
extern uint32_t kairo_buf_u8(kairo_buf_t *b, uint8_t v);
extern uint32_t kairo_buf_u16(kairo_buf_t *b, uint16_t v);
extern uint32_t kairo_buf_u32(kairo_buf_t *b, uint32_t v);
extern uint32_t kairo_buf_u64(kairo_buf_t *b, uint64_t v);
extern void     kairo_buf_set_u16(kairo_buf_t *b, uint32_t at, uint16_t v);
extern void     kairo_buf_set_u32(kairo_buf_t *b, uint32_t at, uint32_t v);
extern void     kairo_buf_align(kairo_buf_t *b, uint32_t align);

/* The firmware configuration device: SeaBIOS selects an item by writing its key to port 510h and
   reads it a byte at a time from port 511h. */
typedef struct kairo_fw_cfg_t kairo_fw_cfg_t;

#ifdef EMU_DEVICE_H
extern const device_t kairo_fw_cfg_device;
#endif

/* An item at a fixed key, or a named file (keys from 20h, listed at key 19h); both copy the data. */
extern void kairo_fw_cfg_add(kairo_fw_cfg_t *cfg, uint16_t key, const void *data, uint32_t len);
extern void kairo_fw_cfg_add_file(kairo_fw_cfg_t *cfg, const char *name, const void *data, uint32_t len);

/* The machine's tables, built from its configuration into fw_cfg files:
   etc/acpi/rsdp, etc/acpi/tables and etc/table-loader (kairo_pc_acpi.c), and
   etc/smbios/smbios-anchor and etc/smbios/smbios-tables (kairo_pc_smbios.c). */
extern void kairo_pc_acpi_tables(kairo_fw_cfg_t *cfg, uint32_t ram_below_4g);
extern void kairo_pc_smbios_tables(kairo_fw_cfg_t *cfg, uint32_t ram_kb);

#endif /*EMU_KAIRO_PC_H*/
