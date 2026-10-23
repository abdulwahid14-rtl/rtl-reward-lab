// Blind attempt 2: fully unrolled (no loops/generate), named per-tap
// registers and explicit per-phase sum expressions.
module TopModule (
  input                 IwClk_500M,
  input                 IwRst_n_500M,
  input                 enb,
  input  signed [1:0]   IwPulseIn,
  input  signed [7:0]   IwCoeffsIn_0,
  input  signed [7:0]   IwCoeffsIn_1,
  input  signed [7:0]   IwCoeffsIn_2,
  input  signed [7:0]   IwCoeffsIn_3,
  input  signed [7:0]   IwCoeffsIn_4,
  input  signed [7:0]   IwCoeffsIn_5,
  input  signed [7:0]   IwCoeffsIn_6,
  input  signed [7:0]   IwCoeffsIn_7,
  input  signed [7:0]   IwCoeffsIn_8,
  input  signed [7:0]   IwCoeffsIn_9,
  input  signed [7:0]   IwCoeffsIn_10,
  input  signed [7:0]   IwCoeffsIn_11,
  input  signed [7:0]   IwCoeffsIn_12,
  input  signed [7:0]   IwCoeffsIn_13,
  input  signed [7:0]   IwCoeffsIn_14,
  input  signed [7:0]   IwCoeffsIn_15,
  input  signed [7:0]   IwCoeffsIn_16,
  input  signed [7:0]   IwCoeffsIn_17,
  input  signed [7:0]   IwCoeffsIn_18,
  input  signed [7:0]   IwCoeffsIn_19,
  input  signed [7:0]   IwCoeffsIn_20,
  input  signed [7:0]   IwCoeffsIn_21,
  input  signed [7:0]   IwCoeffsIn_22,
  input  signed [7:0]   IwCoeffsIn_23,
  input  signed [7:0]   IwCoeffsIn_24,
  input  signed [7:0]   IwCoeffsIn_25,
  input  signed [7:0]   IwCoeffsIn_26,
  input  signed [7:0]   IwCoeffsIn_27,
  input  signed [7:0]   IwCoeffsIn_28,
  input  signed [7:0]   IwCoeffsIn_29,
  input  signed [7:0]   IwCoeffsIn_30,
  input  signed [7:0]   IwCoeffsIn_31,
  output signed [7:0]   OwSampleOut_0,
  output signed [7:0]   OwSampleOut_1,
  output signed [7:0]   OwSampleOut_2,
  output signed [7:0]   OwSampleOut_3
);

  reg signed [1:0] d1, d2, d3, d4, d5, d6, d7;
  wire signed [1:0] d0 = IwPulseIn;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M) begin
      d1 <= 2'sb00; d2 <= 2'sb00; d3 <= 2'sb00; d4 <= 2'sb00;
      d5 <= 2'sb00; d6 <= 2'sb00; d7 <= 2'sb00;
    end else if (enb) begin
      d1 <= IwPulseIn; d2 <= d1; d3 <= d2; d4 <= d3;
      d5 <= d4; d6 <= d5; d7 <= d6;
    end
  end

  reg signed [10:0] sum0, sum1, sum2, sum3;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M) begin
      sum0 <= 11'sb0; sum1 <= 11'sb0; sum2 <= 11'sb0; sum3 <= 11'sb0;
    end else if (enb) begin
      sum0 <= d0*IwCoeffsIn_0  + d1*IwCoeffsIn_4  + d2*IwCoeffsIn_8  + d3*IwCoeffsIn_12
            + d4*IwCoeffsIn_16 + d5*IwCoeffsIn_20 + d6*IwCoeffsIn_24 + d7*IwCoeffsIn_28;
      sum1 <= d0*IwCoeffsIn_1  + d1*IwCoeffsIn_5  + d2*IwCoeffsIn_9  + d3*IwCoeffsIn_13
            + d4*IwCoeffsIn_17 + d5*IwCoeffsIn_21 + d6*IwCoeffsIn_25 + d7*IwCoeffsIn_29;
      sum2 <= d0*IwCoeffsIn_2  + d1*IwCoeffsIn_6  + d2*IwCoeffsIn_10 + d3*IwCoeffsIn_14
            + d4*IwCoeffsIn_18 + d5*IwCoeffsIn_22 + d6*IwCoeffsIn_26 + d7*IwCoeffsIn_30;
      sum3 <= d0*IwCoeffsIn_3  + d1*IwCoeffsIn_7  + d2*IwCoeffsIn_11 + d3*IwCoeffsIn_15
            + d4*IwCoeffsIn_19 + d5*IwCoeffsIn_23 + d6*IwCoeffsIn_27 + d7*IwCoeffsIn_31;
    end
  end

  function automatic signed [7:0] saturate(input signed [10:0] v);
    begin
      if ((v[10] == 1'b0) && (v[9:7] != 3'b000))
        saturate = 8'sb01111111;
      else if ((v[10] == 1'b1) && (v[9:7] != 3'b111))
        saturate = 8'sb10000000;
      else
        saturate = v[7:0];
    end
  endfunction

  assign OwSampleOut_0 = saturate(sum0);
  assign OwSampleOut_1 = saturate(sum1);
  assign OwSampleOut_2 = saturate(sum2);
  assign OwSampleOut_3 = saturate(sum3);

endmodule
