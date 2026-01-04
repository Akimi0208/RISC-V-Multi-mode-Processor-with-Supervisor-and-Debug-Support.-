module Fetch_Cycle(
    input clk, rst,
    input PCSrcE,
    input [31:0] PCTargetE,
    input [31:0] InstrF,        // <-- thêm input này, nhận từ IMEM
	 input debug_halt,
    output [31:0] InstrD,
    output [31:0] PCD, PCPlus4D,
    output [31:0] PCF           // <-- thêm output này, xuất địa chỉ cho IMEM
);

    // Declaring interim wires
    wire [31:0] PC_F, PCPlus4F;
    // wire [31:0] InstrF;  <-- bỏ dòng này vì giờ là input

    // Registers
    reg [31:0] InstrF_reg;
    reg [31:0] PCF_reg, PCPlus4F_reg;

    // PC Mux
    Mux PC_MUX (
        .a(PCPlus4F),
        .b(PCTargetE),
        .s(PCSrcE),
        .c(PC_F)
    );

    // Program Counter
    PC_Module Program_Counter (
        .clk(clk),
        .rst(rst),
        .PC(PCF),
		  .debug_halt(debug_halt),
        .PC_Next(PC_F)
    );

    // ❌ Bỏ phần Instruction_Memory IMEM (nằm ở top bây giờ)

    // PC adder
    PC_Adder PC_adder (
        .a(PCF),
        .b(32'h00000004),
        .c(PCPlus4F)
    );

    // Fetch Cycle Registers
    always @(posedge clk or negedge rst) begin
		if(!rst) begin
        InstrF_reg <= 32'h0;
        PCF_reg <= 32'h0;
        PCPlus4F_reg <= 32'h0;
		end
		else if (!debug_halt) begin
        InstrF_reg <= InstrF;
        PCF_reg <= PCF;
        PCPlus4F_reg <= PCPlus4F;
		end
    // else: giữ nguyên (freeze)
	end


    assign InstrD = (rst == 1'b0) ? 32'h00000000 : InstrF_reg;
    assign PCD = (rst == 1'b0) ? 32'h00000000 : PCF_reg;
    assign PCPlus4D = (rst == 1'b0) ? 32'h00000000 : PCPlus4F_reg;
    assign PCF_out = PCF;  // <-- cho phép top.v truy cập địa chỉ PC hiện tại

endmodule
