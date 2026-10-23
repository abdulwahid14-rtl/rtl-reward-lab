// Polyphase FIR interpolator implemented strictly from the text spec in
// examples/correct/pulse_shaping_fir/prompt.txt, independent of the
// existing reference.sv / candidate.sv implementations.
module TopModule (
  input              IwClk_500M,
  input              IwRst_n_500M,
  input              enb,
  input  signed [1:0]  IwPulseIn,
  input  signed [7:0]  IwCoeffsIn_0,
  input  signed [7:0]  IwCoeffsIn_1,
  input  signed [7:0]  IwCoeffsIn_2,
  input  signed [7:0]  IwCoeffsIn_3,
  input  signed [7:0]  IwCoeffsIn_4,
  input  signed [7:0]  IwCoeffsIn_5,
  input  signed [7:0]  IwCoeffsIn_6,
  input  signed [7:0]  IwCoeffsIn_7,
  input  signed [7:0]  IwCoeffsIn_8,
  input  signed [7:0]  IwCoeffsIn_9,
  input  signed [7:0]  IwCoeffsIn_10,
  input  signed [7:0]  IwCoeffsIn_11,
  input  signed [7:0]  IwCoeffsIn_12,
  input  signed [7:0]  IwCoeffsIn_13,
  input  signed [7:0]  IwCoeffsIn_14,
  input  signed [7:0]  IwCoeffsIn_15,
  input  signed [7:0]  IwCoeffsIn_16,
  input  signed [7:0]  IwCoeffsIn_17,
  input  signed [7:0]  IwCoeffsIn_18,
  input  signed [7:0]  IwCoeffsIn_19,
  input  signed [7:0]  IwCoeffsIn_20,
  input  signed [7:0]  IwCoeffsIn_21,
  input  signed [7:0]  IwCoeffsIn_22,
  input  signed [7:0]  IwCoeffsIn_23,
  input  signed [7:0]  IwCoeffsIn_24,
  input  signed [7:0]  IwCoeffsIn_25,
  input  signed [7:0]  IwCoeffsIn_26,
  input  signed [7:0]  IwCoeffsIn_27,
  input  signed [7:0]  IwCoeffsIn_28,
  input  signed [7:0]  IwCoeffsIn_29,
  input  signed [7:0]  IwCoeffsIn_30,
  input  signed [7:0]  IwCoeffsIn_31,
  output signed [7:0]  OwSampleOut_0,
  output signed [7:0]  OwSampleOut_1,
  output signed [7:0]  OwSampleOut_2,
  output signed [7:0]  OwSampleOut_3
);

  // -- Coefficient bank, indexable as coeffs[0..31]. --
  wire signed [7:0] coeffs [0:31];
  assign coeffs[0]  = IwCoeffsIn_0;
  assign coeffs[1]  = IwCoeffsIn_1;
  assign coeffs[2]  = IwCoeffsIn_2;
  assign coeffs[3]  = IwCoeffsIn_3;
  assign coeffs[4]  = IwCoeffsIn_4;
  assign coeffs[5]  = IwCoeffsIn_5;
  assign coeffs[6]  = IwCoeffsIn_6;
  assign coeffs[7]  = IwCoeffsIn_7;
  assign coeffs[8]  = IwCoeffsIn_8;
  assign coeffs[9]  = IwCoeffsIn_9;
  assign coeffs[10] = IwCoeffsIn_10;
  assign coeffs[11] = IwCoeffsIn_11;
  assign coeffs[12] = IwCoeffsIn_12;
  assign coeffs[13] = IwCoeffsIn_13;
  assign coeffs[14] = IwCoeffsIn_14;
  assign coeffs[15] = IwCoeffsIn_15;
  assign coeffs[16] = IwCoeffsIn_16;
  assign coeffs[17] = IwCoeffsIn_17;
  assign coeffs[18] = IwCoeffsIn_18;
  assign coeffs[19] = IwCoeffsIn_19;
  assign coeffs[20] = IwCoeffsIn_20;
  assign coeffs[21] = IwCoeffsIn_21;
  assign coeffs[22] = IwCoeffsIn_22;
  assign coeffs[23] = IwCoeffsIn_23;
  assign coeffs[24] = IwCoeffsIn_24;
  assign coeffs[25] = IwCoeffsIn_25;
  assign coeffs[26] = IwCoeffsIn_26;
  assign coeffs[27] = IwCoeffsIn_27;
  assign coeffs[28] = IwCoeffsIn_28;
  assign coeffs[29] = IwCoeffsIn_29;
  assign coeffs[30] = IwCoeffsIn_30;
  assign coeffs[31] = IwCoeffsIn_31;

  // -- 8-deep delay line. Tap 0 is the combinational passthrough input;
  //    taps 1-7 are a 7-deep register chain, held while enb is low,
  //    asynchronously reset to 0. --
  reg signed [1:0] delay_taps [1:7];
  wire signed [1:0] taps [0:7];
  assign taps[0] = IwPulseIn;
  assign taps[1] = delay_taps[1];
  assign taps[2] = delay_taps[2];
  assign taps[3] = delay_taps[3];
  assign taps[4] = delay_taps[4];
  assign taps[5] = delay_taps[5];
  assign taps[6] = delay_taps[6];
  assign taps[7] = delay_taps[7];

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M) begin
      delay_taps[1] <= 2'sb0;
      delay_taps[2] <= 2'sb0;
      delay_taps[3] <= 2'sb0;
      delay_taps[4] <= 2'sb0;
      delay_taps[5] <= 2'sb0;
      delay_taps[6] <= 2'sb0;
      delay_taps[7] <= 2'sb0;
    end else if (enb) begin
      delay_taps[7] <= delay_taps[6];
      delay_taps[6] <= delay_taps[5];
      delay_taps[5] <= delay_taps[4];
      delay_taps[4] <= delay_taps[3];
      delay_taps[3] <= delay_taps[2];
      delay_taps[2] <= delay_taps[1];
      delay_taps[1] <= taps[0];
    end
  end

  // -- Polyphase decomposition: phase p sums taps[i] * coeffs[p + 4*i]
  //    for i = 0..7, into an 11-bit signed accumulator registered once
  //    per enabled clock edge, reset to 0 on async reset. --
  genvar gp, gi;
  wire signed [31:0] phase_sum [0:3];
  generate
    for (gp = 0; gp < 4; gp = gp + 1) begin : g_phase
      wire signed [31:0] partial [0:7];
      for (gi = 0; gi < 8; gi = gi + 1) begin : g_tap
        assign partial[gi] = taps[gi] * coeffs[gp + 4 * gi];
      end
      assign phase_sum[gp] = partial[0] + partial[1] + partial[2] + partial[3]
                           + partial[4] + partial[5] + partial[6] + partial[7];
    end
  endgenerate

  reg signed [10:0] phase_acc [0:3];
  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M) begin
      phase_acc[0] <= 11'sb0;
      phase_acc[1] <= 11'sb0;
      phase_acc[2] <= 11'sb0;
      phase_acc[3] <= 11'sb0;
    end else if (enb) begin
      phase_acc[0] <= phase_sum[0][10:0];
      phase_acc[1] <= phase_sum[1][10:0];
      phase_acc[2] <= phase_sum[2][10:0];
      phase_acc[3] <= phase_sum[3][10:0];
    end
  end

  // -- Output saturation: 11-bit signed accumulator down to 8-bit
  //    signed output, saturating (not wrapping) on overflow. --
  function signed [7:0] saturate11to8(input signed [10:0] v);
    begin
      if (v > 11'sd127)
        saturate11to8 = 8'sb01111111;
      else if (v < -11'sd128)
        saturate11to8 = 8'sb10000000;
      else
        saturate11to8 = v[7:0];
    end
  endfunction

  assign OwSampleOut_0 = saturate11to8(phase_acc[0]);
  assign OwSampleOut_1 = saturate11to8(phase_acc[1]);
  assign OwSampleOut_2 = saturate11to8(phase_acc[2]);
  assign OwSampleOut_3 = saturate11to8(phase_acc[3]);

endmodule
