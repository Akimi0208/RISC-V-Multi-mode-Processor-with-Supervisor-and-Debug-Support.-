module Memory_Cycle(
    input clk, rst,
    input RegWriteM, MemWriteM, 
	 input [1:0] ResultSrcM,
    input [2:0] funct3_M,
    input [4:0] RD_M,
    input [31:0] PCPlus4M, WriteDataM, ALU_ResultM, ReadDataM_in,
	 input debug_halt,


    output RegWriteW, 
	 output [1:0] ResultSrcW,
    output [4:0] RD_W,
    output [31:0] PCPlus4W, ALU_ResultW, ReadDataW,

    // xuống DataMemory
    output [31:0] A_out, WD_out,
    output [3:0] byte_enable_out,
    output WE_out
);

    //==============================
    // Pipeline registers
    //==============================
    reg RegWriteM_r; 
	 reg [1:0] ResultSrcM_r;
    reg [4:0] RD_M_r;
    reg [31:0] PCPlus4M_r, ALU_ResultM_r, ReadDataM_r;
    reg [2:0] funct3_M_r;
    reg [31:0] WriteDataM_r;

    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            RegWriteM_r   <= 1'b0;
            ResultSrcM_r  <= 2'b00;
            RD_M_r        <= 5'h00;
            PCPlus4M_r    <= 32'h0;
            ALU_ResultM_r <= 32'h0;
            ReadDataM_r   <= 32'h0;
            funct3_M_r    <= 3'b000;
            WriteDataM_r  <= 32'h0;
        end else if (!debug_halt) begin
            RegWriteM_r   <= RegWriteM;
            ResultSrcM_r  <= ResultSrcM;
            RD_M_r        <= RD_M;
            PCPlus4M_r    <= PCPlus4M;
            ALU_ResultM_r <= ALU_ResultM;
            ReadDataM_r   <= ReadDataM_in;
            funct3_M_r    <= funct3_M;
            WriteDataM_r  <= WriteDataM;
        end
    end

    //=====================================================
    // LOAD DATA DECODE (LB, LH, LW, LBU, LHU)
    //=====================================================
    reg [31:0] load_data;

    always @(*) begin
        case (funct3_M_r)
            3'b000: begin  // LB
                case (ALU_ResultM_r[1:0])
                    2'b00: load_data = {{24{ReadDataM_r[7]}},  ReadDataM_r[7:0]};
                    2'b01: load_data = {{24{ReadDataM_r[15]}}, ReadDataM_r[15:8]};
                    2'b10: load_data = {{24{ReadDataM_r[23]}}, ReadDataM_r[23:16]};
                    2'b11: load_data = {{24{ReadDataM_r[31]}}, ReadDataM_r[31:24]};
                    default: load_data = 32'h0;
                endcase
            end

            3'b001: begin // LH
                case (ALU_ResultM_r[1])
                    1'b0: load_data = {{16{ReadDataM_r[15]}}, ReadDataM_r[15:0]};
                    1'b1: load_data = {{16{ReadDataM_r[31]}}, ReadDataM_r[31:16]};
                    default: load_data = 32'h0;
                endcase
            end

            3'b010: begin // LW
                load_data = ReadDataM_r;
            end

            3'b100: begin // LBU
                case (ALU_ResultM_r[1:0])
                    2'b00: load_data = {24'h0, ReadDataM_r[7:0]};
                    2'b01: load_data = {24'h0, ReadDataM_r[15:8]};
                    2'b10: load_data = {24'h0, ReadDataM_r[23:16]};
                    2'b11: load_data = {24'h0, ReadDataM_r[31:24]};
                    default: load_data = 32'h0;
                endcase
            end

            3'b101: begin // LHU
                case (ALU_ResultM_r[1])
                    1'b0: load_data = {16'h0, ReadDataM_r[15:0]};
                    1'b1: load_data = {16'h0, ReadDataM_r[31:16]};
                    default: load_data = 32'h0;
                endcase
            end

            default: load_data = ReadDataM_r;
        endcase
    end

    assign ReadDataW = load_data;

    //=====================================================
    // STORE byte-enable generator (SB, SH, SW)
    //=====================================================
    reg [3:0] be;

    always @(*) begin
        case (funct3_M_r)
            3'b000: begin // SB
                case (ALU_ResultM_r[1:0])
                    2'b00: be = 4'b0001;
                    2'b01: be = 4'b0010;
                    2'b10: be = 4'b0100;
                    2'b11: be = 4'b1000;
                    default: be = 4'b0000;
                endcase
            end

            3'b001: begin // SH
                case (ALU_ResultM_r[1])
                    1'b0: be = 4'b0011;
                    1'b1: be = 4'b1100;
                    default: be = 4'b0000;
                endcase
            end

            3'b010: begin // SW
                be = 4'b1111;
            end

            default: be = 4'b0000;
        endcase
    end

    //==============================
    // Outputs xuống Writeback stage
    //==============================
    assign RegWriteW   = RegWriteM_r;
    assign ResultSrcW  = ResultSrcM_r;
    assign RD_W        = RD_M_r;
    assign PCPlus4W    = PCPlus4M_r;
    assign ALU_ResultW = ALU_ResultM_r;

    //==============================
    // Outputs xuống Data Memory
    //==============================
    assign A_out           = ALU_ResultM_r;
    assign WD_out          = WriteDataM_r;
    assign WE_out          = MemWriteM;
    assign byte_enable_out = be;

endmodule