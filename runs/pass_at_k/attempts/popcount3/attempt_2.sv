// Blind attempt 2: same behavior, written as an exhaustive case statement.
module TopModule(input [2:0] in, output [1:0] out);
  reg [1:0] out_r;
  always @(*) begin
    case (in)
      3'b000: out_r = 2'd0;
      3'b001: out_r = 2'd1;
      3'b010: out_r = 2'd1;
      3'b100: out_r = 2'd1;
      3'b011: out_r = 2'd2;
      3'b101: out_r = 2'd2;
      3'b110: out_r = 2'd2;
      3'b111: out_r = 2'd3;
    endcase
  end
  assign out = out_r;
endmodule
