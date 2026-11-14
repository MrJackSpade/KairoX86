/*
 * The ACPI tables of KairoX86's free machine (kairo_pc.h), built from the machine as configured and
 * handed to SeaBIOS through fw_cfg in its table-loader form: etc/acpi/tables holds the FACS, DSDT,
 * FADT and RSDT, etc/acpi/rsdp the RSDP, and etc/table-loader the commands that place them in
 * memory, link their pointers and fill in their checksums (SeaBIOS's romfile_loader.h).
 *
 * The tables are ACPI 1.0, which Windows 98 reads: the DSDT describes the PCI root (its windows and
 * the interrupt routing every slot's pins take, the same as SeaBIOS's $PIR), the PIIX4's ISA devices
 * the machine has, and the four PCI interrupt links the PIIX4's PIRQ registers steer. The FADT gives
 * the PIIX4's power management registers at the base SeaBIOS programs (KAIRO_PC_PM_BASE).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/device.h>
#include <86box/io.h>
#include <86box/timer.h>
#include <86box/lpt.h>
#include <86box/serial.h>
#include <86box/fdd.h>
#include <86box/kairo_pc.h>

typedef kairo_buf_t aml_t;

/* ---- AML encoding (ACPI 1.0, section 16) ---- */

#define AML_ZERO       0x00
#define AML_ONE        0x01
#define AML_ONES       0xff
#define AML_NAME       0x08
#define AML_BYTE       0x0a
#define AML_WORD       0x0b
#define AML_DWORD      0x0c
#define AML_STRING     0x0d
#define AML_SCOPE      0x10
#define AML_BUFFER     0x11
#define AML_PACKAGE    0x12
#define AML_METHOD     0x14
#define AML_LOCAL0     0x60
#define AML_ARG0       0x68
#define AML_STORE      0x70
#define AML_DECREMENT  0x76
#define AML_SHIFTLEFT  0x79
#define AML_AND        0x7b
#define AML_OR         0x7d
#define AML_FINDSETRB  0x82
#define AML_CREATEWORD 0x8b
#define AML_LLESS      0x95
#define AML_IF         0xa0
#define AML_ELSE       0xa1
#define AML_RETURN     0xa4
#define AML_EXT        0x5b
#define AML_EXT_REGION 0x80
#define AML_EXT_FIELD  0x81
#define AML_EXT_DEVICE 0x82
#define AML_EXT_PROC   0x83

static void
aml_op(aml_t *a, uint8_t op)
{
    kairo_buf_u8(a, op);
}

/* A name path: "\" for the root, "^" for each parent, then 1-4 character segments split by ".". */
static void
aml_name(aml_t *a, const char *path)
{
    const char *seg[8];
    int         lens[8];
    int         n = 0;

    while (*path == '\\' || *path == '^')
        aml_op(a, (uint8_t) *path++);
    if (*path == '\0') {
        aml_op(a, 0x00); /* NullName */
        return;
    }
    while (*path) {
        const char *dot = strchr(path, '.');
        const int   len = dot ? (int) (dot - path) : (int) strlen(path);
        if ((n == 8) || (len < 1) || (len > 4))
            fatal("KairoX86 PC: bad ACPI name in \"%s\"\n", path);
        seg[n]    = path;
        lens[n++] = len;
        path += len + (dot ? 1 : 0);
    }
    if (n == 2)
        aml_op(a, 0x2e); /* DualNamePrefix */
    else if (n > 2) {
        aml_op(a, 0x2f); /* MultiNamePrefix */
        aml_op(a, (uint8_t) n);
    }
    for (int i = 0; i < n; i++) {
        for (int c = 0; c < 4; c++)
            aml_op(a, (c < lens[i]) ? (uint8_t) seg[i][c] : '_');
    }
}

static void
aml_int(aml_t *a, uint32_t v)
{
    if (v == 0)
        aml_op(a, AML_ZERO);
    else if (v == 1)
        aml_op(a, AML_ONE);
    else if (v <= 0xff) {
        aml_op(a, AML_BYTE);
        kairo_buf_u8(a, (uint8_t) v);
    } else if (v <= 0xffff) {
        aml_op(a, AML_WORD);
        kairo_buf_u16(a, (uint16_t) v);
    } else {
        aml_op(a, AML_DWORD);
        kairo_buf_u32(a, v);
    }
}

static void
aml_dword(aml_t *a, uint32_t v)
{
    aml_op(a, AML_DWORD);
    kairo_buf_u32(a, v);
}

static void
aml_string(aml_t *a, const char *s)
{
    aml_op(a, AML_STRING);
    kairo_buf_put(a, s, (uint32_t) strlen(s) + 1);
}

/* A compressed EISA ID ("PNP0A03") as the DWord ACPI stores it. */
static void
aml_eisaid(aml_t *a, const char *id)
{
    const uint8_t c0 = id[0] - '@';
    const uint8_t c1 = id[1] - '@';
    const uint8_t c2 = id[2] - '@';
    uint8_t       hex[4];

    for (int i = 0; i < 4; i++) {
        const char h = id[3 + i];
        hex[i] = (h >= 'A') ? (h - 'A' + 10) : (h - '0');
    }
    aml_op(a, AML_DWORD);
    aml_op(a, (uint8_t) ((c0 << 2) | (c1 >> 3)));
    aml_op(a, (uint8_t) (((c1 << 5) & 0xe0) | c2));
    aml_op(a, (uint8_t) ((hex[0] << 4) | hex[1]));
    aml_op(a, (uint8_t) ((hex[2] << 4) | hex[3]));
}

/* A PkgLength for a body of len bytes (the encoding counts itself). */
static void
aml_pkglen(aml_t *a, uint32_t len)
{
    int n;

    if ((len + 1) < 0x40) {
        aml_op(a, (uint8_t) (len + 1));
        return;
    }
    if ((len + 2) < 0x1000)
        n = 2;
    else if ((len + 3) < 0x100000)
        n = 3;
    else
        n = 4;
    len += n;
    aml_op(a, (uint8_t) (((n - 1) << 6) | (len & 0x0f)));
    for (int i = 1; i < n; i++)
        aml_op(a, (uint8_t) (len >> (4 + 8 * (i - 1))));
}

/* op [ext] PkgLength body, consuming body. */
static void
aml_block(aml_t *a, int ext, uint8_t op, aml_t *body)
{
    if (ext)
        aml_op(a, AML_EXT);
    aml_op(a, op);
    aml_pkglen(a, body->len);
    kairo_buf_put(a, body->data, body->len);
    kairo_buf_free(body);
}

static void
aml_append(aml_t *a, aml_t *part)
{
    kairo_buf_put(a, part->data, part->len);
    kairo_buf_free(part);
}

/* Name(name, value), consuming value. */
static void
aml_name_obj(aml_t *a, const char *name, aml_t *value)
{
    aml_op(a, AML_NAME);
    aml_name(a, name);
    aml_append(a, value);
}

static void
aml_name_int(aml_t *a, const char *name, uint32_t v)
{
    aml_t value = { 0 };
    aml_int(&value, v);
    aml_name_obj(a, name, &value);
}

static void
aml_name_eisaid(aml_t *a, const char *name, const char *id)
{
    aml_t value = { 0 };
    aml_eisaid(&value, id);
    aml_name_obj(a, name, &value);
}

/* Buffer(){bytes}, consuming bytes. */
static void
aml_buffer(aml_t *a, aml_t *bytes)
{
    aml_t body = { 0 };
    aml_int(&body, bytes->len);
    aml_append(&body, bytes);
    aml_block(a, 0, AML_BUFFER, &body);
}

/* Device(name){body}, Scope(name){body}, consuming body (which must not hold the name). */
static void
aml_named_block(aml_t *a, int ext, uint8_t op, const char *name, aml_t *body)
{
    aml_t whole = { 0 };
    aml_name(&whole, name);
    aml_append(&whole, body);
    aml_block(a, ext, op, &whole);
}

static void
aml_method(aml_t *a, const char *name, uint8_t args, int serialized, aml_t *body)
{
    aml_t whole = { 0 };
    aml_name(&whole, name);
    aml_op(&whole, (uint8_t) (args | (serialized ? 0x08 : 0x00)));
    aml_append(&whole, body);
    aml_block(a, 0, AML_METHOD, &whole);
}

/* ---- Resource descriptors (ACPI 1.0, section 6.4) ---- */

static void
rt_io(aml_t *r, uint16_t base, uint8_t align, uint8_t len)
{
    const uint8_t d[8] = { 0x47, 0x01, base & 0xff, base >> 8, base & 0xff, base >> 8, align, len };
    kairo_buf_put(r, d, sizeof(d));
}

static void
rt_irq(aml_t *r, int irq)
{
    const uint16_t mask = 1 << irq;
    const uint8_t  d[3] = { 0x22, mask & 0xff, mask >> 8 };
    kairo_buf_put(r, d, sizeof(d));
}

/* IRQ(Level, ActiveLow, Shared){mask} */
static void
rt_irq_shared(aml_t *r, uint16_t mask)
{
    const uint8_t d[4] = { 0x23, mask & 0xff, mask >> 8, 0x18 };
    kairo_buf_put(r, d, sizeof(d));
}

/* DMA(Compatibility, NotBusMaster, Transfer8){channel} */
static void
rt_dma(aml_t *r, int channel)
{
    const uint8_t d[3] = { 0x2a, (uint8_t) (1 << channel), 0x00 };
    kairo_buf_put(r, d, sizeof(d));
}

/* A Word address space descriptor: ResourceProducer, MinFixed, MaxFixed, PosDecode. */
static void
rt_word(aml_t *r, uint8_t type, uint8_t type_flags, uint16_t min, uint16_t max)
{
    const uint16_t len  = (uint16_t) (max - min + 1);
    const uint8_t  d[16] = { 0x88, 13, 0, type, 0x0c, type_flags, 0, 0,
                             min & 0xff, min >> 8, max & 0xff, max >> 8, 0, 0, len & 0xff, len >> 8 };
    kairo_buf_put(r, d, sizeof(d));
}

/* A DWord memory range: ResourceProducer, MinFixed, MaxFixed, PosDecode, Cacheable, ReadWrite. */
static void
rt_dword_mem(aml_t *r, uint32_t min, uint32_t max)
{
    kairo_buf_u8(r, 0x87);
    kairo_buf_u16(r, 23);
    kairo_buf_u8(r, 0);    /* memory */
    kairo_buf_u8(r, 0x0c);
    kairo_buf_u8(r, 0x03);
    kairo_buf_u32(r, 0);   /* granularity */
    kairo_buf_u32(r, min);
    kairo_buf_u32(r, max);
    kairo_buf_u32(r, 0);   /* translation */
    kairo_buf_u32(r, max - min + 1);
}

/* Name(name, ResourceTemplate(){descriptors}), consuming the descriptors. */
static void
aml_name_rt(aml_t *a, const char *name, aml_t *descriptors)
{
    aml_t value = { 0 };
    kairo_buf_u8(descriptors, 0x79); /* End tag, checksum 0 */
    kairo_buf_u8(descriptors, 0x00);
    aml_buffer(&value, descriptors);
    aml_name_obj(a, name, &value);
}

/* A legacy ISA device: _HID and _CRS. */
static void
isa_device(aml_t *isa, const char *name, const char *hid, aml_t *crs)
{
    aml_t body = { 0 };
    aml_name_eisaid(&body, "_HID", hid);
    aml_name_rt(&body, "_CRS", crs);
    aml_named_block(isa, 1, AML_EXT_DEVICE, name, &body);
}

/* ---- The DSDT ---- */

/* The PCI interrupt link for PIRQ n (0-3), its PIIX4 routing register PRQn (bit 7: disabled). */
static void
pci_link(aml_t *sb, int n)
{
    char  dev[5], reg[32];
    aml_t body = { 0 }, rt = { 0 }, m = { 0 }, then = { 0 }, els = { 0 };

    snprintf(dev, sizeof(dev), "LNK%c", 'A' + n);
    snprintf(reg, sizeof(reg), "\\_SB.PCI0.ISA.PRQ%c", 'A' + n);

    aml_name_eisaid(&body, "_HID", "PNP0C0F");
    aml_name_int(&body, "_UID", n + 1);
    /* The IRQs SeaBIOS's $PIR lets each link take (bitmap DEF8h). */
    rt_irq_shared(&rt, 0xdef8);
    aml_name_rt(&body, "_PRS", &rt);

    /* _STA: If (LLess(PRQn, 0x80)) Return(0x0B) Else Return(0x09) */
    aml_op(&m, AML_IF);
    {
        aml_t pred = { 0 };
        aml_op(&pred, AML_LLESS);
        aml_name(&pred, reg);
        aml_int(&pred, 0x80);
        aml_op(&then, AML_RETURN);
        aml_int(&then, 0x0b);
        aml_append(&pred, &then);
        aml_pkglen(&m, pred.len);
        aml_append(&m, &pred);
    }
    aml_op(&els, AML_RETURN);
    aml_int(&els, 0x09);
    aml_block(&m, 0, AML_ELSE, &els);
    aml_method(&body, "_STA", 0, 0, &m);

    /* _DIS: Or(PRQn, 0x80, PRQn) */
    aml_op(&m, AML_OR);
    aml_name(&m, reg);
    aml_int(&m, 0x80);
    aml_name(&m, reg);
    aml_method(&body, "_DIS", 0, 0, &m);

    /* _CRS: Name(BUF0, ResourceTemplate(){IRQ(Level, ActiveLow, Shared){}})
             CreateWordField(BUF0, 1, IRQW)
             If (LLess(PRQn, 0x80)) { ShiftLeft(One, And(PRQn, 0x0F), IRQW) }
             Return(BUF0) */
    {
        aml_t empty = { 0 };
        rt_irq_shared(&empty, 0x0000);
        aml_name_rt(&m, "BUF0", &empty);
        aml_op(&m, AML_CREATEWORD);
        aml_name(&m, "BUF0");
        aml_int(&m, 1);
        aml_name(&m, "IRQW");
        aml_t pred = { 0 };
        aml_op(&pred, AML_LLESS);
        aml_name(&pred, reg);
        aml_int(&pred, 0x80);
        aml_op(&pred, AML_SHIFTLEFT);
        aml_int(&pred, 1);
        aml_op(&pred, AML_AND);
        aml_name(&pred, reg);
        aml_int(&pred, 0x0f);
        aml_op(&pred, 0x00); /* no target */
        aml_name(&pred, "IRQW");
        aml_block(&m, 0, AML_IF, &pred);
        aml_op(&m, AML_RETURN);
        aml_name(&m, "BUF0");
    }
    aml_method(&body, "_CRS", 0, 1, &m);

    /* _SRS: CreateWordField(Arg0, 1, IRQW) FindSetRightBit(IRQW, Local0) Decrement(Local0)
             Store(Local0, PRQn) */
    aml_op(&m, AML_CREATEWORD);
    aml_op(&m, AML_ARG0);
    aml_int(&m, 1);
    aml_name(&m, "IRQW");
    aml_op(&m, AML_FINDSETRB);
    aml_name(&m, "IRQW");
    aml_op(&m, AML_LOCAL0);
    aml_op(&m, AML_DECREMENT);
    aml_op(&m, AML_LOCAL0);
    aml_op(&m, AML_STORE);
    aml_op(&m, AML_LOCAL0);
    aml_name(&m, reg);
    aml_method(&body, "_SRS", 1, 1, &m);

    aml_named_block(sb, 1, AML_EXT_DEVICE, dev, &body);
}

/* _PRT: every pin of every device from the PIIX4 (device 1) to the last slot, to its link. */
static void
pci_prt(aml_t *pci0)
{
    aml_t      elements = { 0 };
    const int  last     = KAIRO_PC_FIRST_SLOT + KAIRO_PC_SLOTS - 1;
    int        count    = 0;

    for (int dev = 1; dev <= last; dev++) {
        for (int pin = 0; pin < 4; pin++) {
            char  link[16];
            aml_t entry = { 0 }, pkg = { 0 };
            snprintf(link, sizeof(link), "\\_SB.LNK%c", 'A' + ((dev - 1 + pin) & 3));
            aml_op(&entry, 4);
            aml_dword(&entry, ((uint32_t) dev << 16) | 0xffff);
            aml_int(&entry, pin);
            aml_name(&entry, link);
            aml_int(&entry, 0);
            aml_block(&pkg, 0, AML_PACKAGE, &entry);
            aml_append(&elements, &pkg);
            count++;
        }
    }
    aml_t list = { 0 }, value = { 0 };
    aml_op(&list, (uint8_t) count);
    aml_append(&list, &elements);
    aml_block(&value, 0, AML_PACKAGE, &list);
    aml_name_obj(pci0, "_PRT", &value);
}

static int
floppy_present(void)
{
    for (int i = 0; i < FDD_NUM; i++) {
        if (strcmp(fdd_get_internal_name(fdd_get_type(&drives[i])), "none") != 0)
            return 1;
    }
    return 0;
}

static void
isa_bridge(aml_t *pci0)
{
    aml_t isa = { 0 }, rt = { 0 }, fields = { 0 }, region = { 0 };

    aml_name_int(&isa, "_ADR", 0x00010000);

    /* The PIIX4's PIRQ routing registers, 60h-63h of function 0's configuration space. */
    aml_name(&region, "PIRQ");
    aml_op(&region, 0x02); /* PCI_Config */
    aml_int(&region, 0x60);
    aml_int(&region, 0x04);
    aml_op(&isa, AML_EXT);
    aml_op(&isa, AML_EXT_REGION);
    aml_append(&isa, &region);
    aml_name(&fields, "PIRQ");
    aml_op(&fields, 0x01); /* ByteAcc, NoLock, Preserve */
    for (int n = 0; n < 4; n++) {
        const char name[4] = { 'P', 'R', 'Q', (char) ('A' + n) };
        kairo_buf_put(&fields, name, 4);
        aml_op(&fields, 8);
    }
    aml_block(&isa, 1, AML_EXT_FIELD, &fields);

    rt_io(&rt, 0x60, 1, 1);
    rt_io(&rt, 0x64, 1, 1);
    rt_irq(&rt, 1);
    isa_device(&isa, "KBD", "PNP0303", &rt);
    rt_irq(&rt, 12);
    isa_device(&isa, "MOU", "PNP0F13", &rt);
    rt_io(&rt, 0x20, 1, 2);
    rt_io(&rt, 0xa0, 1, 2);
    rt_irq(&rt, 2);
    isa_device(&isa, "PIC", "PNP0000", &rt);
    rt_io(&rt, 0x40, 1, 4);
    rt_irq(&rt, 0);
    isa_device(&isa, "TMR", "PNP0100", &rt);
    rt_io(&rt, 0x70, 1, 2);
    rt_irq(&rt, 8);
    isa_device(&isa, "RTC", "PNP0B00", &rt);
    rt_io(&rt, 0x00, 1, 16);
    rt_io(&rt, 0x80, 1, 16);
    rt_io(&rt, 0xc0, 1, 32);
    rt_dma(&rt, 4);
    isa_device(&isa, "DMAC", "PNP0200", &rt);
    rt_io(&rt, 0x61, 1, 1);
    isa_device(&isa, "SPKR", "PNP0800", &rt);
    rt_io(&rt, 0xf0, 1, 16);
    rt_irq(&rt, 13);
    isa_device(&isa, "FPU", "PNP0C04", &rt);
    if (floppy_present()) {
        rt_io(&rt, 0x3f2, 0, 4);
        rt_io(&rt, 0x3f7, 0, 1);
        rt_irq(&rt, 6);
        rt_dma(&rt, 2);
        isa_device(&isa, "FDC0", "PNP0700", &rt);
    }
    if (com_ports[0].enabled) {
        rt_io(&rt, 0x3f8, 0, 8);
        rt_irq(&rt, 4);
        isa_device(&isa, "COM1", "PNP0501", &rt);
    }
    if (com_ports[1].enabled) {
        rt_io(&rt, 0x2f8, 0, 8);
        rt_irq(&rt, 3);
        isa_device(&isa, "COM2", "PNP0501", &rt);
    }
    if (lpt_ports[0].enabled) {
        rt_io(&rt, 0x378, 0, 8);
        rt_irq(&rt, 7);
        isa_device(&isa, "LPT1", "PNP0400", &rt);
    }
    /* The motherboard's other ports: port 92h, APM (B2h-B3h), the edge/level registers (4D0h),
       the fw_cfg ports, the PIIX4's power management and SMBus blocks. */
    rt_io(&rt, 0x92, 1, 1);
    rt_io(&rt, 0xb2, 1, 2);
    rt_io(&rt, 0x4d0, 1, 2);
    rt_io(&rt, 0x510, 1, 2);
    rt_io(&rt, KAIRO_PC_PM_BASE, 1, 64);
    rt_io(&rt, KAIRO_PC_SMBUS_BASE, 1, 16);
    {
        aml_t body = { 0 };
        aml_name_eisaid(&body, "_HID", "PNP0C02");
        aml_name_int(&body, "_UID", 1);
        aml_name_rt(&body, "_CRS", &rt);
        aml_named_block(&isa, 1, AML_EXT_DEVICE, "SYSR", &body);
    }

    aml_named_block(pci0, 1, AML_EXT_DEVICE, "ISA", &isa);
}

static void
build_dsdt(aml_t *dsdt, uint32_t ram_below_4g)
{
    aml_t pr = { 0 }, sb = { 0 }, pci0 = { 0 }, rt = { 0 }, s5 = { 0 };

    /* The processor, its P_BLK the PIIX4's processor control block at PM base + 10h. */
    {
        aml_t cpu = { 0 };
        aml_name(&cpu, "CPU0");
        aml_op(&cpu, 0);
        kairo_buf_u32(&cpu, KAIRO_PC_PM_BASE + 0x10);
        aml_op(&cpu, 6);
        aml_block(&pr, 1, AML_EXT_PROC, &cpu);
        aml_named_block(dsdt, 0, AML_SCOPE, "\\_PR", &pr);
    }

    /* S5 (soft off): the PIIX4's SUS_TYP 0. */
    {
        aml_t list = { 0 };
        aml_op(&list, 4);
        for (int i = 0; i < 4; i++)
            aml_int(&list, 0);
        aml_block(&s5, 0, AML_PACKAGE, &list);
        aml_name_obj(dsdt, "\\_S5", &s5);
    }

    aml_name_eisaid(&pci0, "_HID", "PNP0A03");
    aml_name_int(&pci0, "_ADR", 0);
    aml_name_int(&pci0, "_UID", 0);
    rt_word(&rt, 2, 0x00, 0x0000, 0x00ff);       /* bus numbers 0-FFh */
    rt_io(&rt, 0x0cf8, 1, 8);                     /* the configuration ports */
    rt_word(&rt, 1, 0x03, 0x0000, 0x0cf7);        /* I/O below them */
    rt_word(&rt, 1, 0x03, 0x0d00, 0xffff);        /* and above */
    rt_dword_mem(&rt, 0x000a0000, 0x000bffff);    /* VGA memory */
    rt_dword_mem(&rt, ram_below_4g, 0xfebfffff);  /* the PCI hole */
    aml_name_rt(&pci0, "_CRS", &rt);
    pci_prt(&pci0);
    isa_bridge(&pci0);
    aml_named_block(&sb, 1, AML_EXT_DEVICE, "PCI0", &pci0);
    for (int n = 0; n < 4; n++)
        pci_link(&sb, n);
    aml_named_block(dsdt, 0, AML_SCOPE, "\\_SB", &sb);
}

/* ---- The tables and their loader ---- */

#define LOADER_FILE   56
#define LOADER_ENTRY  128
#define ZONE_HIGH     1
#define ZONE_FSEG     2
#define TABLES_FILE   "etc/acpi/tables"
#define RSDP_FILE     "etc/acpi/rsdp"

static void
loader_name(kairo_buf_t *l, const char *name)
{
    char field[LOADER_FILE] = { 0 };
    strncpy(field, name, LOADER_FILE - 1);
    kairo_buf_put(l, field, LOADER_FILE);
}

static void
loader_allocate(kairo_buf_t *l, const char *file, uint32_t align, uint8_t zone)
{
    const uint32_t at = l->len;
    kairo_buf_u32(l, 1);
    loader_name(l, file);
    kairo_buf_u32(l, align);
    kairo_buf_u8(l, zone);
    kairo_buf_zero(l, LOADER_ENTRY - (l->len - at));
}

static void
loader_pointer(kairo_buf_t *l, const char *dest, const char *src, uint32_t offset, uint8_t size)
{
    const uint32_t at = l->len;
    kairo_buf_u32(l, 2);
    loader_name(l, dest);
    loader_name(l, src);
    kairo_buf_u32(l, offset);
    kairo_buf_u8(l, size);
    kairo_buf_zero(l, LOADER_ENTRY - (l->len - at));
}

static void
loader_checksum(kairo_buf_t *l, const char *file, uint32_t offset, uint32_t start, uint32_t length)
{
    const uint32_t at = l->len;
    kairo_buf_u32(l, 3);
    loader_name(l, file);
    kairo_buf_u32(l, offset);
    kairo_buf_u32(l, start);
    kairo_buf_u32(l, length);
    kairo_buf_zero(l, LOADER_ENTRY - (l->len - at));
}

/* A description table's 36-byte header, its length and checksum filled in later; returns its start. */
static uint32_t
table_header(kairo_buf_t *t, const char *signature, uint8_t revision, const char *table_id)
{
    const uint32_t at = t->len;
    char           id[8];

    memset(id, ' ', sizeof(id));
    memcpy(id, table_id, strlen(table_id) < 8 ? strlen(table_id) : 8);
    kairo_buf_put(t, signature, 4);
    kairo_buf_u32(t, 0);           /* length */
    kairo_buf_u8(t, revision);
    kairo_buf_u8(t, 0);            /* checksum */
    kairo_buf_put(t, "KAIRO ", 6); /* OEM ID */
    kairo_buf_put(t, id, 8);       /* OEM table ID */
    kairo_buf_u32(t, 1);           /* OEM revision */
    kairo_buf_put(t, "KAIR", 4);   /* creator */
    kairo_buf_u32(t, 1);           /* creator revision */
    return at;
}

/* Ends the table started at `at`: its length, and a loader checksum over it. */
static void
table_end(kairo_buf_t *t, kairo_buf_t *loader, uint32_t at)
{
    kairo_buf_set_u32(t, at + 4, t->len - at);
    loader_checksum(loader, TABLES_FILE, at + 9, at, t->len - at);
}

void
kairo_pc_acpi_tables(kairo_fw_cfg_t *cfg, uint32_t ram_below_4g)
{
    kairo_buf_t tables = { 0 }, rsdp = { 0 }, loader = { 0 }, dsdt = { 0 };

    loader_allocate(&loader, TABLES_FILE, 64, ZONE_HIGH);
    loader_allocate(&loader, RSDP_FILE, 16, ZONE_FSEG);

    /* FACS (64-byte aligned, at the start of the allocation). */
    const uint32_t facs = tables.len;
    kairo_buf_put(&tables, "FACS", 4);
    kairo_buf_u32(&tables, 64);
    kairo_buf_zero(&tables, 56);

    /* DSDT */
    const uint32_t dsdt_at = table_header(&tables, "DSDT", 1, "KX86PC");
    build_dsdt(&dsdt, ram_below_4g);
    kairo_buf_put(&tables, dsdt.data, dsdt.len);
    kairo_buf_free(&dsdt);
    table_end(&tables, &loader, dsdt_at);

    /* FADT, revision 1 (116 bytes) */
    kairo_buf_align(&tables, 4);
    const uint32_t fadt = table_header(&tables, "FACP", 1, "KX86PC");
    const uint32_t fadt_facs = kairo_buf_u32(&tables, facs);    /* FIRMWARE_CTRL, relocated */
    const uint32_t fadt_dsdt = kairo_buf_u32(&tables, dsdt_at); /* DSDT, relocated */
    kairo_buf_u8(&tables, 0);                                   /* INT_MODEL: dual PIC */
    kairo_buf_u8(&tables, 0);
    kairo_buf_u16(&tables, 9);                                  /* SCI_INT */
    kairo_buf_u32(&tables, 0xb2);                               /* SMI_CMD */
    kairo_buf_u8(&tables, 0xf1);                                /* ACPI_ENABLE */
    kairo_buf_u8(&tables, 0xf0);                                /* ACPI_DISABLE */
    kairo_buf_u8(&tables, 0);                                   /* S4BIOS_REQ */
    kairo_buf_u8(&tables, 0);
    kairo_buf_u32(&tables, KAIRO_PC_PM_BASE + 0x00);            /* PM1a_EVT_BLK */
    kairo_buf_u32(&tables, 0);
    kairo_buf_u32(&tables, KAIRO_PC_PM_BASE + 0x04);            /* PM1a_CNT_BLK */
    kairo_buf_u32(&tables, 0);
    kairo_buf_u32(&tables, 0);                                  /* PM2_CNT_BLK */
    kairo_buf_u32(&tables, KAIRO_PC_PM_BASE + 0x08);            /* PM_TMR_BLK */
    kairo_buf_u32(&tables, KAIRO_PC_PM_BASE + 0x0c);            /* GPE0_BLK */
    kairo_buf_u32(&tables, 0);
    kairo_buf_u8(&tables, 4);                                   /* PM1_EVT_LEN */
    kairo_buf_u8(&tables, 2);                                   /* PM1_CNT_LEN */
    kairo_buf_u8(&tables, 0);
    kairo_buf_u8(&tables, 4);                                   /* PM_TM_LEN */
    kairo_buf_u8(&tables, 4);                                   /* GPE0_BLK_LEN */
    kairo_buf_u8(&tables, 0);
    kairo_buf_u8(&tables, 0);
    kairo_buf_u8(&tables, 0);
    kairo_buf_u16(&tables, 0x0fff);                             /* P_LVL2_LAT: no C2 */
    kairo_buf_u16(&tables, 0xffff);                             /* P_LVL3_LAT: no C3 */
    kairo_buf_u16(&tables, 0);
    kairo_buf_u16(&tables, 0);
    kairo_buf_u8(&tables, 0);                                   /* DUTY_OFFSET */
    kairo_buf_u8(&tables, 0);
    kairo_buf_u8(&tables, 0x0d);                                /* DAY_ALRM */
    kairo_buf_u8(&tables, 0);                                   /* MON_ALRM */
    kairo_buf_u8(&tables, 0x32);                                /* CENTURY */
    kairo_buf_zero(&tables, 3);
    /* WBINVD, PROC_C1, SLP_BUTTON (none), RTC_S4 */
    kairo_buf_u32(&tables, (1 << 0) | (1 << 2) | (1 << 5) | (1 << 7));
    table_end(&tables, &loader, fadt);

    /* RSDT: the FADT */
    kairo_buf_align(&tables, 4);
    const uint32_t rsdt = table_header(&tables, "RSDT", 1, "KX86PC");
    const uint32_t rsdt_fadt = kairo_buf_u32(&tables, fadt);
    table_end(&tables, &loader, rsdt);

    /* RSDP, revision 0 (ACPI 1.0) */
    kairo_buf_put(&rsdp, "RSD PTR ", 8);
    kairo_buf_u8(&rsdp, 0);
    kairo_buf_put(&rsdp, "KAIRO ", 6);
    kairo_buf_u8(&rsdp, 0);
    const uint32_t rsdp_rsdt = kairo_buf_u32(&rsdp, rsdt);

    /* Pointers first, then the checksums over the linked tables (SeaBIOS runs them in order). */
    kairo_buf_t commands = { 0 };
    kairo_buf_put(&commands, loader.data, 2 * LOADER_ENTRY); /* the two allocations */
    loader_pointer(&commands, TABLES_FILE, TABLES_FILE, fadt_facs, 4);
    loader_pointer(&commands, TABLES_FILE, TABLES_FILE, fadt_dsdt, 4);
    loader_pointer(&commands, TABLES_FILE, TABLES_FILE, rsdt_fadt, 4);
    loader_pointer(&commands, RSDP_FILE, TABLES_FILE, rsdp_rsdt, 4);
    kairo_buf_put(&commands, loader.data + 2 * LOADER_ENTRY, loader.len - 2 * LOADER_ENTRY);
    loader_checksum(&commands, RSDP_FILE, 8, 0, rsdp.len);

    kairo_fw_cfg_add_file(cfg, RSDP_FILE, rsdp.data, rsdp.len);
    kairo_fw_cfg_add_file(cfg, TABLES_FILE, tables.data, tables.len);
    kairo_fw_cfg_add_file(cfg, "etc/table-loader", commands.data, commands.len);

    kairo_buf_free(&tables);
    kairo_buf_free(&rsdp);
    kairo_buf_free(&loader);
    kairo_buf_free(&commands);
}
