module ALU(
    input  [31:0] A,
    input  [31:0] B,
    input  [3:0]  ALUControl,

    output reg [31:0] Result,
    output Zero,
    output Negative,
    output Carry,
    output OverFlow
);

    // -----------------------------
    // Internal wires
    // -----------------------------

    wire [31:0] Sum;
    wire Cout;

    // Adder/Subtractor (dùng chung cho ADD, SUB, SLT, SLTU)
    // ALUControl[0] = 0 → ADD
    // ALUControl[0] = 1 → SUB (B đảo + 1)
    assign {Cout, Sum} = A + (ALUControl[0] ? (~B + 32'd1) : B);

    // -----------------------------
    // Flags
    // -----------------------------

    // Overflow: chỉ ADD/SUB
    assign OverFlow =
        ((Sum[31] ^ A[31]) &
        (~(ALUControl[0] ^ B[31] ^ A[31])) &
        (~ALUControl[1]));

    // Carry: chỉ ADD/SUB
    assign Carry = ((~ALUControl[1]) & Cout);

    assign Zero = &(~Result);
    assign Negative = Result[31];


    // -----------------------------
    // ALU Operation Decode
    // -----------------------------
    // ALUControl mapping bạn đang dùng:
    // 0000 ADD
    // 0001 SUB
    // 0010 AND
    // 0011 OR
    // 0100 XOR
    // 0101 SLT
    // 0110 SLTU
    // 0111 SLL
    // 1000 SRL
    // 1001 SRA

    always @(*) begin
        case (ALUControl)

            4'b0000: Result = Sum;                     // ADD
            4'b0001: Result = Sum;                     // SUB
            4'b0010: Result = A & B;                   // AND
            4'b0011: Result = A | B;                   // OR
            4'b0100: Result = A ^ B;                   // XOR
            4'b0101: Result = (A < B) ? 32'd1 : 32'd0; // SLT (signed)
            4'b0110: Result = ($unsigned(A) < $unsigned(B)) ? 32'd1 : 32'd0; // SLTU
            4'b0111: Result = A << B[4:0];             // SLL
            4'b1000: Result = A >> B[4:0];             // SRL
            4'b1001: Result = $signed(A) >>> B[4:0];   // SRA

            default: Result = 32'd0;
        endcase
    end

endmodule
