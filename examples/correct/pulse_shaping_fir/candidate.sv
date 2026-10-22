module TopModule (
  input                    IwClk_500M,
  input                    IwRst_n_500M,
  input                    enb,
  input   signed [1:0]     IwPulseIn,        // sfix2
  input   signed [7:0]     IwCoeffsIn_0,     // sfix8_En7
  input   signed [7:0]     IwCoeffsIn_1,
  input   signed [7:0]     IwCoeffsIn_2,
  input   signed [7:0]     IwCoeffsIn_3,
  input   signed [7:0]     IwCoeffsIn_4,
  input   signed [7:0]     IwCoeffsIn_5,
  input   signed [7:0]     IwCoeffsIn_6,
  input   signed [7:0]     IwCoeffsIn_7,
  input   signed [7:0]     IwCoeffsIn_8,
  input   signed [7:0]     IwCoeffsIn_9,
  input   signed [7:0]     IwCoeffsIn_10,
  input   signed [7:0]     IwCoeffsIn_11,
  input   signed [7:0]     IwCoeffsIn_12,
  input   signed [7:0]     IwCoeffsIn_13,
  input   signed [7:0]     IwCoeffsIn_14,
  input   signed [7:0]     IwCoeffsIn_15,
  input   signed [7:0]     IwCoeffsIn_16,
  input   signed [7:0]     IwCoeffsIn_17,
  input   signed [7:0]     IwCoeffsIn_18,
  input   signed [7:0]     IwCoeffsIn_19,
  input   signed [7:0]     IwCoeffsIn_20,
  input   signed [7:0]     IwCoeffsIn_21,
  input   signed [7:0]     IwCoeffsIn_22,
  input   signed [7:0]     IwCoeffsIn_23,
  input   signed [7:0]     IwCoeffsIn_24,
  input   signed [7:0]     IwCoeffsIn_25,
  input   signed [7:0]     IwCoeffsIn_26,
  input   signed [7:0]     IwCoeffsIn_27,
  input   signed [7:0]     IwCoeffsIn_28,
  input   signed [7:0]     IwCoeffsIn_29,
  input   signed [7:0]     IwCoeffsIn_30,
  input   signed [7:0]     IwCoeffsIn_31,
  output  signed [7:0]     OwSampleOut_0,    // sfix8_En7
  output  signed [7:0]     OwSampleOut_1,
  output  signed [7:0]     OwSampleOut_2,
  output  signed [7:0]     OwSampleOut_3
);

  // Pack the 32 scalar coefficient ports for indexed access.
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

  // 8-deep delay line: tap 0 is combinational, taps 1-7 are a registered
  // chain, synchronously held on enb, asynchronously reset to 0.
  reg signed [1:0] delay [1:7];
  integer d;

  wire signed [1:0] tap [0:7];
  assign tap[0] = IwPulseIn;
  assign tap[1] = delay[1];
  assign tap[2] = delay[2];
  assign tap[3] = delay[3];
  assign tap[4] = delay[4];
  assign tap[5] = delay[5];
  assign tap[6] = delay[6];
  assign tap[7] = delay[7];

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M) begin
      for (d = 1; d <= 7; d = d + 1)
        delay[d] <= 2'sb00;
    end else if (enb) begin
      delay[1] <= IwPulseIn;
      for (d = 2; d <= 7; d = d + 1)
        delay[d] <= delay[d-1];
    end
  end

  // 4 polyphase 8-tap branches: phase p uses coeffs[p + 4*i] paired with
  // tap i, summed into an 11-bit signed accumulator, registered on enb.
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
          acc = acc + tap[t] * coeffs[p + 4 * t];
        phase_sum[p] <= acc;
      end
    end
  end

  // Saturating cast from sfix11_En7 to sfix8_En7.
  function automatic signed [7:0] sat8(input signed [10:0] v);
    begin
      if ((v[10] == 1'b0) && (v[9:7] != 3'b000))
        sat8 = 8'sb01111111;
      else if ((v[10] == 1'b1) && (v[9:7] != 3'b111))
        sat8 = 8'sb10000000;
      else
        sat8 = v[7:0];
    end
  endfunction

  assign OwSampleOut_0 = sat8(phase_sum[0]);
  assign OwSampleOut_1 = sat8(phase_sum[1]);
  assign OwSampleOut_2 = sat8(phase_sum[2]);
  assign OwSampleOut_3 = sat8(phase_sum[3]);

endmodule
