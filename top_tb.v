`timescale 1ns/1ps

`define CMD_RF_READ     4'd0
`define CMD_RF_WRITE    4'd1
`define CMD_DMEM_READ   4'd2
`define CMD_DMEM_WRITE  4'd3
`define CMD_DPC_READ    4'd4
`define CMD_STEP        4'd5
`define CMD_RESUME      4'd15

module tb_top;

    reg clk;
    reg rst;

    //======================
    // Debug wires
    //======================
    wire debug_halt;
    reg  debug_resume;
	 reg debug_step;

    wire        dbg_rf_we;
    wire        dbg_rf_re;
    wire [4:0]  dbg_rf_addr;
    wire [31:0] dbg_rf_wdata;
    wire [31:0] dbg_rf_rdata;

    wire        dbg_dmem_we;
    wire [31:0] dbg_dmem_addr;
    wire [31:0] dbg_dmem_wdata;
    wire [3:0]  dbg_dmem_be;
    wire [31:0] dbg_dmem_rdata;

    wire [31:0] dpc;
    wire [31:0] dcsr;
    wire [31:0] dscratch0;
    wire [31:0] dscratch1;

    //======================
    // Instruction monitoring
    //======================
    reg [31:0] prev_pc;
    reg prev_debug_halt;
    
    //======================
    // DUT
    //======================
    top dut (
        .clk(clk),
        .rst(rst),
        .debug_resume(debug_resume),
		  .debug_step(debug_step)
    );

    //======================
    // Clock
    //======================
    initial clk = 0;
    always #5 clk = ~clk;

    //======================
    // SCRIPT STORAGE
    //======================
    reg [63:0] script [0:255];
    integer script_length;
    integer pc;

    //======================
    // RESET
    //======================
    initial begin
        rst = 0;
        debug_resume = 0;
		  debug_step   = 0;   // <<< ADD
        prev_debug_halt = 0;
        prev_pc = 32'hFFFFFFFF;
        script_length = 0;
        #20 rst = 1;
        $display("=== CPU RUNNING IN NORMAL MODE ===\n");
    end

    //======================
    // MONITOR PC & INSTRUCTION (Normal Mode)
    //======================
    always @(posedge clk) begin
        if (rst && !dut.debug_halt) begin
            if (dut.cpu.imem_addr !== prev_pc) begin
                $display("[TIME=%0t] Normal Mode: PC=0x%h, INSTR=0x%h", 
                         $time, dut.cpu.Execute.PCE, dut.cpu.Execute.InstrE);
                prev_pc = dut.cpu.imem_addr;
            end
        end
        
        prev_debug_halt = dut.debug_halt;
    end

    //======================
    // LOAD & EXECUTE SCRIPT (chỉ khi vào debug mode)
    //======================
    initial begin
        // Đợi CPU chạy bình thường
        wait (dut.debug_halt);
        
        $display("\n=== ENTER DEBUG MODE ===");
        $display("=== LOADING DEBUG SCRIPT ===\n");
        
        // Bây giờ mới load script
        load_script();
        
        $display("=== EXECUTING DEBUG COMMANDS ===\n");
        
        // Thực thi script
        begin : script_loop
            for (pc = 0; pc < script_length; pc = pc + 1) begin
                exec_cmd(script[pc]);

                if (script[pc][63:60] == `CMD_RESUME)
                    disable script_loop;

                #20;
            end
        end

        $display("\n=== SCRIPT DONE ===\n");
        
        #1000;
        $finish;
    end

    //======================
    // TASK: LOAD SCRIPT FROM FILE
    //======================
    task load_script;
        integer file, status;
        reg [8*20:1] cmd_str;
        integer addr, data;
        begin
            script_length = 0;
            file = $fopen("D:/DOAN1/RISCVD/DebugScript.txt", "r");
            
            if (file == 0) begin
                $display("ERROR: Cannot open D:/DOAN1/RISCVD/DebugScript.txt");
                $finish;
            end
            
            while (!$feof(file) && script_length < 256) begin
                status = $fscanf(file, "%s", cmd_str);
                
                if (status == 1) begin
                    if (cmd_str == "RF_READ") begin
                        status = $fscanf(file, "%d", addr);
                        if (status == 1) begin
                            script[script_length] = {`CMD_RF_READ, 23'd0, addr[4:0], 32'd0};
                            $display("  [%0d] RF_READ x%0d", script_length, addr);
                            script_length = script_length + 1;
                        end
                    end
                    else if (cmd_str == "RF_WRITE") begin
                        status = $fscanf(file, "%d %d", addr, data);
                        if (status == 2) begin
                            script[script_length] = {`CMD_RF_WRITE, 23'd0, addr[4:0], data[31:0]};
                            $display("  [%0d] RF_WRITE x%0d = 0x%h", script_length, addr, data);
                            script_length = script_length + 1;
                        end
                    end
                    else if (cmd_str == "DMEM_READ") begin
                        status = $fscanf(file, "%h", addr);
                        if (status == 1) begin
                            script[script_length] = {`CMD_DMEM_READ, addr[27:0], 32'd0};
                            $display("  [%0d] DMEM_READ 0x%h", script_length, addr);
                            script_length = script_length + 1;
                        end
                    end
                    else if (cmd_str == "DMEM_WRITE") begin
                        status = $fscanf(file, "%h %h", addr, data);
                        if (status == 2) begin
                            script[script_length] = {`CMD_DMEM_WRITE, addr[27:0], data[31:0]};
                            $display("  [%0d] DMEM_WRITE 0x%h = 0x%h", script_length, addr, data);
                            script_length = script_length + 1;
                        end
                    end
                    else if (cmd_str == "DPC_READ") begin
                        script[script_length] = {`CMD_DPC_READ, 28'd0, 32'd0};
                        $display("  [%0d] DPC_READ", script_length);
                        script_length = script_length + 1;
                    end
						  else if (cmd_str == "STEP") begin
								script[script_length] = {`CMD_STEP, 28'd0, 32'd0};
								$display("  [%0d] STEP", script_length);
								script_length = script_length + 1;
						  end
                    else if (cmd_str == "RESUME") begin
                        script[script_length] = {`CMD_RESUME, 28'd0, 32'd0};
                        $display("  [%0d] RESUME", script_length);
                        script_length = script_length + 1;
                    end
                    else begin
                        $display("WARNING: Unknown command '%s'", cmd_str);
                    end
                end
            end
            
            $fclose(file);
            $display("\nLoaded %0d commands from script file\n", script_length);
        end
    endtask

    //======================
    // COMMAND EXECUTOR
    //======================
    task exec_cmd;
        input [63:0] cmd;
        reg [3:0] op;
        reg [27:0] addr;
        reg [31:0] data;
        begin
            op   = cmd[63:60];
            addr = cmd[59:32];
            data = cmd[31:0];

            case (op)
                `CMD_RF_READ: begin
                    force dut.dbg_rf_addr = addr[4:0];
                    force dut.dbg_rf_re   = 1'b1;
                    @(posedge clk);
                    #1;
                    $display("[DEBUG] RF[x%0d] = 0x%h", addr[4:0], dut.dbg_rf_rdata);
                    release dut.dbg_rf_re;
                    release dut.dbg_rf_addr;
                end

                `CMD_RF_WRITE: begin
                    force dut.dbg_rf_addr  = addr[4:0];
                    force dut.dbg_rf_wdata = data;
                    force dut.dbg_rf_we    = 1'b1;
                    @(posedge clk);
                    $display("[DEBUG] RF[x%0d] <= 0x%h", addr[4:0], data);
                    release dut.dbg_rf_we;
                    release dut.dbg_rf_wdata;
                    release dut.dbg_rf_addr;
                end

                `CMD_DMEM_READ: begin
                    force dut.dbg_dmem_addr = addr;
                    force dut.dbg_dmem_we   = 1'b0;
                    @(posedge clk);
                    #1;
                    $display("[DEBUG] MEM[0x%h] = 0x%h", addr, dut.dbg_dmem_rdata);
                    release dut.dbg_dmem_addr;
                    release dut.dbg_dmem_we;
                end

                `CMD_DMEM_WRITE: begin
                    force dut.dbg_dmem_addr  = addr;
                    force dut.dbg_dmem_wdata = data;
                    force dut.dbg_dmem_be    = 4'b1111;
                    force dut.dbg_dmem_we    = 1'b1;
                    @(posedge clk);
                    $display("[DEBUG] MEM[0x%h] <= 0x%h", addr, data);
                    release dut.dbg_dmem_we;
                    @(posedge clk);
                    release dut.dbg_dmem_wdata;
                    release dut.dbg_dmem_be;
                    release dut.dbg_dmem_addr;
                end

                `CMD_DPC_READ: begin
                    $display("[DEBUG] DPC = 0x%h", dut.dpc);
                end
					 `CMD_STEP: begin
							$display("[DEBUG] STEP 1 instruction");
							debug_step = 1'b1;
							@(posedge clk);
							debug_step = 1'b0;

							// đợi CPU chạy xong 1 instruction và quay lại halt
							wait (dut.debug_halt);
					 end

                `CMD_RESUME: begin
                    debug_resume = 1'b1;
                    @(posedge clk);
                    debug_resume = 1'b0;
                    $display("\n=== RESUME TO NORMAL MODE ===\n");
                end
            endcase
        end
    endtask

endmodule