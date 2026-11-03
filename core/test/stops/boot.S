/*
 * KairoX86's stop tests (KairoX86#34): a floppy boot sector that stops the PC one way, chosen by
 * MODE when it is assembled (core/test/stops/make_floppies.py):
 *
 *   MODE_HALT       CLI, then HLT: the processor stops with interrupts off.
 *   MODE_KEYBOARD   The AT keyboard's "set scan code set" command with set 5, which 86Box's
 *                   keyboard stops on (fatal(), on the machine's own thread).
 *   MODE_POWER_OFF  The Intel PIIX4's ACPI soft off (SLP_TYP 0 with SLP_EN), as an operating
 *                   system powers the PC down.
 *   MODE_VOODOO     A Voodoo 2 blit with an undefined command, which 86Box's Voodoo stops on
 *                   (fatal(), on the card's FIFO thread).
 *   MODE_IDLE       Waits for interrupts forever: a PC that has not stopped.
 *
 * Every mode but MODE_HALT then waits for interrupts, so only the stop under test ends the run.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#define MODE_HALT      1
#define MODE_KEYBOARD  2
#define MODE_POWER_OFF 3
#define MODE_VOODOO    4
#define MODE_IDLE      5

    .code16
    .text
    .globl _start
_start:
    cli
    xorw    %ax, %ax
    movw    %ax, %ds
    movw    %ax, %ss
    movw    $0x7c00, %sp
    sti

#if MODE == MODE_HALT
    cli
1:  hlt
    jmp     1b
#endif

#if MODE == MODE_KEYBOARD
    call    kbd_wait_input
    movb    $0xf0, %al          /* set scan code set */
    outb    %al, $0x60
    call    kbd_wait_output
    inb     $0x60, %al          /* its ACK */
    call    kbd_wait_input
    movb    $0x05, %al          /* set 5, which no keyboard has */
    outb    %al, $0x60
    jmp     idle
#endif

#if MODE == MODE_POWER_OFF
    movl    $0x71138086, %ebx   /* the PIIX4's power management function */
    call    pci_find
    /* Its I/O at 0x4000 (PMBA), enabled (PMREGMISC bit 0). */
    movl    %ecx, %eax
    orb     $0x40, %al
    movl    $0x4001, %edx
    call    pci_write
    movl    %ecx, %eax
    orb     $0x80, %al
    movl    $0x1, %edx
    call    pci_write
    /* PMCNTRL's high byte: SLP_EN (bit 13) with SLP_TYP 0, soft off on Intel. */
    movw    $0x4005, %dx
    movb    $0x20, %al
    outb    %al, %dx
    jmp     idle
#endif

#if MODE == MODE_VOODOO
    movl    $0x0002121a, %ebx   /* 3dfx Voodoo 2 */
    call    pci_find
    movl    %ecx, %eax          /* its registers: BAR0 */
    orb     $0x10, %al
    movw    $0xcf8, %dx
    outl    %eax, %dx
    movw    $0xcfc, %dx
    inl     %dx, %eax
    andl    $0xfffffff0, %eax
    movl    %eax, %esi
    movl    %ecx, %eax          /* memory decoding on (command register bit 1) */
    orb     $0x04, %al
    movl    $0x0006, %edx
    call    pci_write
    /* Unreal mode: FS with a 4 GB limit, back in real mode. */
    cli
    lgdtl   gdt_desc
    movl    %cr0, %eax
    orb     $1, %al
    movl    %eax, %cr0
    jmp     2f
2:  movw    $8, %bx
    movw    %bx, %fs
    andb    $0xfe, %al
    movl    %eax, %cr0
    jmp     3f
3:  sti
    /* bltCommand: start (bit 31) with command 7, which the blitter does not have. */
    movl    $0x80000007, %eax
    movl    %eax, %fs:0x2f8(%esi)   /* a 32-bit address: the assembler adds the 0x67 prefix */
    /* nopCMD: a command register, which wakes the FIFO thread to run what is queued. */
    xorl    %eax, %eax
    movl    %eax, %fs:0x120(%esi)
    jmp     idle
#endif

#if MODE == MODE_IDLE
    jmp     idle
#endif

idle:
    sti
4:  hlt
    jmp     4b

#if MODE == MODE_KEYBOARD
kbd_wait_input:                 /* until the controller's input buffer is empty */
    inb     $0x64, %al
    testb   $0x02, %al
    jnz     kbd_wait_input
    ret
kbd_wait_output:                /* until a byte waits in its output buffer */
    inb     $0x64, %al
    testb   $0x01, %al
    jz      kbd_wait_output
    ret
#endif

#if MODE == MODE_POWER_OFF || MODE == MODE_VOODOO
/* ECX = the PCI configuration address (bus 0) of the first function whose vendor and device are
   EBX; waits for interrupts forever if there is none. */
pci_find:
    movl    $0x80000000, %ecx
5:  movl    %ecx, %eax
    movw    $0xcf8, %dx
    outl    %eax, %dx
    movw    $0xcfc, %dx
    inl     %dx, %eax
    cmpl    %ebx, %eax
    je      6f
    addl    $0x100, %ecx
    cmpl    $0x80010000, %ecx
    jb      5b
    jmp     idle
6:  ret

/* Writes EDX to the PCI configuration register EAX (dword aligned). */
pci_write:
    pushl   %edx
    movw    $0xcf8, %dx
    outl    %eax, %dx
    popl    %eax
    movw    $0xcfc, %dx
    outl    %eax, %dx
    ret
#endif

#if MODE == MODE_VOODOO
    .p2align 3
gdt:
    .quad   0
    .quad   0x00cf92000000ffff  /* data: base 0, limit 4 GB, writable */
gdt_desc:
    .word   gdt_desc - gdt - 1
    .long   gdt
#endif

    .org    510
    .byte   0x55, 0xaa
