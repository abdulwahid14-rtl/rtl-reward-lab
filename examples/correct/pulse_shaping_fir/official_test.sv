`timescale 1ns/1ps

module tb;

  localparam CLK_PERIOD  = 2;
  localparam NUM_SAMPLES = 2000;

  reg                 IwClk_500M;
  reg                 IwRst_n_500M;
  reg                 enb;
  reg  signed [1:0]   IwPulseIn;

  reg  signed [7:0]   coeffs [0:31];
  wire signed [7:0]   IwCoeffsIn_0  = coeffs[0];
  wire signed [7:0]   IwCoeffsIn_1  = coeffs[1];
  wire signed [7:0]   IwCoeffsIn_2  = coeffs[2];
  wire signed [7:0]   IwCoeffsIn_3  = coeffs[3];
  wire signed [7:0]   IwCoeffsIn_4  = coeffs[4];
  wire signed [7:0]   IwCoeffsIn_5  = coeffs[5];
  wire signed [7:0]   IwCoeffsIn_6  = coeffs[6];
  wire signed [7:0]   IwCoeffsIn_7  = coeffs[7];
  wire signed [7:0]   IwCoeffsIn_8  = coeffs[8];
  wire signed [7:0]   IwCoeffsIn_9  = coeffs[9];
  wire signed [7:0]   IwCoeffsIn_10 = coeffs[10];
  wire signed [7:0]   IwCoeffsIn_11 = coeffs[11];
  wire signed [7:0]   IwCoeffsIn_12 = coeffs[12];
  wire signed [7:0]   IwCoeffsIn_13 = coeffs[13];
  wire signed [7:0]   IwCoeffsIn_14 = coeffs[14];
  wire signed [7:0]   IwCoeffsIn_15 = coeffs[15];
  wire signed [7:0]   IwCoeffsIn_16 = coeffs[16];
  wire signed [7:0]   IwCoeffsIn_17 = coeffs[17];
  wire signed [7:0]   IwCoeffsIn_18 = coeffs[18];
  wire signed [7:0]   IwCoeffsIn_19 = coeffs[19];
  wire signed [7:0]   IwCoeffsIn_20 = coeffs[20];
  wire signed [7:0]   IwCoeffsIn_21 = coeffs[21];
  wire signed [7:0]   IwCoeffsIn_22 = coeffs[22];
  wire signed [7:0]   IwCoeffsIn_23 = coeffs[23];
  wire signed [7:0]   IwCoeffsIn_24 = coeffs[24];
  wire signed [7:0]   IwCoeffsIn_25 = coeffs[25];
  wire signed [7:0]   IwCoeffsIn_26 = coeffs[26];
  wire signed [7:0]   IwCoeffsIn_27 = coeffs[27];
  wire signed [7:0]   IwCoeffsIn_28 = coeffs[28];
  wire signed [7:0]   IwCoeffsIn_29 = coeffs[29];
  wire signed [7:0]   IwCoeffsIn_30 = coeffs[30];
  wire signed [7:0]   IwCoeffsIn_31 = coeffs[31];

  wire signed [7:0] cand_out0, cand_out1, cand_out2, cand_out3;
  wire signed [7:0] ref_out0,  ref_out1,  ref_out2,  ref_out3;

  TopModule dut (
    .IwClk_500M(IwClk_500M),
    .IwRst_n_500M(IwRst_n_500M),
    .enb(enb),
    .IwPulseIn(IwPulseIn),
    .IwCoeffsIn_0(IwCoeffsIn_0),
    .IwCoeffsIn_1(IwCoeffsIn_1),
    .IwCoeffsIn_2(IwCoeffsIn_2),
    .IwCoeffsIn_3(IwCoeffsIn_3),
    .IwCoeffsIn_4(IwCoeffsIn_4),
    .IwCoeffsIn_5(IwCoeffsIn_5),
    .IwCoeffsIn_6(IwCoeffsIn_6),
    .IwCoeffsIn_7(IwCoeffsIn_7),
    .IwCoeffsIn_8(IwCoeffsIn_8),
    .IwCoeffsIn_9(IwCoeffsIn_9),
    .IwCoeffsIn_10(IwCoeffsIn_10),
    .IwCoeffsIn_11(IwCoeffsIn_11),
    .IwCoeffsIn_12(IwCoeffsIn_12),
    .IwCoeffsIn_13(IwCoeffsIn_13),
    .IwCoeffsIn_14(IwCoeffsIn_14),
    .IwCoeffsIn_15(IwCoeffsIn_15),
    .IwCoeffsIn_16(IwCoeffsIn_16),
    .IwCoeffsIn_17(IwCoeffsIn_17),
    .IwCoeffsIn_18(IwCoeffsIn_18),
    .IwCoeffsIn_19(IwCoeffsIn_19),
    .IwCoeffsIn_20(IwCoeffsIn_20),
    .IwCoeffsIn_21(IwCoeffsIn_21),
    .IwCoeffsIn_22(IwCoeffsIn_22),
    .IwCoeffsIn_23(IwCoeffsIn_23),
    .IwCoeffsIn_24(IwCoeffsIn_24),
    .IwCoeffsIn_25(IwCoeffsIn_25),
    .IwCoeffsIn_26(IwCoeffsIn_26),
    .IwCoeffsIn_27(IwCoeffsIn_27),
    .IwCoeffsIn_28(IwCoeffsIn_28),
    .IwCoeffsIn_29(IwCoeffsIn_29),
    .IwCoeffsIn_30(IwCoeffsIn_30),
    .IwCoeffsIn_31(IwCoeffsIn_31),
    .OwSampleOut_0(cand_out0),
    .OwSampleOut_1(cand_out1),
    .OwSampleOut_2(cand_out2),
    .OwSampleOut_3(cand_out3)
  );

  RefModule ref_dut (
    .IwClk_500M(IwClk_500M),
    .IwRst_n_500M(IwRst_n_500M),
    .enb(enb),
    .IwPulseIn(IwPulseIn),
    .IwCoeffsIn_0(IwCoeffsIn_0),
    .IwCoeffsIn_1(IwCoeffsIn_1),
    .IwCoeffsIn_2(IwCoeffsIn_2),
    .IwCoeffsIn_3(IwCoeffsIn_3),
    .IwCoeffsIn_4(IwCoeffsIn_4),
    .IwCoeffsIn_5(IwCoeffsIn_5),
    .IwCoeffsIn_6(IwCoeffsIn_6),
    .IwCoeffsIn_7(IwCoeffsIn_7),
    .IwCoeffsIn_8(IwCoeffsIn_8),
    .IwCoeffsIn_9(IwCoeffsIn_9),
    .IwCoeffsIn_10(IwCoeffsIn_10),
    .IwCoeffsIn_11(IwCoeffsIn_11),
    .IwCoeffsIn_12(IwCoeffsIn_12),
    .IwCoeffsIn_13(IwCoeffsIn_13),
    .IwCoeffsIn_14(IwCoeffsIn_14),
    .IwCoeffsIn_15(IwCoeffsIn_15),
    .IwCoeffsIn_16(IwCoeffsIn_16),
    .IwCoeffsIn_17(IwCoeffsIn_17),
    .IwCoeffsIn_18(IwCoeffsIn_18),
    .IwCoeffsIn_19(IwCoeffsIn_19),
    .IwCoeffsIn_20(IwCoeffsIn_20),
    .IwCoeffsIn_21(IwCoeffsIn_21),
    .IwCoeffsIn_22(IwCoeffsIn_22),
    .IwCoeffsIn_23(IwCoeffsIn_23),
    .IwCoeffsIn_24(IwCoeffsIn_24),
    .IwCoeffsIn_25(IwCoeffsIn_25),
    .IwCoeffsIn_26(IwCoeffsIn_26),
    .IwCoeffsIn_27(IwCoeffsIn_27),
    .IwCoeffsIn_28(IwCoeffsIn_28),
    .IwCoeffsIn_29(IwCoeffsIn_29),
    .IwCoeffsIn_30(IwCoeffsIn_30),
    .IwCoeffsIn_31(IwCoeffsIn_31),
    .OwSampleOut_0(ref_out0),
    .OwSampleOut_1(ref_out1),
    .OwSampleOut_2(ref_out2),
    .OwSampleOut_3(ref_out3)
  );

  initial IwClk_500M = 0;
  always #(CLK_PERIOD / 2) IwClk_500M = ~IwClk_500M;

  integer i;
  integer mismatches;
  integer total_samples;

  initial begin
    for (i = 0; i < 32; i = i + 1)
      coeffs[i] = $random;

    IwRst_n_500M = 0;
    enb          = 1;
    IwPulseIn    = 0;
    mismatches   = 0;
    total_samples = 0;

    repeat (4) @(negedge IwClk_500M);
    IwRst_n_500M = 1;

    for (i = 0; i < NUM_SAMPLES; i = i + 1) begin
      @(negedge IwClk_500M);
      // Ternary input: -1, 0 or +1 only (2'b10 / -2 is never driven).
      IwPulseIn = ($random & 32'h7fffffff) % 3 - 1;
      enb       = (($random % 10) != 0);

      if (cand_out0 !== ref_out0 || cand_out1 !== ref_out1 ||
          cand_out2 !== ref_out2 || cand_out3 !== ref_out3) begin
        mismatches = mismatches + 1;
      end
      total_samples = total_samples + 1;
    end

    $display("Hint: Total mismatched samples is %0d out of %0d samples",
              mismatches, total_samples);
    $finish;
  end

endmodule
