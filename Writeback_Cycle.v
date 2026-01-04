module Writeback_Cycle(
    input clk, rst,
    input [1:0] ResultSrcW,         // đổi 1-bit → 2-bit
    input [31:0] PCPlus4W, ALU_ResultW, ReadDataW,
    output reg [31:0] ResultW
);

    always @(*) begin
        case (ResultSrcW)
            2'b00: ResultW = ALU_ResultW;   // ALU
            2'b01: ResultW = ReadDataW;     // LOAD
            2'b10: ResultW = PCPlus4W;      // JAL / JALR
            default: ResultW = ALU_ResultW;
        endcase
    end
endmodule
