uint32_t ropREP_MOVSB(codeblock_t *block, ir_data_t *ir, uint8_t opcode, uint32_t fetchdat, uint32_t op_32, uint32_t op_pc);
uint32_t ropREP_MOVSW(codeblock_t *block, ir_data_t *ir, uint8_t opcode, uint32_t fetchdat, uint32_t op_32, uint32_t op_pc);
uint32_t ropREP_MOVSL(codeblock_t *block, ir_data_t *ir, uint8_t opcode, uint32_t fetchdat, uint32_t op_32, uint32_t op_pc);
uint32_t ropREP_STOSB(codeblock_t *block, ir_data_t *ir, uint8_t opcode, uint32_t fetchdat, uint32_t op_32, uint32_t op_pc);
uint32_t ropREP_STOSW(codeblock_t *block, ir_data_t *ir, uint8_t opcode, uint32_t fetchdat, uint32_t op_32, uint32_t op_pc);
uint32_t ropREP_STOSL(codeblock_t *block, ir_data_t *ir, uint8_t opcode, uint32_t fetchdat, uint32_t op_32, uint32_t op_pc);

/*The elements of REP MOVS/STOS the compiled routines do not copy directly (KairoX86#441: as many as the loop body
  takes, the guest registers and cycle count kept current), indexed by [STOS][log2 element size][32-bit addressing]*/
extern int (*const codegen_rep_elem[2][3][2])(x86seg *seg, int cycles_end, int elem_cycles);
