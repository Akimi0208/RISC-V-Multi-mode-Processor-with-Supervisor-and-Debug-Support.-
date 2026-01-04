module Pipeline_Top(
    input  clk,
    input  rst,

    //========================
    // Debug interface
    //========================
    output        is_ebreak,
    output [31:0] pc_decode,
    input         debug_halt,

    //========================
    // IMEM
    //========================
    output [31:0] imem_addr,
    input  [31:0] imem_data,

    //========================
    // DMEM
    //========================
    output [31:0] dmem_addr,
    output [31:0] dmem_wdata,
    input  [31:0] dmem_rdata,
    output        dmem_we,
    output [3:0]  dmem_byte_en,

    //========================
    // RF debug
    //========================
    input         dbg_rf_we,
    input         dbg_rf_re,
    input  [4:0]  dbg_rf_addr,
    input  [31:0] dbg_rf_wdata,
    output [31:0] dbg_rf_rdata,

    //========================
    // Debug status
    //========================
    output        instr_retired
);

    //==================================================
    // Internal control
    //==================================================
    wire retire_en;
    assign retire_en = ~debug_halt;   // 🔥 DEBUG khóa retire

    //==================================================
    // Pipeline control wires (GIỮ NGUYÊN)
    //==================================================
    wire PCSrcE, RegWriteE, RegWriteM, RegWriteW;
    wire ALUSrcE, MemWriteE, MemWriteM;
    wire BranchE;
    wire [1:0] ResultSrcE, ResultSrcM, ResultSrcW;
    wire [3:0] ALUControlE;
    wire [31:0] PCTargetE;
    wire [4:0] RD_E, RD_M, RDW;
    wire [31:0] InstrD, InstrE;
    wire [31:0] PCD, PCPlus4D, PCE, PCPlus4E;
    wire [31:0] PCPlus4M, PCPlus4W;
    wire [31:0] ResultW;
    wire [31:0] RD1_E, RD2_E, Imm_Ext_E;
    wire [31:0] ALU_ResultM, ALU_ResultW;
    wire [31:0] WriteDataM;
    wire [31:0] ReadDataW;

    wire [4:0] RS1_E, RS2_E;
    wire [1:0] ForwardAE, ForwardBE;

    wire Jal, Jalr, Auipc;
    wire is_ebreak_d;
    wire [2:0] funct3_E, funct3_M;

    //==================================================
    // FETCH
    //==================================================
    Fetch_Cycle Fetch (
        .clk(clk),
        .rst(rst),
        .debug_halt(debug_halt),
        .PCSrcE(PCSrcE),
        .PCTargetE(PCTargetE),
        .InstrF(imem_data),
        .InstrD(InstrD),
        .PCD(PCD),
        .PCPlus4D(PCPlus4D),
        .PCF(imem_addr)
    );

    //==================================================
    // DECODE
    //==================================================
    Decode_Cycle Decode (
        .clk(clk),
        .rst(rst),
        .debug_halt(debug_halt),

        .InstrD(InstrD),
        .PCD(PCD),
        .PCPlus4D(PCPlus4D),

        .RegWriteW(RegWriteW),
        .RDW(RDW),
        .ResultW(ResultW),

        .RegWriteE(RegWriteE),
        .ALUSrcE(ALUSrcE),
        .MemWriteE(MemWriteE),
        .ResultSrcE(ResultSrcE),
        .BranchE(BranchE),
        .ALUControlE(ALUControlE),

        .RD1_E(RD1_E),
        .RD2_E(RD2_E),
        .Imm_Ext_E(Imm_Ext_E),
        .RD_E(RD_E),

        .PCE(PCE),
        .InstrE(InstrE),
        .PCPlus4E(PCPlus4E),

        .RS1_E(RS1_E),
        .RS2_E(RS2_E),

        .Jal(Jal),
        .Jalr(Jalr),
        .Auipc(Auipc),

        .funct3_E(funct3_E),

        .is_ebreak(is_ebreak_d),

        // RF debug
        .dbg_rf_we(dbg_rf_we),
        .dbg_rf_re(dbg_rf_re),
        .dbg_rf_addr(dbg_rf_addr),
        .dbg_rf_wdata(dbg_rf_wdata),
        .dbg_rf_rdata(dbg_rf_rdata)
    );

    //==================================================
    // EXECUTE
    //==================================================
    Execute_Cycle Execute (
        .clk(clk),
        .rst(rst),
        .debug_halt(debug_halt),

        .JalE(Jal),
        .JalrE(Jalr),
        .AuipcE(Auipc),

        .RegWriteE(RegWriteE),
        .ALUSrcE(ALUSrcE),
        .MemWriteE(MemWriteE),
        .ResultSrcE(ResultSrcE),
        .BranchE(BranchE),
        .ALUControlE(ALUControlE),

        .RD1_E(RD1_E),
        .RD2_E(RD2_E),
        .Imm_Ext_E(Imm_Ext_E),
        .RD_E(RD_E),

        .PCE(PCE),
        .InstrE(InstrE),
        .PCPlus4E(PCPlus4E),

        .PCSrcE(PCSrcE),
        .PCTargetE(PCTargetE),

        .RegWriteM(RegWriteM),
        .MemWriteM(MemWriteM),
        .ResultSrcM(ResultSrcM),
        .RD_M(RD_M),
        .PCPlus4M(PCPlus4M),
        .WriteDataM(WriteDataM),
        .ALU_ResultM(ALU_ResultM),

        .ResultW(ResultW),

        .ForwardA_E(ForwardAE),
        .ForwardB_E(ForwardBE),

        .funct3_E(funct3_E),
        .funct3_M(funct3_M)
    );

    //==================================================
    // MEMORY (KHÓA WE)
    //==================================================
    Memory_Cycle Memory (
        .clk(clk),
        .rst(rst),
        .debug_halt(debug_halt),

        .RegWriteM(RegWriteM & retire_en),
        .MemWriteM(MemWriteM & retire_en),
        .ResultSrcM(ResultSrcM),
        .funct3_M(funct3_M),
        .RD_M(RD_M),

        .PCPlus4M(PCPlus4M),
        .WriteDataM(WriteDataM),
        .ALU_ResultM(ALU_ResultM),
        .ReadDataM_in(dmem_rdata),

        .RegWriteW(RegWriteW),
        .ResultSrcW(ResultSrcW),
        .RD_W(RDW),

        .PCPlus4W(PCPlus4W),
        .ALU_ResultW(ALU_ResultW),
        .ReadDataW(ReadDataW),

        .A_out(dmem_addr),
        .WD_out(dmem_wdata),
        .byte_enable_out(dmem_byte_en),
        .WE_out(dmem_we)
    );

    //==================================================
    // WRITEBACK
    //==================================================
    Writeback_Cycle WriteBack (
        .clk(clk),
        .rst(rst),
        .ResultSrcW(ResultSrcW),
        .PCPlus4W(PCPlus4W),
        .ALU_ResultW(ALU_ResultW),
        .ReadDataW(ReadDataW),
        .ResultW(ResultW)
    );

    //==================================================
    // HAZARD
    //==================================================
    Hazard_unit Hazard (
        .rst(rst),
        .RegWriteM(RegWriteM),
        .RegWriteW(RegWriteW),
        .RD_M(RD_M),
        .RD_W(RDW),
        .Rs1_E(RS1_E),
        .Rs2_E(RS2_E),
        .ForwardAE(ForwardAE),
        .ForwardBE(ForwardBE)
    );

    //==================================================
    // DEBUG EXPORT
    //==================================================
    assign is_ebreak   = is_ebreak_d;
    assign pc_decode   = PCE;

    // 🔥 RETIRE CHỈ Ở WB
    assign instr_retired = RegWriteW & retire_en;

endmodule
