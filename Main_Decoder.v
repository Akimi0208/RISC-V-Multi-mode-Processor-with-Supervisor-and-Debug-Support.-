module Main_Decoder(
    input  [6:0] Op,
    output       RegWrite,
    output [2:0] ImmSrc,
    output       ALUSrc,
    output       MemWrite,
    output [1:0] ResultSrc,
    output       Branch,
    output       Jal,
    output       Jalr,
    output       Auipc,
    output [1:0] ALUOp
);

    // RegWrite for: R-type, I-type, LOAD, LUI, AUIPC, JAL, JALR
    assign RegWrite =
        (Op == 7'b0110011 ||   // R-type
         Op == 7'b0010011 ||   // I-type arithmetic
         Op == 7'b0000011 ||   // LOAD
         Op == 7'b0110111 ||   // LUI
         Op == 7'b0010111 ||   // AUIPC
         Op == 7'b1101111 ||   // JAL
         Op == 7'b1100111)     // JALR
        ? 1 : 0;

    // ImmSrc
    assign ImmSrc =
        (Op == 7'b0100011) ? 3'b001 :  // STORE
        (Op == 7'b1100011) ? 3'b010 :  // BRANCH
        (Op == 7'b0110111) ? 3'b011 :  // LUI (U-type)
        (Op == 7'b0010111) ? 3'b011 :  // AUIPC (U-type)
        (Op == 7'b1101111) ? 3'b100 :  // JAL  (J-type)
                             3'b000;   // I-type + JALR

    // ALUSrc
    assign ALUSrc =
        (Op == 7'b0010011 ||   // I-type
         Op == 7'b0000011 ||   // LOAD
         Op == 7'b0100011 ||   // STORE
         Op == 7'b1100111)     // JALR
        ? 1 : 0;

    assign MemWrite = (Op == 7'b0100011);
    assign ResultSrc = (Op == 7'b0000011);
    assign Branch = (Op == 7'b1100011);

    // NEW signals for Execute stage
    assign Jal   = (Op == 7'b1101111);
    assign Jalr  = (Op == 7'b1100111);
    assign Auipc = (Op == 7'b0010111);

    // ALUOp
    assign ALUOp =
        (Op == 7'b0110011) ? 2'b10 : // R-type
        (Op == 7'b1100011) ? 2'b01 : // BRANCH
                             2'b00;  // default
endmodule
