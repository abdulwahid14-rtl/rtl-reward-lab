// Derived from a Simulink/HDL-Coder-generated polyphase FIR pulse-shaping
// interpolator (upsample-by-4, 32 taps split into 4 phases of 8 taps each).
//
// The source snippet provided was missing:
//   1. The top module's name and port-direction header line.
//   2. The body of submodule sca_vbond_tx_Delayline.
//   3. The body of submodule sca_vbond_tx_Polyphase_FIR0.
//
// (1) is filled in here as "RefModule" per this project's task convention
// (candidate -> TopModule, reference -> RefModule). (2) and (3) are
// reconstructed below as straightforward implementations matching the
// declared port widths and the bit growth implied by the original wiring
// (sfix2 x sfix8_En7 -> accumulated into sfix11_En7). They are best-effort
// reconstructions, not the original IP -- flagged inline on each module.

module RefModule (
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

  wire signed [1:0] Delayline_out1_Delay0;
  wire signed [1:0] Delayline_out1_Delay1;
  wire signed [1:0] Delayline_out1_Delay2;
  wire signed [1:0] Delayline_out1_Delay3;
  wire signed [1:0] Delayline_out1_Delay4;
  wire signed [1:0] Delayline_out1_Delay5;
  wire signed [1:0] Delayline_out1_Delay6;
  wire signed [1:0] Delayline_out1_Delay7;
  wire signed [10:0] Polyphase_FIR0_out1;
  wire signed [10:0] Polyphase_FIR1_out1;
  wire signed [10:0] Polyphase_FIR2_out1;
  wire signed [10:0] Polyphase_FIR3_out1;
  wire signed [10:0] Mux_out1 [0:3];
  wire signed [7:0] Data_Type_Conversion3_out1 [0:3];

  sca_vbond_tx_Delayline u_Delayline (
    .IwClk_500M(IwClk_500M),
    .IwRst_n_500M(IwRst_n_500M),
    .enb(enb),
    .In(IwPulseIn),
    .DelayedOut_Delay0(Delayline_out1_Delay0),
    .DelayedOut_Delay1(Delayline_out1_Delay1),
    .DelayedOut_Delay2(Delayline_out1_Delay2),
    .DelayedOut_Delay3(Delayline_out1_Delay3),
    .DelayedOut_Delay4(Delayline_out1_Delay4),
    .DelayedOut_Delay5(Delayline_out1_Delay5),
    .DelayedOut_Delay6(Delayline_out1_Delay6),
    .DelayedOut_Delay7(Delayline_out1_Delay7)
  );

  sca_vbond_tx_Polyphase_FIR0 u_Polyphase_FIR0 (
    .IwClk_500M(IwClk_500M),
    .IwRst_n_500M(IwRst_n_500M),
    .enb(enb),
    .IwPulseIn_Delay0(Delayline_out1_Delay0),
    .IwPulseIn_Delay1(Delayline_out1_Delay1),
    .IwPulseIn_Delay2(Delayline_out1_Delay2),
    .IwPulseIn_Delay3(Delayline_out1_Delay3),
    .IwPulseIn_Delay4(Delayline_out1_Delay4),
    .IwPulseIn_Delay5(Delayline_out1_Delay5),
    .IwPulseIn_Delay6(Delayline_out1_Delay6),
    .IwPulseIn_Delay7(Delayline_out1_Delay7),
    .IwCoeffsIn_0(IwCoeffsIn_0),
    .IwCoeffsIn_1(IwCoeffsIn_4),
    .IwCoeffsIn_2(IwCoeffsIn_8),
    .IwCoeffsIn_3(IwCoeffsIn_12),
    .IwCoeffsIn_4(IwCoeffsIn_16),
    .IwCoeffsIn_5(IwCoeffsIn_20),
    .IwCoeffsIn_6(IwCoeffsIn_24),
    .IwCoeffsIn_7(IwCoeffsIn_28),
    .OwSampleOut(Polyphase_FIR0_out1)
  );

  sca_vbond_tx_Polyphase_FIR0 u_Polyphase_FIR1 (
    .IwClk_500M(IwClk_500M),
    .IwRst_n_500M(IwRst_n_500M),
    .enb(enb),
    .IwPulseIn_Delay0(Delayline_out1_Delay0),
    .IwPulseIn_Delay1(Delayline_out1_Delay1),
    .IwPulseIn_Delay2(Delayline_out1_Delay2),
    .IwPulseIn_Delay3(Delayline_out1_Delay3),
    .IwPulseIn_Delay4(Delayline_out1_Delay4),
    .IwPulseIn_Delay5(Delayline_out1_Delay5),
    .IwPulseIn_Delay6(Delayline_out1_Delay6),
    .IwPulseIn_Delay7(Delayline_out1_Delay7),
    .IwCoeffsIn_0(IwCoeffsIn_1),
    .IwCoeffsIn_1(IwCoeffsIn_5),
    .IwCoeffsIn_2(IwCoeffsIn_9),
    .IwCoeffsIn_3(IwCoeffsIn_13),
    .IwCoeffsIn_4(IwCoeffsIn_17),
    .IwCoeffsIn_5(IwCoeffsIn_21),
    .IwCoeffsIn_6(IwCoeffsIn_25),
    .IwCoeffsIn_7(IwCoeffsIn_29),
    .OwSampleOut(Polyphase_FIR1_out1)
  );

  sca_vbond_tx_Polyphase_FIR0 u_Polyphase_FIR2 (
    .IwClk_500M(IwClk_500M),
    .IwRst_n_500M(IwRst_n_500M),
    .enb(enb),
    .IwPulseIn_Delay0(Delayline_out1_Delay0),
    .IwPulseIn_Delay1(Delayline_out1_Delay1),
    .IwPulseIn_Delay2(Delayline_out1_Delay2),
    .IwPulseIn_Delay3(Delayline_out1_Delay3),
    .IwPulseIn_Delay4(Delayline_out1_Delay4),
    .IwPulseIn_Delay5(Delayline_out1_Delay5),
    .IwPulseIn_Delay6(Delayline_out1_Delay6),
    .IwPulseIn_Delay7(Delayline_out1_Delay7),
    .IwCoeffsIn_0(IwCoeffsIn_2),
    .IwCoeffsIn_1(IwCoeffsIn_6),
    .IwCoeffsIn_2(IwCoeffsIn_10),
    .IwCoeffsIn_3(IwCoeffsIn_14),
    .IwCoeffsIn_4(IwCoeffsIn_18),
    .IwCoeffsIn_5(IwCoeffsIn_22),
    .IwCoeffsIn_6(IwCoeffsIn_26),
    .IwCoeffsIn_7(IwCoeffsIn_30),
    .OwSampleOut(Polyphase_FIR2_out1)
  );

  sca_vbond_tx_Polyphase_FIR0 u_Polyphase_FIR3 (
    .IwClk_500M(IwClk_500M),
    .IwRst_n_500M(IwRst_n_500M),
    .enb(enb),
    .IwPulseIn_Delay0(Delayline_out1_Delay0),
    .IwPulseIn_Delay1(Delayline_out1_Delay1),
    .IwPulseIn_Delay2(Delayline_out1_Delay2),
    .IwPulseIn_Delay3(Delayline_out1_Delay3),
    .IwPulseIn_Delay4(Delayline_out1_Delay4),
    .IwPulseIn_Delay5(Delayline_out1_Delay5),
    .IwPulseIn_Delay6(Delayline_out1_Delay6),
    .IwPulseIn_Delay7(Delayline_out1_Delay7),
    .IwCoeffsIn_0(IwCoeffsIn_3),
    .IwCoeffsIn_1(IwCoeffsIn_7),
    .IwCoeffsIn_2(IwCoeffsIn_11),
    .IwCoeffsIn_3(IwCoeffsIn_15),
    .IwCoeffsIn_4(IwCoeffsIn_19),
    .IwCoeffsIn_5(IwCoeffsIn_23),
    .IwCoeffsIn_6(IwCoeffsIn_27),
    .IwCoeffsIn_7(IwCoeffsIn_31),
    .OwSampleOut(Polyphase_FIR3_out1)
  );

  assign Mux_out1[0] = Polyphase_FIR0_out1;
  assign Mux_out1[1] = Polyphase_FIR1_out1;
  assign Mux_out1[2] = Polyphase_FIR2_out1;
  assign Mux_out1[3] = Polyphase_FIR3_out1;

  assign Data_Type_Conversion3_out1[0] = ((Mux_out1[0][10] == 1'b0) && (Mux_out1[0][9:7] != 3'b000) ? 8'sb01111111 :
              ((Mux_out1[0][10] == 1'b1) && (Mux_out1[0][9:7] != 3'b111) ? 8'sb10000000 :
              $signed(Mux_out1[0][7:0])));
  assign Data_Type_Conversion3_out1[1] = ((Mux_out1[1][10] == 1'b0) && (Mux_out1[1][9:7] != 3'b000) ? 8'sb01111111 :
              ((Mux_out1[1][10] == 1'b1) && (Mux_out1[1][9:7] != 3'b111) ? 8'sb10000000 :
              $signed(Mux_out1[1][7:0])));
  assign Data_Type_Conversion3_out1[2] = ((Mux_out1[2][10] == 1'b0) && (Mux_out1[2][9:7] != 3'b000) ? 8'sb01111111 :
              ((Mux_out1[2][10] == 1'b1) && (Mux_out1[2][9:7] != 3'b111) ? 8'sb10000000 :
              $signed(Mux_out1[2][7:0])));
  assign Data_Type_Conversion3_out1[3] = ((Mux_out1[3][10] == 1'b0) && (Mux_out1[3][9:7] != 3'b000) ? 8'sb01111111 :
              ((Mux_out1[3][10] == 1'b1) && (Mux_out1[3][9:7] != 3'b111) ? 8'sb10000000 :
              $signed(Mux_out1[3][7:0])));

  assign OwSampleOut_0 = Data_Type_Conversion3_out1[0];
  assign OwSampleOut_1 = Data_Type_Conversion3_out1[1];
  assign OwSampleOut_2 = Data_Type_Conversion3_out1[2];
  assign OwSampleOut_3 = Data_Type_Conversion3_out1[3];

endmodule


// ---------------------------------------------------------------------------
// Exact source provided by the user: Delay0 is a combinational passthrough
// of `In`; Delay1..Delay7 form a 7-deep synchronous register chain.
// ---------------------------------------------------------------------------
module sca_vbond_tx_Delayline (
  input                IwClk_500M,
  input                IwRst_n_500M,
  input                enb,
  input  signed [1:0]  In,
  output signed [1:0]  DelayedOut_Delay0,
  output signed [1:0]  DelayedOut_Delay1,
  output signed [1:0]  DelayedOut_Delay2,
  output signed [1:0]  DelayedOut_Delay3,
  output signed [1:0]  DelayedOut_Delay4,
  output signed [1:0]  DelayedOut_Delay5,
  output signed [1:0]  DelayedOut_Delay6,
  output signed [1:0]  DelayedOut_Delay7
);

  reg signed [1:0] Delay1_1;
  reg signed [1:0] Delay2_1;
  reg signed [1:0] Delay3_1;
  reg signed [1:0] Delay4_1;
  reg signed [1:0] Delay5_1;
  reg signed [1:0] Delay6_1;
  reg signed [1:0] Delay7_1;

  assign DelayedOut_Delay0 = In;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (IwRst_n_500M == 1'b0) begin
      Delay1_1 <= 2'sb00;
    end else begin
      if (enb) begin
        Delay1_1 <= In;
      end
    end
  end

  assign DelayedOut_Delay1 = Delay1_1;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (IwRst_n_500M == 1'b0) begin
      Delay2_1 <= 2'sb00;
    end else begin
      if (enb) begin
        Delay2_1 <= Delay1_1;
      end
    end
  end

  assign DelayedOut_Delay2 = Delay2_1;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (IwRst_n_500M == 1'b0) begin
      Delay3_1 <= 2'sb00;
    end else begin
      if (enb) begin
        Delay3_1 <= Delay2_1;
      end
    end
  end

  assign DelayedOut_Delay3 = Delay3_1;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (IwRst_n_500M == 1'b0) begin
      Delay4_1 <= 2'sb00;
    end else begin
      if (enb) begin
        Delay4_1 <= Delay3_1;
      end
    end
  end

  assign DelayedOut_Delay4 = Delay4_1;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (IwRst_n_500M == 1'b0) begin
      Delay5_1 <= 2'sb00;
    end else begin
      if (enb) begin
        Delay5_1 <= Delay4_1;
      end
    end
  end

  assign DelayedOut_Delay5 = Delay5_1;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (IwRst_n_500M == 1'b0) begin
      Delay6_1 <= 2'sb00;
    end else begin
      if (enb) begin
        Delay6_1 <= Delay5_1;
      end
    end
  end

  assign DelayedOut_Delay6 = Delay6_1;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (IwRst_n_500M == 1'b0) begin
      Delay7_1 <= 2'sb00;
    end else begin
      if (enb) begin
        Delay7_1 <= Delay6_1;
      end
    end
  end

  assign DelayedOut_Delay7 = Delay7_1;

endmodule


// ---------------------------------------------------------------------------
// RECONSTRUCTED (not from the provided source): 8-tap MAC for one polyphase
// branch. Each sfix2 x sfix8_En7 product is sfix10_En7; the 8 products are
// summed combinationally and registered once per enabled clock, truncated to
// the declared 11-bit (sfix11_En7) accumulator width -- matching the limited
// (2-bit, not full 3-bit) guard growth implied by the original port widths.
// No explicit rounding; final saturation to 8 bits happens in RefModule.
// ---------------------------------------------------------------------------
module sca_vbond_tx_Polyphase_FIR0 (
  input                IwClk_500M,
  input                IwRst_n_500M,
  input                enb,
  input  signed [1:0]  IwPulseIn_Delay0,
  input  signed [1:0]  IwPulseIn_Delay1,
  input  signed [1:0]  IwPulseIn_Delay2,
  input  signed [1:0]  IwPulseIn_Delay3,
  input  signed [1:0]  IwPulseIn_Delay4,
  input  signed [1:0]  IwPulseIn_Delay5,
  input  signed [1:0]  IwPulseIn_Delay6,
  input  signed [1:0]  IwPulseIn_Delay7,
  input  signed [7:0]  IwCoeffsIn_0,
  input  signed [7:0]  IwCoeffsIn_1,
  input  signed [7:0]  IwCoeffsIn_2,
  input  signed [7:0]  IwCoeffsIn_3,
  input  signed [7:0]  IwCoeffsIn_4,
  input  signed [7:0]  IwCoeffsIn_5,
  input  signed [7:0]  IwCoeffsIn_6,
  input  signed [7:0]  IwCoeffsIn_7,
  output signed [10:0] OwSampleOut
);

  wire signed [10:0] sum =
      IwPulseIn_Delay0 * IwCoeffsIn_0 +
      IwPulseIn_Delay1 * IwCoeffsIn_1 +
      IwPulseIn_Delay2 * IwCoeffsIn_2 +
      IwPulseIn_Delay3 * IwCoeffsIn_3 +
      IwPulseIn_Delay4 * IwCoeffsIn_4 +
      IwPulseIn_Delay5 * IwCoeffsIn_5 +
      IwPulseIn_Delay6 * IwCoeffsIn_6 +
      IwPulseIn_Delay7 * IwCoeffsIn_7;

  reg signed [10:0] sum_reg;

  always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
    if (!IwRst_n_500M)
      sum_reg <= 11'sb0;
    else if (enb)
      sum_reg <= sum;
  end

  assign OwSampleOut = sum_reg;

endmodule
