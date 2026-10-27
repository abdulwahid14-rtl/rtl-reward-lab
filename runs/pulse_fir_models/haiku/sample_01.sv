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
    output reg signed [7:0] OwSampleOut_0,
    output reg signed [7:0] OwSampleOut_1,
    output reg signed [7:0] OwSampleOut_2,
    output reg signed [7:0] OwSampleOut_3
);

    // Delay line: tap 0 is combinational, taps 1..7 are registered
    reg signed [1:0] d1, d2, d3, d4, d5, d6, d7;

    wire signed [1:0] t0 = IwPulseIn;
    wire signed [1:0] t1 = d1;
    wire signed [1:0] t2 = d2;
    wire signed [1:0] t3 = d3;
    wire signed [1:0] t4 = d4;
    wire signed [1:0] t5 = d5;
    wire signed [1:0] t6 = d6;
    wire signed [1:0] t7 = d7;

    // Signed 8x2 product, computed at 11-bit accumulator width
    function automatic signed [10:0] mul;
        input signed [7:0] c;
        input signed [1:0] x;
        begin
            mul = $signed(c) * $signed(x);
        end
    endfunction

    // Saturating cast from 11-bit accumulator to sfix8_En7
    function automatic [7:0] sat;
        input signed [10:0] v;
        begin
            if (v > 11'sd127)
                sat = 8'h7F;
            else if (v < -11'sd128)
                sat = 8'h80;
            else
                sat = v[7:0];
        end
    endfunction

    // Polyphase accumulators: phase p uses coeffs p, p+4, ..., p+28
    wire signed [10:0] acc0 =
          mul(IwCoeffsIn_0,  t0) + mul(IwCoeffsIn_4,  t1)
        + mul(IwCoeffsIn_8,  t2) + mul(IwCoeffsIn_12, t3)
        + mul(IwCoeffsIn_16, t4) + mul(IwCoeffsIn_20, t5)
        + mul(IwCoeffsIn_24, t6) + mul(IwCoeffsIn_28, t7);

    wire signed [10:0] acc1 =
          mul(IwCoeffsIn_1,  t0) + mul(IwCoeffsIn_5,  t1)
        + mul(IwCoeffsIn_9,  t2) + mul(IwCoeffsIn_13, t3)
        + mul(IwCoeffsIn_17, t4) + mul(IwCoeffsIn_21, t5)
        + mul(IwCoeffsIn_25, t6) + mul(IwCoeffsIn_29, t7);

    wire signed [10:0] acc2 =
          mul(IwCoeffsIn_2,  t0) + mul(IwCoeffsIn_6,  t1)
        + mul(IwCoeffsIn_10, t2) + mul(IwCoeffsIn_14, t3)
        + mul(IwCoeffsIn_18, t4) + mul(IwCoeffsIn_22, t5)
        + mul(IwCoeffsIn_26, t6) + mul(IwCoeffsIn_30, t7);

    wire signed [10:0] acc3 =
          mul(IwCoeffsIn_3,  t0) + mul(IwCoeffsIn_7,  t1)
        + mul(IwCoeffsIn_11, t2) + mul(IwCoeffsIn_15, t3)
        + mul(IwCoeffsIn_19, t4) + mul(IwCoeffsIn_23, t5)
        + mul(IwCoeffsIn_27, t6) + mul(IwCoeffsIn_31, t7);

    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            d1 <= 2'sd0;
            d2 <= 2'sd0;
            d3 <= 2'sd0;
            d4 <= 2'sd0;
            d5 <= 2'sd0;
            d6 <= 2'sd0;
            d7 <= 2'sd0;
            OwSampleOut_0 <= 8'sd0;
            OwSampleOut_1 <= 8'sd0;
            OwSampleOut_2 <= 8'sd0;
            OwSampleOut_3 <= 8'sd0;
        end
        else if (enb) begin
            d1 <= IwPulseIn;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            d6 <= d5;
            d7 <= d6;
            OwSampleOut_0 <= sat(acc0);
            OwSampleOut_1 <= sat(acc1);
            OwSampleOut_2 <= sat(acc2);
            OwSampleOut_3 <= sat(acc3);
        end
    end

endmodule
