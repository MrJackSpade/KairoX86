#include <stdint.h>
#include <86box/86box.h>
#include "cpu.h"
#include <86box/mem.h>
#include <86box/plat_unused.h>

#include "x86.h"
#include "x86seg_common.h"
#include "x86seg.h"
#include "x86_flags.h"
#include "386_common.h"
#include "codegen.h"
#include "codegen_ir.h"
#include "codegen_accumulate.h" /* KairoX86#396 */
#include "codegen_ops.h"
#include "codegen_ops_helpers.h"
#include "codegen_ops_jit_wrappers.h"
#include "codegen_ops_misc.h"

uint32_t
ropPUSH_r16(UNUSED(codeblock_t *block), ir_data_t *ir, uint8_t opcode, UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    sp_reg = LOAD_SP_WITH_OFFSET(ir, -2);
    uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_16(opcode & 7));
    SUB_SP(ir, 2);

    return op_pc;
}
uint32_t
ropPUSH_r32(UNUSED(codeblock_t *block), ir_data_t *ir, uint8_t opcode, UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    sp_reg = LOAD_SP_WITH_OFFSET(ir, -4);
    uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_32(opcode & 7));
    SUB_SP(ir, 4);

    return op_pc;
}

uint32_t
ropPOP_r16(UNUSED(codeblock_t *block), ir_data_t *ir, uint8_t opcode, UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);

    if (stack32)
        uop_MEM_LOAD_REG(ir, IREG_16(opcode & 7), IREG_SS_base, IREG_ESP);
    else {
        uop_MOVZX(ir, IREG_eaaddr, IREG_SP);
        uop_MEM_LOAD_REG(ir, IREG_16(opcode & 7), IREG_SS_base, IREG_eaaddr);
    }
    if ((opcode & 7) != REG_SP)
        ADD_SP(ir, 2);

    return op_pc;
}
uint32_t
ropPOP_r32(UNUSED(codeblock_t *block), ir_data_t *ir, uint8_t opcode, UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);

    if (stack32)
        uop_MEM_LOAD_REG(ir, IREG_32(opcode & 7), IREG_SS_base, IREG_ESP);
    else {
        uop_MOVZX(ir, IREG_eaaddr, IREG_SP);
        uop_MEM_LOAD_REG(ir, IREG_32(opcode & 7), IREG_SS_base, IREG_eaaddr);
    }
    if ((opcode & 7) != REG_ESP)
        ADD_SP(ir, 4);

    return op_pc;
}

/*PUSH imm. In a block rewritten again and again (CODEBLOCK_NO_IMMEDIATES)
  the immediate is read from RAM as the block runs, and not marked.*/
static uint32_t
push_imm_common(codeblock_t *block, ir_data_t *ir, uint32_t op_pc, int size32, int imm8)
{
    const int len = imm8 ? 1 : (size32 ? 4 : 2);
    int       sp_reg;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    if (block->flags & CODEBLOCK_NO_IMMEDIATES) {
        if (imm8) {
            LOAD_IMMEDIATE_FROM_RAM_8(block, ir, IREG_temp0, cs + op_pc);
            uop_MOVSX(ir, size32 ? IREG_temp0 : IREG_temp0_W, IREG_temp0_B);
        } else if (size32)
            LOAD_IMMEDIATE_FROM_RAM_32(block, ir, IREG_temp0, cs + op_pc);
        else
            LOAD_IMMEDIATE_FROM_RAM_16(block, ir, IREG_temp0, cs + op_pc);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, size32 ? -4 : -2);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, size32 ? IREG_temp0 : IREG_temp0_W);
    } else {
        uint32_t imm;

        if (imm8)
            imm = (uint32_t) (int32_t) (int8_t) fastreadb(cs + op_pc);
        else
            imm = size32 ? fastreadl(cs + op_pc) : fastreadw(cs + op_pc);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, size32 ? -4 : -2);
        if (size32)
            uop_MEM_STORE_IMM_32(ir, IREG_SS_base, sp_reg, imm);
        else
            uop_MEM_STORE_IMM_16(ir, IREG_SS_base, sp_reg, imm & 0xffff);
        codegen_mark_code_present(block, cs + op_pc, len);
    }
    SUB_SP(ir, size32 ? 4 : 2);

    return op_pc + len;
}

uint32_t
ropPUSH_imm_16(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return push_imm_common(block, ir, op_pc, 0, 0);
}
uint32_t
ropPUSH_imm_32(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return push_imm_common(block, ir, op_pc, 1, 0);
}

uint32_t
ropPUSH_imm_16_8(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return push_imm_common(block, ir, op_pc, 0, 1);
}
uint32_t
ropPUSH_imm_32_8(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return push_imm_common(block, ir, op_pc, 1, 1);
}

uint32_t
ropPOP_W(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), uint32_t fetchdat, uint32_t op_32, uint32_t op_pc)
{
    if (fetchdat & 0x38) /*8F /1-/7 are #UD*/
        return 0;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);

    codegen_mark_code_present(block, cs + op_pc, 1);
    if ((fetchdat & 0xc0) == 0xc0) {
        if (stack32)
            uop_MEM_LOAD_REG(ir, IREG_16(fetchdat & 7), IREG_SS_base, IREG_ESP);
        else {
            uop_MOVZX(ir, IREG_eaaddr, IREG_SP);
            uop_MEM_LOAD_REG(ir, IREG_16(fetchdat & 7), IREG_SS_base, IREG_eaaddr);
        }
    } else {
        x86seg *target_seg = codegen_generate_ea(ir, op_ea_seg, fetchdat, op_ssegs, &op_pc, op_32, 2);
        codegen_check_seg_write(block, ir, target_seg);
        CHECK_SEG_LIMITS(block, ir, target_seg, IREG_eaaddr, 1);

        if (stack32)
            uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_ESP);
        else {
            uop_MOVZX(ir, IREG_temp0, IREG_SP);
            uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_temp0);
        }

        uop_MEM_STORE_REG(ir, ireg_seg_base(target_seg), IREG_eaaddr, IREG_temp0_W);
    }

    if ((fetchdat & 0xc7) != (0xc0 | REG_SP))
        ADD_SP(ir, 2);

    return op_pc + 1;
}
uint32_t
ropPOP_L(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), uint32_t fetchdat, uint32_t op_32, uint32_t op_pc)
{
    if (fetchdat & 0x38) /*8F /1-/7 are #UD*/
        return 0;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);

    codegen_mark_code_present(block, cs + op_pc, 1);
    if ((fetchdat & 0xc0) == 0xc0) {
        if (stack32)
            uop_MEM_LOAD_REG(ir, IREG_32(fetchdat & 7), IREG_SS_base, IREG_ESP);
        else {
            uop_MOVZX(ir, IREG_eaaddr, IREG_SP);
            uop_MEM_LOAD_REG(ir, IREG_32(fetchdat & 7), IREG_SS_base, IREG_eaaddr);
        }
    } else {
        x86seg *target_seg = codegen_generate_ea(ir, op_ea_seg, fetchdat, op_ssegs, &op_pc, op_32, 4);
        codegen_check_seg_write(block, ir, target_seg);
        CHECK_SEG_LIMITS(block, ir, target_seg, IREG_eaaddr, 3);

        if (stack32)
            uop_MEM_LOAD_REG(ir, IREG_temp0, IREG_SS_base, IREG_ESP);
        else {
            uop_MOVZX(ir, IREG_temp0, IREG_SP);
            uop_MEM_LOAD_REG(ir, IREG_temp0, IREG_SS_base, IREG_temp0);
        }

        uop_MEM_STORE_REG(ir, ireg_seg_base(target_seg), IREG_eaaddr, IREG_temp0);
    }

    if ((fetchdat & 0xc7) != (0xc0 | REG_ESP))
        ADD_SP(ir, 4);

    return op_pc + 1;
}

#define ROP_PUSH_SEG(seg)                                                                          \
    uint32_t ropPUSH_##seg##_16(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), \
                                UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc) \
    {                                                                                              \
        int sp_reg;                                                                                \
                                                                                                   \
        uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);                                              \
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -2);                                                      \
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_##seg##_seg_W);                           \
        SUB_SP(ir, 2);                                                                             \
                                                                                                   \
        return op_pc;                                                                              \
    }                                                                                              \
    uint32_t ropPUSH_##seg##_32(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), \
                                UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc) \
    {                                                                                              \
        int sp_reg;                                                                                \
                                                                                                   \
        uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);                                              \
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -4);                                                      \
        uop_MOVZX(ir, IREG_temp0, IREG_##seg##_seg_W);                                             \
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_temp0);                                   \
        SUB_SP(ir, 4);                                                                             \
                                                                                                   \
        return op_pc;                                                                              \
    }

#define ROP_POP_SEG(seg, rseg)                                                                    \
    uint32_t ropPOP_##seg##_16(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), \
                               UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc) \
    {                                                                                             \
        uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);                                             \
                                                                                                  \
        if (stack32)                                                                              \
            uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_ESP);                           \
        else {                                                                                    \
            uop_MOVZX(ir, IREG_eaaddr, IREG_SP);                                                  \
            uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_eaaddr);                        \
        }                                                                                         \
        uop_LOAD_SEG(ir, &rseg, IREG_temp0_W);                                                    \
        ADD_SP(ir, 2);                                                                            \
                                                                                                  \
        return op_pc;                                                                             \
    }                                                                                             \
    uint32_t ropPOP_##seg##_32(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), \
                               UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc) \
    {                                                                                             \
        uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);                                             \
                                                                                                  \
        if (stack32)                                                                              \
            uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_ESP);                           \
        else {                                                                                    \
            uop_MOVZX(ir, IREG_eaaddr, IREG_SP);                                                  \
            uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_eaaddr);                        \
        }                                                                                         \
        uop_LOAD_SEG(ir, &rseg, IREG_temp0_W);                                                    \
        ADD_SP(ir, 4);                                                                            \
                                                                                                  \
        return op_pc;                                                                             \
    }

// clang-format off
ROP_PUSH_SEG(CS)
ROP_PUSH_SEG(DS)
ROP_PUSH_SEG(ES)
ROP_PUSH_SEG(FS)
ROP_PUSH_SEG(GS)
ROP_PUSH_SEG(SS)
ROP_POP_SEG(DS, cpu_state.seg_ds)
ROP_POP_SEG(ES, cpu_state.seg_es)
ROP_POP_SEG(FS, cpu_state.seg_fs)
ROP_POP_SEG(GS, cpu_state.seg_gs)
// clang-format on

uint32_t
ropLEAVE_16(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);

    if (stack32)
        uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_EBP);
    else {
        uop_MOVZX(ir, IREG_eaaddr, IREG_BP);
        uop_MEM_LOAD_REG(ir, IREG_temp0_W, IREG_SS_base, IREG_eaaddr);
    }
    /*The stack size picks SP or ESP, the operand size the pop*/
    if (stack32)
        uop_ADD_IMM(ir, IREG_ESP, IREG_EBP, 2);
    else
        uop_ADD_IMM(ir, IREG_SP, IREG_BP, 2);
    uop_MOV(ir, IREG_BP, IREG_temp0_W);

    return op_pc;
}
uint32_t
ropLEAVE_32(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);

    if (stack32)
        uop_MEM_LOAD_REG(ir, IREG_temp0, IREG_SS_base, IREG_EBP);
    else {
        uop_MOVZX(ir, IREG_eaaddr, IREG_BP);
        uop_MEM_LOAD_REG(ir, IREG_temp0, IREG_SS_base, IREG_eaaddr);
    }
    /*The stack size picks SP or ESP, the operand size the pop*/
    if (stack32)
        uop_ADD_IMM(ir, IREG_ESP, IREG_EBP, 4);
    else
        uop_ADD_IMM(ir, IREG_SP, IREG_BP, 4);
    uop_MOV(ir, IREG_EBP, IREG_temp0);

    return op_pc;
}

uint32_t
ropPUSHA_16(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    if (stack32) {
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -16);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 14, IREG_AX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 12, IREG_CX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 10, IREG_DX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 8, IREG_BX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 6, IREG_SP);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 4, IREG_BP);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 2, IREG_SI);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_DI);
    } else {
        /*A 16-bit stack wraps each slot's address, not just the first*/
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -2);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_AX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -4);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_CX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -6);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_DX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -8);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_BX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -10);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_SP);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -12);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_BP);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -14);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_SI);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -16);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_DI);
    }
    SUB_SP(ir, 16);
    return op_pc;
}
uint32_t
ropPUSHA_32(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    if (stack32) {
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -32);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 28, IREG_EAX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 24, IREG_ECX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 20, IREG_EDX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 16, IREG_EBX);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 12, IREG_ESP);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 8, IREG_EBP);
        uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 4, IREG_ESI);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_EDI);
    } else {
        /*A 16-bit stack wraps each slot's address, not just the first*/
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -4);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_EAX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -8);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_ECX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -12);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_EDX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -16);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_EBX);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -20);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_ESP);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -24);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_EBP);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -28);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_ESI);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, -32);
        uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_EDI);
    }
    SUB_SP(ir, 32);
    return op_pc;
}

uint32_t
ropPOPA_16(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    if (stack32) {
        sp_reg = LOAD_SP(ir);
        uop_MEM_LOAD_REG(ir, IREG_DI, IREG_SS_base, sp_reg);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_SI, IREG_SS_base, sp_reg, 2);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_BP, IREG_SS_base, sp_reg, 4);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_BX, IREG_SS_base, sp_reg, 8);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_DX, IREG_SS_base, sp_reg, 10);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_CX, IREG_SS_base, sp_reg, 12);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_AX, IREG_SS_base, sp_reg, 14);
    } else {
        /*A 16-bit stack wraps each slot's address, not just the first*/
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 0);
        uop_MEM_LOAD_REG(ir, IREG_DI, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 2);
        uop_MEM_LOAD_REG(ir, IREG_SI, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 4);
        uop_MEM_LOAD_REG(ir, IREG_BP, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 8);
        uop_MEM_LOAD_REG(ir, IREG_BX, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 10);
        uop_MEM_LOAD_REG(ir, IREG_DX, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 12);
        uop_MEM_LOAD_REG(ir, IREG_CX, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 14);
        uop_MEM_LOAD_REG(ir, IREG_AX, IREG_SS_base, sp_reg);
    }
    ADD_SP(ir, 16);
    return op_pc;
}
uint32_t
ropPOPA_32(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    if (stack32) {
        sp_reg = LOAD_SP(ir);
        uop_MEM_LOAD_REG(ir, IREG_EDI, IREG_SS_base, sp_reg);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_ESI, IREG_SS_base, sp_reg, 4);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_EBP, IREG_SS_base, sp_reg, 8);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_EBX, IREG_SS_base, sp_reg, 16);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_EDX, IREG_SS_base, sp_reg, 20);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_ECX, IREG_SS_base, sp_reg, 24);
        uop_MEM_LOAD_REG_OFFSET(ir, IREG_EAX, IREG_SS_base, sp_reg, 28);
    } else {
        /*A 16-bit stack wraps each slot's address, not just the first*/
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 0);
        uop_MEM_LOAD_REG(ir, IREG_EDI, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 4);
        uop_MEM_LOAD_REG(ir, IREG_ESI, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 8);
        uop_MEM_LOAD_REG(ir, IREG_EBP, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 16);
        uop_MEM_LOAD_REG(ir, IREG_EBX, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 20);
        uop_MEM_LOAD_REG(ir, IREG_EDX, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 24);
        uop_MEM_LOAD_REG(ir, IREG_ECX, IREG_SS_base, sp_reg);
        sp_reg = LOAD_SP_WITH_OFFSET(ir, 28);
        uop_MEM_LOAD_REG(ir, IREG_EAX, IREG_SS_base, sp_reg);
    }
    ADD_SP(ir, 32);
    return op_pc;
}

uint32_t
ropPUSHF(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    /*In V86 mode the fault depends on IOPL, which blocks aren't keyed on:
      the interpreter decides it at run time*/
    if (cpu_state.eflags & VM_FLAG)
        return 0;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    call_flags_rebuild(ir, jit_flags_rebuild);
    sp_reg = LOAD_SP_WITH_OFFSET(ir, -2);
    uop_AND_IMM(ir, IREG_flags, IREG_flags, 0x7fd5);
    uop_OR_IMM(ir, IREG_flags, IREG_flags, 0x0002);
    uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_flags);
    SUB_SP(ir, 2);

    return op_pc;
}
/*KairoX86#396: POPF and POPFD as x86_ops_flag.h's opPOPF/opPOPFD outside V86 mode. Blocks are keyed on protected
  mode but not on CPL or IOPL, so the bits the guest may not change (K: none at CPL 0 or in real mode, IOPL at a CPL
  IOPL allows, IOPL and IF above it) are worked out at run time: CPL > 0 as (CPL + 3) >> 2, CPL > IOPL as the sign of
  IOPL - CPL. With the 486 debug registers the interpreter's loop reads the rf_flag_no_clear the handler sets, so the
  handler runs there. TF turned on ends the block past POPF, as the handler's nonzero answer does.*/
extern int cpu_debug_regs_486;

static uint32_t
rop_popf_common(ir_data_t *ir, uint32_t op_pc, int size32)
{
    int sp_reg;
    int jump_uop;

    if ((cpu_state.eflags & VM_FLAG) || cpu_debug_regs_486)
        return 0;

    codegen_accumulate_flush(ir);
    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    sp_reg = LOAD_SP(ir);
    if (size32)
        uop_MEM_LOAD_REG(ir, IREG_temp2, IREG_SS_base, sp_reg);
    else
        uop_MEM_LOAD_REG(ir, IREG_temp2_W, IREG_SS_base, sp_reg);
    ADD_SP(ir, size32 ? 4 : 2);

    uop_MOVZX(ir, IREG_temp3, IREG_temp2_W);
    if (cpu_cur_status & CPU_STATUS_PMODE) {
        uop_MOVZX_REG_PTR_8(ir, IREG_temp0, &cpu_state.seg_cs.access);
        uop_SHR_IMM(ir, IREG_temp0, IREG_temp0, 5);
        uop_AND_IMM(ir, IREG_temp0, IREG_temp0, 3);
        uop_MOVZX(ir, IREG_temp1, IREG_flags);
        uop_SHR_IMM(ir, IREG_temp1, IREG_temp1, 12);
        uop_AND_IMM(ir, IREG_temp1, IREG_temp1, 3);
        uop_SUB(ir, IREG_temp1, IREG_temp1, IREG_temp0);
        uop_SHR_IMM(ir, IREG_temp1, IREG_temp1, 31); /*CPL > IOPL*/
        uop_ADD_IMM(ir, IREG_temp0, IREG_temp0, 3);
        uop_SHR_IMM(ir, IREG_temp0, IREG_temp0, 2); /*CPL > 0*/
        /*K = (CPL > 0) * 0x3000 + (CPL > IOPL) * 0x200 (CPL > IOPL only when CPL > 0)*/
        uop_SHL_IMM(ir, IREG_temp0, IREG_temp0, 12);
        uop_SHL_IMM(ir, IREG_temp1, IREG_temp1, 9);
        uop_ADD(ir, IREG_temp1, IREG_temp1, IREG_temp0);
        uop_SHL_IMM(ir, IREG_temp0, IREG_temp0, 1);
        uop_ADD(ir, IREG_temp0, IREG_temp0, IREG_temp1);
        uop_MOVZX(ir, IREG_temp1, IREG_flags);
        uop_AND(ir, IREG_temp1, IREG_temp1, IREG_temp0);
        uop_XOR_IMM(ir, IREG_temp0, IREG_temp0, 0x7fd5);
        uop_AND(ir, IREG_temp3, IREG_temp3, IREG_temp0);
        uop_OR(ir, IREG_temp1, IREG_temp1, IREG_temp3);
    } else {
        uop_AND_IMM(ir, IREG_temp1, IREG_temp3, 0x7fd5);
    }
    uop_OR_IMM(ir, IREG_temp1, IREG_temp1, 2);

    uop_MOVZX(ir, IREG_temp0, IREG_flags);
    uop_XOR_IMM(ir, IREG_temp0, IREG_temp0, 0xffff);
    uop_AND(ir, IREG_temp0, IREG_temp0, IREG_temp1);
    uop_AND_IMM(ir, IREG_temp0, IREG_temp0, T_FLAG);
    uop_MOV(ir, IREG_flags, IREG_temp1_W);
    uop_MOV_IMM(ir, IREG_flags_op, FLAGS_UNKNOWN);
    if (size32) {
        uop_AND_IMM(ir, IREG_eflags, IREG_eflags, VM_FLAG | RF_FLAG | VIF_FLAG | VIP_FLAG);
        uop_SHR_IMM(ir, IREG_temp2, IREG_temp2, 16);
        uop_AND_IMM(ir, IREG_temp2, IREG_temp2, (AC_FLAG | VID_FLAG) & cpu_eflags_implemented());
        uop_OR(ir, IREG_eflags, IREG_eflags, IREG_temp2_W);
    }
    codegen_flags_changed = 0;

    jump_uop = uop_CMP_IMM_JZ_DEST(ir, IREG_temp0, 0);
    uop_MOV_IMM(ir, IREG_pc, op_pc);
    uop_JMP(ir, codegen_exit_rout);
    uop_set_jump_dest(ir, jump_uop);

    return op_pc;
}

uint32_t
ropPOPF(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return rop_popf_common(ir, op_pc, 0);
}

uint32_t
ropPOPFD(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return rop_popf_common(ir, op_pc, 1);
}

uint32_t
ropPUSHFD(UNUSED(codeblock_t *block), ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    int sp_reg;

    /*In V86 mode the fault depends on IOPL, which blocks aren't keyed on:
      the interpreter decides it at run time*/
    if (cpu_state.eflags & VM_FLAG)
        return 0;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    call_flags_rebuild(ir, jit_flags_rebuild);

    uop_AND_IMM(ir, IREG_flags, IREG_flags, 0x7fd5);
    uop_OR_IMM(ir, IREG_flags, IREG_flags, 0x0002);
    if (cpu_CR4_mask & CR4_VME)
        uop_AND_IMM(ir, IREG_temp0_W, IREG_eflags, 0x3c);
    else if (CPUID)
        uop_AND_IMM(ir, IREG_temp0_W, IREG_eflags, 0x24);
    else
        uop_AND_IMM(ir, IREG_temp0_W, IREG_eflags, 4);
    sp_reg = LOAD_SP_WITH_OFFSET(ir, -4);
    uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, IREG_flags);
    uop_MEM_STORE_REG_OFFSET(ir, IREG_SS_base, sp_reg, 2, IREG_temp0_W);
    SUB_SP(ir, 4);

    return op_pc;
}

/*ENTER with nesting level 0, the form compilers emit. As the interpreter:
  the operand size picks the push of BP or EBP and which of them the frame
  goes to, the stack size whether SP or ESP is the frame and takes the frame
  size off. Other levels go to the interpreter.*/
static uint32_t
enter_common(codeblock_t *block, ir_data_t *ir, uint32_t op_pc, int is32)
{
    uint16_t size  = fastreadw(cs + op_pc);
    uint8_t  level = fastreadb(cs + op_pc + 2) & 0x1f;
    int      sp_reg;

    if (level)
        return 0;

    uop_MOV_IMM(ir, IREG_oldpc, cpu_state.oldpc);
    sp_reg = LOAD_SP_WITH_OFFSET(ir, is32 ? -4 : -2);
    uop_MEM_STORE_REG(ir, IREG_SS_base, sp_reg, is32 ? IREG_EBP : IREG_BP);
    SUB_SP(ir, is32 ? 4 : 2);
    if (!is32)
        uop_MOV(ir, IREG_BP, IREG_SP);
    else if (stack32)
        uop_MOV(ir, IREG_EBP, IREG_ESP);
    else
        uop_MOVZX(ir, IREG_EBP, IREG_SP);
    if (size)
        SUB_SP(ir, size);

    codegen_mark_code_present(block, cs + op_pc, 3);
    return op_pc + 3;
}
uint32_t
ropENTER_16(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return enter_common(block, ir, op_pc, 0);
}
uint32_t
ropENTER_32(codeblock_t *block, ir_data_t *ir, UNUSED(uint8_t opcode), UNUSED(uint32_t fetchdat), UNUSED(uint32_t op_32), uint32_t op_pc)
{
    return enter_common(block, ir, op_pc, 1);
}
