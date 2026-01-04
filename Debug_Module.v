module Debug_Module (
    input clk,
    input rst,

    //========================
    // From Decode / Pipeline
    //========================
    input        is_ebreak,
    input [31:0] pc_decode,
    input        instr_retired,   // <-- NEW

    //========================
    // From testbench
    //========================
    input        debug_resume,
    input        debug_step,       // <-- NEW

    // RF debug access (from TB)
    input        dbg_we,
    input        dbg_re,
    input [4:0]  dbg_addr,
    input [31:0] dbg_wdata,
    input [31:0] dbg_rdata,

    // DMEM debug access (from TB)
    output reg [31:0] dbg_dmem_addr,
    output reg        dbg_dmem_we,
    output reg [31:0] dbg_dmem_wdata,
    output reg [3:0]  dbg_dmem_be,
    input      [31:0] dbg_dmem_rdata,

    //========================
    // Outputs
    //========================
    output        debug_halt,
    output [31:0] dpc,
    output [31:0] dcsr,
    output [31:0] dscratch0,
    output [31:0] dscratch1
);

    //========================
    // Debug states
    //========================
    localparam RUN   = 1'b0;
    localparam DEBUG = 1'b1;

    reg dbg_state;
    reg step_pending;

    //========================
    // Debug CSRs
    //========================
    reg [31:0] dpc_r;
    reg [31:0] dcsr_r;
    reg [31:0] dscratch0_r;
    reg [31:0] dscratch1_r;

    //========================
    // Debug FSM + STEP
    //========================
    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            dbg_state    <= RUN;
            step_pending <= 1'b0;
        end else begin
            // mặc định giữ nguyên
            dbg_state    <= dbg_state;
            step_pending <= step_pending;

            // RUN → DEBUG khi gặp ebreak
            if (dbg_state == RUN && is_ebreak) begin
                dbg_state <= DEBUG;
            end

            // DEBUG handling
            else if (dbg_state == DEBUG) begin
                if (debug_resume) begin
                    dbg_state    <= RUN;
                    step_pending <= 1'b0;
                end
                else if (debug_step) begin
                    step_pending <= 1'b1; // cho chạy đúng 1 instruction
                end
            end

            // STEP hoàn tất → quay lại DEBUG
            if (step_pending && instr_retired) begin
                step_pending <= 1'b0;
            end
        end
    end

    //========================
    // dpc
    //========================
    always @(posedge clk or negedge rst) begin
        if (!rst)
            dpc_r <= 32'b0;
        else if (is_ebreak)
            dpc_r <= pc_decode;
        else if (step_pending && instr_retired)
            dpc_r <= pc_decode;
    end

    //========================
    // dcsr
    //========================
    always @(posedge clk or negedge rst) begin
        if (!rst)
            dcsr_r <= 32'b0;
        else if (is_ebreak)
            dcsr_r <= 32'h0000_0001; // bit0 = debug mode
        else if (dbg_state == RUN)
            dcsr_r[0] <= 1'b0;
    end

    //========================
    // dscratch0 / dscratch1
    //========================
    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            dscratch0_r <= 32'b0;
            dscratch1_r <= 32'b0;
        end
        else if (dbg_state == DEBUG && dbg_we) begin
            dscratch0_r <= dbg_wdata;
            dscratch1_r <= dbg_wdata;
        end
    end

    //========================
    // DMEM default (idle)
    //========================
    always @(*) begin
        dbg_dmem_we    = 1'b0;
        dbg_dmem_addr  = 32'b0;
        dbg_dmem_wdata = 32'b0;
        dbg_dmem_be    = 4'b0000;
    end

    //========================
    // Outputs
    //========================
    assign debug_halt = (dbg_state == DEBUG) && !step_pending;
    assign dpc        = dpc_r;
    assign dcsr       = dcsr_r;
    assign dscratch0  = dscratch0_r;
    assign dscratch1  = dscratch1_r;

endmodule
