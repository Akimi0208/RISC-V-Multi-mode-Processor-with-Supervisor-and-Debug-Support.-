module ALU_Decoder(
    input  [1:0] ALUOp,
    input  [2:0] funct3,
    input  [6:0] funct7,
    input  [6:0] op,
    output reg [3:0] ALUControl
);

    always @(*) begin
        case(ALUOp)
            // ---------------------
            // I-type arithmetic / logic / immediate
            // ---------------------
            2'b00: begin
                case(funct3)
                    3'b000: ALUControl = 4'b0000; // ADDI / LOAD / STORE
                    3'b010: ALUControl = 4'b0101; // SLTI
                    3'b011: ALUControl = 4'b0110; // SLTIU
                    3'b100: ALUControl = 4'b0100; // XORI
                    3'b110: ALUControl = 4'b0011; // ORI
                    3'b111: ALUControl = 4'b0010; // ANDI
                    3'b001: ALUControl = 4'b0111; // SLLI
                    3'b101: begin
                        if (funct7 == 7'b0100000)
                            ALUControl = 4'b1001; // SRAI
                        else
                            ALUControl = 4'b1000; // SRLI
                    end
                    default: ALUControl = 4'b0000;
                endcase
            end

            // ---------------------
            // R-type arithmetic / logic
            // ---------------------
            2'b10: begin
                case(funct3)
                    3'b000: ALUControl =
                        (funct7 == 7'b0100000) ? 4'b0001 : 4'b0000; // SUB / ADD
                    3'b010: ALUControl = 4'b0101; // SLT
                    3'b011: ALUControl = 4'b0110; // SLTU
                    3'b100: ALUControl = 4'b0100; // XOR
                    3'b110: ALUControl = 4'b0011; // OR
                    3'b111: ALUControl = 4'b0010; // AND
                    3'b001: ALUControl = 4'b0111; // SLL
                    3'b101: begin
                        if (funct7 == 7'b0100000)
                            ALUControl = 4'b1001; // SRA
                        else
                            ALUControl = 4'b1000; // SRL
                    end
                    default: ALUControl = 4'b0000;
                endcase
            end

            // ---------------------
            // Branches (ALUOp=01)
            // ---------------------
            2'b01: ALUControl = 4'b0001; // SUB for BEQ/BNE comparison

            default: ALUControl = 4'b0000;
        endcase
    end

endmodule
