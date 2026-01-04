module Decode_Cycle(
    clk, rst,
    InstrD, PCD, PCPlus4D,
    RegWriteW, RDW, ResultW,

    // Outputs to Execute stage
    RegWriteE, ALUSrcE, MemWriteE, ResultSrcE, BranchE,
    ALUControlE,
    RD1_E, RD2_E, Imm_Ext_E,
    RD_E, RS1_E, RS2_E,
    PCE, PCPlus4E, Jal, Jalr, Auipc,

    // Debug / misc
    funct3_E,
    is_ebreak,
    debug_halt,
	 dbg_rf_we,
	 dbg_rf_re,
    dbg_rf_addr,
    dbg_rf_wdata,
	 dbg_rf_rdata,
	 InstrE
);

    //========================
    // Inputs
    //========================
    input clk, rst;
    input RegWriteW;
    input [4:0]  RDW;
    input [31:0] InstrD, PCD, PCPlus4D, ResultW;
    input debug_halt;
	 input        dbg_rf_we;
	 input        dbg_rf_re;
    input [4:0]  dbg_rf_addr;
    input [31:0] dbg_rf_wdata;
	 

    //========================
    // Outputs
    //========================
    output RegWriteE, ALUSrcE, MemWriteE, BranchE;
    output [1:0] ResultSrcE;
    output [3:0] ALUControlE;
    output [31:0] RD1_E, RD2_E, Imm_Ext_E;
    output [4:0] RS1_E, RS2_E, RD_E;
    output [31:0] PCE, PCPlus4E, InstrE;
    output [2:0] funct3_E;
    output Jal, Jalr, Auipc;
    output is_ebreak;
	 output [31:0] dbg_rf_rdata;
	

    //========================
    // Internal wires
    //========================
    wire RegWriteD, ALUSrcD, MemWriteD, BranchD;
    wire [1:0] ResultSrcD;
    wire [2:0] ImmSrcD;
    wire [3:0] ALUControlD;
    wire [31:0] RD1_D, RD2_D, Imm_Ext_D;

    wire is_ebreak_d;
    wire rf_we_cpu;

    //========================
    // Pipeline registers
    //========================
    reg RegWriteD_r, ALUSrcD_r, MemWriteD_r, BranchD_r;
    reg [1:0] ResultSrcD_r;
    reg [3:0] ALUControlD_r;
    reg [31:0] RD1_D_r, RD2_D_r, Imm_Ext_D_r;
    reg [4:0] RD_D_r, RS1_D_r, RS2_D_r;
    reg [31:0] PCD_r, PCPlus4D_r, InstrD_r;
    reg [2:0] funct3_D_r;
    reg is_ebreak_r;

    //========================
    // Control Unit
    //========================
    Control_Unit_Top control (
        .Op(InstrD[6:0]),
        .RegWrite(RegWriteD),
        .ImmSrc(ImmSrcD),
        .ALUSrc(ALUSrcD),
        .MemWrite(MemWriteD),
        .ResultSrc(ResultSrcD),
        .Branch(BranchD),
        .funct3(InstrD[14:12]),
        .funct7(InstrD[31:25]),
        .Jal(Jal),
        .Jalr(Jalr),
        .Auipc(Auipc),
        .ALUControl(ALUControlD)
    );

    //========================
    // Register File
    //========================
    assign rf_we_cpu = RegWriteW & ~debug_halt;

    Register_File rf (
        .clk(clk),
        .rst(rst),
        .WE3(rf_we_cpu),      // ❗ chặn ghi RF khi debug
        .WD3(ResultW),
        .A1(InstrD[19:15]),
        .A2(InstrD[24:20]),
        .A3(RDW),
        .RD1(RD1_D),
        .RD2(RD2_D),
		  .dbg_we(dbg_rf_we),        // từ testbench
		  .dbg_re(dbg_rf_re), 
		  .dbg_addr(dbg_rf_addr),
        .dbg_wdata(dbg_rf_wdata),
		  .dbg_rdata(dbg_rf_rdata),
        .debug_halt(debug_halt)
    );

    //========================
    // Sign Extend
    //========================
    Sign_Extend extension (
        .In(InstrD),
        .Imm_Ext(Imm_Ext_D),
        .ImmSrc(ImmSrcD)
    );

    //========================
    // EBREAK detect (Decode)
    //========================
    assign is_ebreak_d = (InstrD == 32'h00100073);

    //========================
    // Pipeline registers (ID → EX)
    //========================
    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            RegWriteD_r   <= 0;
            ALUSrcD_r     <= 0;
            MemWriteD_r   <= 0;
            ResultSrcD_r  <= 0;
            BranchD_r     <= 0;
            ALUControlD_r <= 0;

            RD1_D_r       <= 0;
            RD2_D_r       <= 0;
            Imm_Ext_D_r   <= 0;

            RD_D_r        <= 0;
            RS1_D_r       <= 0;
            RS2_D_r       <= 0;

            PCD_r         <= 0;
            PCPlus4D_r    <= 0;
            funct3_D_r    <= 0;
            is_ebreak_r   <= 0;
        end
        else if (!debug_halt) begin
            RegWriteD_r   <= RegWriteD & ~is_ebreak_d; // an toàn
            ALUSrcD_r     <= ALUSrcD;
            MemWriteD_r   <= MemWriteD & ~is_ebreak_d; // an toàn
            ResultSrcD_r  <= ResultSrcD;
            BranchD_r     <= BranchD;
            ALUControlD_r <= ALUControlD;

            RD1_D_r       <= RD1_D;
            RD2_D_r       <= RD2_D;
            Imm_Ext_D_r   <= Imm_Ext_D;

            RD_D_r        <= InstrD[11:7];
            RS1_D_r       <= InstrD[19:15];
            RS2_D_r       <= InstrD[24:20];

            PCD_r         <= PCD;
				InstrD_r      <= InstrD;
            PCPlus4D_r    <= PCPlus4D;

            funct3_D_r    <= InstrD[14:12];
            is_ebreak_r   <= is_ebreak_d;  // ✅ pipeline hóa
        end
    end

    //========================
    // Outputs to Execute
    //========================
    assign RegWriteE   = RegWriteD_r;
    assign ALUSrcE     = ALUSrcD_r;
    assign MemWriteE   = MemWriteD_r;
    assign ResultSrcE  = ResultSrcD_r;
    assign BranchE     = BranchD_r;

    assign ALUControlE = ALUControlD_r;
    assign RD1_E       = RD1_D_r;
    assign RD2_E       = RD2_D_r;
    assign Imm_Ext_E   = Imm_Ext_D_r;

    assign RD_E        = RD_D_r;
    assign RS1_E       = RS1_D_r;
    assign RS2_E       = RS2_D_r;

    assign PCE         = PCD_r;
	 assign InstrE      = InstrD_r;
    assign PCPlus4E    = PCPlus4D_r;

    assign funct3_E    = funct3_D_r;
    assign is_ebreak   = is_ebreak_r;

endmodule
