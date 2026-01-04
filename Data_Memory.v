module Data_Memory(
    input clk,
    input rst,
    input WE,
    input [3:0] byte_enable,    // <-- thêm byte-enable
    input [31:0] A,
    input [31:0] WD,
    output [31:0] RD
);

    reg [31:0] mem [0:1023];    // 1024 words = 4 KB

    wire [9:0] word_addr = A[31:2];  // địa chỉ theo word
    wire [1:0] byte_off  = A[1:0];   // byte offset trong word


    //====================
    // WRITE (SB/SH/SW)
    //====================
    always @(posedge clk) begin
        if (WE) begin
            if (byte_enable[0]) mem[word_addr][7:0]   <= WD[7:0];
            if (byte_enable[1]) mem[word_addr][15:8]  <= WD[15:8];
            if (byte_enable[2]) mem[word_addr][23:16] <= WD[23:16];
            if (byte_enable[3]) mem[word_addr][31:24] <= WD[31:24];
        end
    end

    //====================
    // READ (always returns 32 bits)
    //====================
    assign RD = mem[word_addr];

endmodule
