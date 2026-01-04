// tb_debug_example.sv (snippet)
// This snippet assumes you have an instantiated top-level 'top' named tb.cpu, and
// that you instantiated Debug_Module and connected signals accordingly.

module tb_debug_example();
    reg clk = 0;
    reg rst = 1;

    // toggle clock
    always #5 clk = ~clk;

    // Instantiate top (your CPU) and Debug_Module / connect wires accordingly
    // For simplicity assume pipeline_top exposes halt_request -> debug_halt_sig
    // and we instantiated Debug_Module as 'dm' and connected signals between dm and regfile/testbench.

    // ... instantiate your CPU 'cpu' and regfile wiring ...

    // For illustration we'll drive Debug_Module's command inputs directly
    reg cmd_valid;
    reg [2:0] cmd_type;
    reg [4:0] cmd_reg;
    reg [31:0] cmd_val;
    reg [11:0] cmd_csr;

    // Hook to debug module outputs
    wire cpu_halted;
    wire cmd_ack;
    wire debug_reg_read;
    wire debug_reg_write;
    wire [4:0] debug_reg_addr;
    wire [31:0] debug_reg_wdata;

    // dummy regfile storage (simple array)
    reg [31:0] regfile [0:31];

    // CSR mock
    reg [31:0] csrfile [0:4095];

    // Provide debug_reg_rdata / csr_rdata back to Debug_Module
    wire [31:0] debug_reg_rdata = regfile[debug_reg_addr];
    wire [31:0] csr_rdata = csrfile[dm.csr_addr];

    // Instantiate Debug_Module (connected to clocks and to our regfile)
    Debug_Module dm (
        .clk(clk),
        .rst(rst),
        .halt_request(/*wired from cpu when ebreak seen*/),
        .pc_value(/*wired from cpu.PC*/),

        .debug_reg_read(dm.debug_reg_read),
        .debug_reg_write(dm.debug_reg_write),
        .debug_reg_addr(dm.debug_reg_addr),
        .debug_reg_wdata(dm.debug_reg_wdata),
        .debug_reg_rdata(debug_reg_rdata),

        .csr_read(dm.csr_read),
        .csr_addr(dm.csr_addr),
        .csr_rdata(csr_rdata),

        .cmd_valid(cmd_valid),
        .cmd_type(cmd_type),
        .cmd_reg(cmd_reg),
        .cmd_val(cmd_val),
        .cmd_csr(cmd_csr),

        .cmd_ack(cmd_ack),
        .cpu_halted(cpu_halted),
        .resume_req(/*connect to CPU resume input*/)
    );

    // helper: send structured command
    task automatic send_cmd(input [2:0] t, input [4:0] r, input [31:0] v, input [11:0] c);
    begin
        @(posedge clk);
        cmd_type <= t;
        cmd_reg  <= r;
        cmd_val  <= v;
        cmd_csr  <= c;
        cmd_valid <= 1;
        @(posedge clk);
        cmd_valid <= 0;
        // wait for ack
        wait (dm.cmd_ack == 1);
        @(posedge clk);
    end
    endtask

    // small string->command mapper
    task automatic send_cmd_from_string(string s);
        int idx;
        string token;
        int val;
        // very small parser for your example strings only
        if (s.substr(0,4) == "reg ") begin
            // format "reg xN"
            token = s.substr(4);
            if (token.substr(0,1) == "x") begin
                idx = $atoi(token.substr(1)); // SV function
                send_cmd(3'b000, idx, 32'd0, 12'd0); // READ_REG
            end
        end else if (s.find("=") != -1) begin
            // "x5=12"
            string left = s.substr(0, s.find("=")-1);
            string right = s.substr(s.find("=")+1);
            if (left.substr(0,1) == "x") begin
                idx = $atoi(left.substr(1));
                val = $atoi(right);
                send_cmd(3'b001, idx, val, 12'd0); // WRITE_REG
            end
        end else if (s == "csr") begin
            send_cmd(3'b010, 5'd0, 32'd0, 12'h7b0); // example print CSR at 0x7b0
        end else if (s == "pc") begin
            send_cmd(3'b011, 5'd0, 32'd0, 12'd0);
        end else if (s == "continue") begin
            send_cmd(3'b100, 5'd0, 32'd0, 12'd0);
        end else begin
            $display("Unknown script token: %s", s);
        end
    endtask

    initial begin
        // reset
        rst = 1;
        cmd_valid = 0;
        #20;
        rst = 0;

        // Wait until CPU halts on EBREAK (you should wire halt_request from CPU to dm.halt_request)
        wait (cpu_halted == 1);

        // Example script
        send_cmd_from_string("reg x3");
        send_cmd_from_string("reg x4");
        send_cmd_from_string("x5=12");
        send_cmd_from_string("csr");
        send_cmd_from_string("pc");
        send_cmd_from_string("continue");

        #1000;
        $finish;
    end

    // provide a simple regfile model: on debug write pulses, perform write
    always @(posedge clk) begin
        if (dm.debug_reg_write) begin
            regfile[dm.debug_reg_addr] <= dm.debug_reg_wdata;
        end
    end

endmodule
