module top(
    input clk,
    input rst,
    input debug_resume,   // ← BẮT BUỘC
	 input debug_step
);

    //===============================
    // Instruction memory wires
    //===============================
    wire [31:0] imem_addr, imem_data;

    //===============================
    // Data memory wires
    //===============================
    wire [31:0] dmem_addr;
    wire [31:0] dmem_wdata;
    wire [31:0] dmem_rdata;
    wire        dmem_we_cpu;
    wire [3:0]  dmem_be;

    // Debug DMEM
    wire        dbg_dmem_we;
    wire [31:0] dbg_dmem_addr;
    wire [31:0] dbg_dmem_wdata;
    wire [3:0]  dbg_dmem_be;
    wire [31:0] dbg_dmem_rdata;

    // MUXed DMEM
    wire        dmem_we_sel;
    wire [31:0] dmem_addr_sel;
    wire [31:0] dmem_wdata_sel;
    wire [3:0]  dmem_be_sel;

    //===============================
    // Debug wires
    //===============================
    wire        is_ebreak;
    wire        debug_halt;
    wire [31:0] dpc, dcsr;
    wire [31:0] pc_decode;

    // Debug → RF
    wire        dbg_rf_we;
    wire        dbg_rf_re;
    wire [4:0]  dbg_rf_addr;
    wire [31:0] dbg_rf_wdata;
    wire [31:0] dbg_rf_rdata;
	 wire instr_retired;

    //===============================
    // Pipeline CPU
    //===============================
    Pipeline_Top cpu (
        .clk(clk),
        .rst(rst),
        .imem_addr(imem_addr),
        .imem_data(imem_data),

        .dmem_addr(dmem_addr),
        .dmem_wdata(dmem_wdata),
        .dmem_rdata(dmem_rdata),
        .dmem_we(dmem_we_cpu),
        .dmem_byte_en(dmem_be),

        .is_ebreak(is_ebreak),
        .pc_decode(pc_decode),
        .debug_halt(debug_halt),

        .dbg_rf_we(dbg_rf_we),
        .dbg_rf_re(dbg_rf_re),
        .dbg_rf_addr(dbg_rf_addr),
        .dbg_rf_wdata(dbg_rf_wdata),
        .dbg_rf_rdata(dbg_rf_rdata),
		  .instr_retired(instr_retired)
    );

    //===============================
    // Debug Module
    //===============================
    Debug_Module dbg (
        .clk(clk),
        .rst(rst),
        .is_ebreak(is_ebreak),
        .pc_decode(pc_decode),
        .debug_resume(debug_resume),
		  .debug_step(debug_step),
        .debug_halt(debug_halt),
		  .instr_retired(instr_retired),

        .dbg_we(dbg_rf_we),
        .dbg_re(dbg_rf_re),
        .dbg_addr(dbg_rf_addr),
        .dbg_wdata(dbg_rf_wdata),
        .dbg_rdata(dbg_rf_rdata),

        .dbg_dmem_addr (dbg_dmem_addr),
        .dbg_dmem_we   (dbg_dmem_we),
        .dbg_dmem_wdata(dbg_dmem_wdata),
        .dbg_dmem_be   (dbg_dmem_be),
        .dbg_dmem_rdata(dbg_dmem_rdata),

        .dpc(dpc),
        .dcsr(dcsr)
    );


    //===============================
    // Instruction Memory
    //===============================
    Instruction_Memory imem (
        .rst(rst),
        .A(imem_addr),
        .RD(imem_data)
    );

    //===============================
    // Data Memory
    //===============================
    Data_Memory dmem (
		.clk(clk),
		.rst(rst),
		.WE(dmem_we_sel),
		.byte_enable(dmem_be_sel),
		.WD(dmem_wdata_sel),
		.A(dmem_addr_sel),
		.RD(dmem_rdata)
	 );

	 
	 //===============================
    // DMEM MUX (CPU vs DEBUG)
    //===============================
    assign dmem_we_sel    = debug_halt ? dbg_dmem_we    : dmem_we_cpu;
    assign dmem_addr_sel  = debug_halt ? dbg_dmem_addr  : dmem_addr;
    assign dmem_wdata_sel = debug_halt ? dbg_dmem_wdata : dmem_wdata;
    assign dmem_be_sel    = debug_halt ? dbg_dmem_be    : dmem_be;
    assign dbg_dmem_rdata = dmem_rdata;

endmodule
