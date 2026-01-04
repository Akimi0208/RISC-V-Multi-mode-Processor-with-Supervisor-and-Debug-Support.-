module Execute_Cycle(
    clk, rst,
    RegWriteE, ALUSrcE, MemWriteE, ResultSrcE, BranchE, ALUControlE,
    RD1_E, RD2_E, Imm_Ext_E, RD_E, PCE, PCPlus4E,
    // new: jal, jalr, auipc from decode
    JalE, JalrE, AuipcE,

    PCSrcE, PCTargetE,
    RegWriteM, MemWriteM, ResultSrcM, RD_M, PCPlus4M, WriteDataM, ALU_ResultM,
    ResultW, ForwardA_E, ForwardB_E,
    // new: pipeline funct3
    funct3_E, funct3_M, debug_halt, InstrE
);

    // ========= Inputs =========
    input clk, rst;
    input RegWriteE, ALUSrcE, MemWriteE, BranchE;
    input [3:0] ALUControlE;
    input [31:0] RD1_E, RD2_E, Imm_Ext_E;
    input [4:0] RD_E;
    input [31:0] PCE, PCPlus4E, InstrE;
    input [31:0] ResultW;
    input [1:0] ForwardA_E, ForwardB_E,ResultSrcE;

    // new: JAL / JALR / AUIPC control
    input JalE, JalrE, AuipcE;

    // pipeline funct3 from Decode
    input [2:0] funct3_E;
	 
	 input debug_halt;


    // ========= Outputs =========
    output PCSrcE;
    output [31:0] PCTargetE;
    output RegWriteM, MemWriteM;
	 output [1:0] ResultSrcM;
    output [4:0] RD_M;
    output [31:0] PCPlus4M, WriteDataM, ALU_ResultM;
    output [2:0] funct3_M;

    // ======================================
    // Internal Wires
    // ======================================
    wire [31:0] Src_A, Src_B_interim, Src_B;
    wire [31:0] ResultE;
    wire ZeroE;

    // Comparator wires
    wire eq;
    wire lt_signed;
    wire lt_unsigned;
    reg  branch_taken;

    // PC targets
    wire [31:0] PcPlusImm;      // PCE + imm (used for branch, jal, auipc)
    wire [31:0] JalrTarget;     // (rs1 + imm) & ~1

    // Exec result (AUIPC override)
    wire [31:0] ExecResult;

    // EX/MEM pipeline registers
    reg RegWriteE_r, MemWriteE_r; 
	 reg [1:0] ResultSrcE_r;
    reg [4:0] RD_E_r;
    reg [31:0] PCPlus4E_r, RD2_E_r, ResultE_r;
    reg [2:0] funct3_E_r;

    // ======================================
    // Forwarding Mux A
    // ======================================
    Mux_3_by_1 srca_mux (
        .a(RD1_E),
        .b(ResultW),
        .c(ALU_ResultM),
        .s(ForwardA_E),
        .d(Src_A)
    );

    // ======================================
    // Forwarding Mux B
    // ======================================
    Mux_3_by_1 srcb_mux (
        .a(RD2_E),
        .b(ResultW),
        .c(ALU_ResultM),
        .s(ForwardB_E),
        .d(Src_B_interim)
    );

    // ALUSrc Mux
    Mux alu_src_mux (
        .a(Src_B_interim),
        .b(Imm_Ext_E),
        .s(ALUSrcE),
        .c(Src_B)
    );

    // ======================================
    // ALU Unit
    // ======================================
    ALU alu (
        .A(Src_A),
        .B(Src_B),
        .Result(ResultE),
        .ALUControl(ALUControlE),
        .OverFlow(),
        .Carry(),
        .Zero(ZeroE),
        .Negative()
    );

    // ======================================
    // Branch/JAL target = PC + imm
    // produce PcPlusImm (do NOT drive PCTargetE directly here)
    // ======================================
    PC_Adder branch_adder (
        .a(PCE),
        .b(Imm_Ext_E),
        .c(PcPlusImm)
    );

    // ======================================
    // JALR target = (rs1 + imm) & ~1
    // use forwarded Src_A (rs1) + imm
    // ======================================
    assign JalrTarget = (Src_A + Imm_Ext_E) & 32'hFFFFFFFE;

    // ======================================
    // Exec result: if AUIPC then use PcPlusImm else use ALU result
    // This ensures AUIPC writes rd = PC + imm
    // ======================================
    assign ExecResult = AuipcE ? PcPlusImm : ResultE;

    // ======================================
    // Comparator logic
    // ======================================
    assign eq = (Src_A == Src_B);
    assign lt_signed = ($signed(Src_A) < $signed(Src_B));
    assign lt_unsigned = ($unsigned(Src_A) < $unsigned(Src_B));

    always @(*) begin
        branch_taken = 1'b0;

        case (funct3_E)
            3'b000: branch_taken = eq;         // BEQ
            3'b001: branch_taken = ~eq;        // BNE
            3'b100: branch_taken = lt_signed;  // BLT
            3'b101: branch_taken = ~lt_signed; // BGE
            3'b110: branch_taken = lt_unsigned;// BLTU
            3'b111: branch_taken = ~lt_unsigned;// BGEU
            default: branch_taken = 1'b0;
        endcase
    end

    // ======================================
    // EX/MEM Pipeline Registers
    // ======================================
    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            RegWriteE_r <= 0;
            MemWriteE_r <= 0;
            ResultSrcE_r <= 0;
            RD_E_r <= 0;
            PCPlus4E_r <= 0;
            RD2_E_r <= 0;
            ResultE_r <= 0;
            funct3_E_r <= 0;
        end else if (!debug_halt) begin
            RegWriteE_r <= RegWriteE;
            MemWriteE_r <= MemWriteE;
            ResultSrcE_r <= ResultSrcE;
            RD_E_r <= RD_E;
            PCPlus4E_r <= PCPlus4E;
            RD2_E_r <= Src_B_interim;
            ResultE_r <= ExecResult;       // pipeline ExecResult (AUIPC override)
            funct3_E_r <= funct3_E;
        end
    end

    // ======================================
    // Final Outputs
    // ======================================

    // PCSrcE: chọn nguồn nhảy
    assign PCSrcE =
           (BranchE & branch_taken)   // Branch
        || JalE                       // JAL
        || JalrE;                     // JALR

    // PCTargetE: choose JALR target (rs1+imm & ~1) else PC+imm (for JAL/BRANCH/AUIPC use)
    assign PCTargetE = JalrE ? JalrTarget : PcPlusImm;

    assign RegWriteM = RegWriteE_r;
    assign MemWriteM = MemWriteE_r;
    assign ResultSrcM = ResultSrcE_r;
    assign RD_M = RD_E_r;
    assign PCPlus4M = PCPlus4E_r;
    assign WriteDataM = RD2_E_r;
    assign ALU_ResultM = ResultE_r;

    assign funct3_M = funct3_E_r;

endmodule
