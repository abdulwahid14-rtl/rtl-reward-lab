// Blind attempt 3: plausible mistake -- computes parity (XOR) instead of
// a population count. Parity and popcount agree only when the count is 0
// or 1, so this is wrong for inputs like 011 (count=2, parity=0).
module TopModule(input [2:0] in, output [1:0] out);
  assign out = {1'b0, ^in};
endmodule
