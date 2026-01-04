module PC_Module(clk,rst,PC,PC_Next,debug_halt);
    input clk,rst;
    input [31:0]PC_Next;
	 input debug_halt;
    output [31:0]PC;
    reg [31:0]PC;

    always @(posedge clk)
    begin
        if(rst == 1'b0)
            PC <= {32{1'b0}};
        else if (!debug_halt)
			 PC <= PC_Next;
    end
endmodule