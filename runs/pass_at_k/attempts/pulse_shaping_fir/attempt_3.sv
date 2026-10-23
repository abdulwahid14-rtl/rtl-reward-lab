// Blind attempt 3: plausible transcription bug -- pairs delay tap i with
// coefficient p + 4*(7-i) instead of p + 4*i, i.e. the tap order within
// each phase is reversed relative to the spec. Structure is otherwise
// identical to attempt_1.
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

  wire signed [7:0] coeffs [0:31];
  assign coeffs[0]  = IwCoeffsIn_0;  assign coeffs[1]  = IwCoeffsIn_1;
  assign coeffs[2]  = IwCoeffsIn_2;  assign coeffs[3]  = IwCoeffsIn_3;
  assign coeffs[4]  = IwCoeffsIn_4;  assign coeffs[5]  = IwCoeffsIn_5;
  assign coeffs[6]  = IwCoeffsIn_6;  assign coeffs[7]  = IwCoeffsIn_7;
  assign coeffs[8]  = IwCoeffsIn_8;  assign coeffs[9]  = IwCoeffsIn_9;
  assign coeffs[10] = IwCoeffsIn_10; assign coeffs[11] = IwCoeffsIn_11;
  assign coeffs[12] = IwCoeffsIn_12; assign coeffs[13] = IwCoeffsIn_13;
  assign coeffs[14] = IwCoeffsIn_14; assign coeffs[15] = IwCoeffsIn_15;
  assign coeffs[16] = IwCoeffsIn_16; assign coeffs[17] = IwCoeffsIn_17;
  assign coeffs[18] = IwCoeffsIn_18; assign coeffs[19] = IwCoeffsIn_19;
  assign coeffs[20] = IwCoeffsIn_20; assign coeffs[21] = IwCoeffsIn_21;
  assign coeffs[22] = IwCoeffsIn_22; assign coeffs[23] = IwCoeffsIn_23;
  assign coeffs[24] = IwCoeffsIn_24; assign coeffs[25] = IwCoeffsIn_25;
  assign coeffs[26] = IwCoeffsIn_26; assign coeffs[27] = IwCoeffsIn_27;
  assign coeffs[28] = IwCoeffsIn_28; assign coeffs[29] = IwCoeffsIn_29;
  assign coeffs[30] = IwCoeffsIn_30; assign coeffs[31] = IwCoeffsIn_31;

  reg signed [1:0] shift [1:7];
  integer i;
  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M) begin
      for (i = 1; i <= 7; i = i + 1)
        shift[i] <= 2'sb00;
    end else if (enb) begin
      shift[1] <= IwPulseIn;
      for (i = 2; i <= 7; i = i + 1)
        shift[i] <= shift[i-1];
    end
  end

  wire signed [1:0] tap [0:7];
  assign tap[0] = IwPulseIn;
  genvar g;
  generate
    for (g = 1; g <= 7; g = g + 1) begin : TAPS
      assign tap[g] = shift[g];
    end
  endgenerate

  reg signed [10:0] phase_sum [0:3];
  integer p, t;
  reg signed [10:0] acc;
  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M) begin
      for (p = 0; p < 4; p = p + 1)
        phase_sum[p] <= 11'sb0;
    end else if (enb) begin
      for (p = 0; p < 4; p = p + 1) begin
        acc = 11'sb0;
        for (t = 0; t < 8; t = t + 1)
          acc = acc + tap[t] * coeffs[p + 4*(7-t)];  // BUG: reversed tap order
        phase_sum[p] <= acc;
      end
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

  assign OwSampleOut_0 = saturate(phase_sum[0]);
  assign OwSampleOut_1 = saturate(phase_sum[1]);
  assign OwSampleOut_2 = saturate(phase_sum[2]);
  assign OwSampleOut_3 = saturate(phase_sum[3]);

endmodule
