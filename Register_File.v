module Register_File (
    input clk,
    input rst,

    // =====================
    // CPU PORT
    // =====================
    input        WE3,
    input [4:0]  A1, A2, A3,
    input [31:0] WD3,
    output [31:0] RD1, RD2,

    // =====================
    // DEBUG PORT
    // =====================
    input        dbg_we,
    input        dbg_re,
    input [4:0]  dbg_addr,
    input [31:0] dbg_wdata,
    output [31:0] dbg_rdata,

    input        debug_halt
);

    reg [31:0] Register [31:0];
    integer i;

    // =====================
    // WRITE LOGIC
    // =====================
    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            for (i = 0; i < 32; i = i + 1)
                Register[i] <= 32'b0;
        end
        else begin
            // CPU write (chỉ khi không halt)
            if (WE3 && !debug_halt && (A3 != 5'd0))
                Register[A3] <= WD3;

            // DEBUG write (ưu tiên)
            if (dbg_we && debug_halt && (dbg_addr != 5'd0))
                Register[dbg_addr] <= dbg_wdata;
        end
    end

    // =====================
    // CPU READ (combinational)
    // =====================
    assign RD1 = (A1 == 5'd0) ? 32'b0 : Register[A1];
    assign RD2 = (A2 == 5'd0) ? 32'b0 : Register[A2];

    // =====================
    // DEBUG READ (combinational)
    // =====================
    assign dbg_rdata =
        (dbg_re && debug_halt) ?
            ((dbg_addr == 5'd0) ? 32'b0 : Register[dbg_addr])
            : 32'b0;

endmodule
