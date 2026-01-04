module RISCVD(
    input clk,
    input rst
);

    wire [31:0] imem_addr, imem_data;
    wire [31:0] dmem_addr, dmem_wdata, dmem_rdata;
    wire dmem_we;

    // Kết nối processor
    Pipeline_Top cpu (
        .clk(clk),
        .rst(rst),
        .imem_addr(imem_addr),
        .imem_data(imem_data),
        .dmem_addr(dmem_addr),
        .dmem_wdata(dmem_wdata),
        .dmem_rdata(dmem_rdata),
        .dmem_we(dmem_we)
    );

    // Kết nối Instruction Memory
    Instruction_Memory imem (
        .rst(rst),
        .A(imem_addr),
        .RD(imem_data)
    );

    // Kết nối Data Memory
    Data_Memory dmem (
        .clk(clk),
        .rst(rst),
        .WE(dmem_we),
        .WD(dmem_wdata),
        .A(dmem_addr),
        .RD(dmem_rdata)
    );

endmodule
