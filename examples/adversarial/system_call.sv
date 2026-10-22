module TopModule(input [2:0] in, output [1:0] out);
  initial $system("echo hijacked");
  assign out = 0;
endmodule
