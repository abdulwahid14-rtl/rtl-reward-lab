module TopModule (
    input                    IwClk_500M,
    input                    IwRst_n_500M,
    input                    enb,
    input  signed [1:0]      IwPulseIn,
    input  signed [7:0]      IwCoeffsIn_0,
    input  signed [7:0]      IwCoeffsIn_1,
    input  signed [7:0]      IwCoeffsIn_2,
    input  signed [7:0]      IwCoeffsIn_3,
    input  signed [7:0]      IwCoeffsIn_4,
    input  signed [7:0]      IwCoeffsIn_5,
    input  signed [7:0]      IwCoeffsIn_6,
    input  signed [7:0]      IwCoeffsIn_7,
    input  signed [7:0]      IwCoeffsIn_8,
    input  signed [7:0]      IwCoeffsIn_9,
    input  signed [7:0]      IwCoeffsIn_10,
    input  signed [7:0]      IwCoeffsIn_11,
    input  signed [7:0]      IwCoeffsIn_12,
    input  signed [7:0]      IwCoeffsIn_13,
    input  signed [7:0]      IwCoeffsIn_14,
    input  signed [7:0]      IwCoeffsIn_15,
    input  signed [7:0]      IwCoeffsIn_16,
    input  signed [7:0]      IwCoeffsIn_17,
    input  signed [7:0]      IwCoeffsIn_18,
    input  signed [7:0]      IwCoeffsIn_19,
    input  signed [7:0]      IwCoeffsIn_20,
    input  signed [7:0]      IwCoeffsIn_21,
    input  signed [7:0]      IwCoeffsIn_22,
    input  signed [7:0]      IwCoeffsIn_23,
    input  signed [7:0]      IwCoeffsIn_24,
    input  signed [7:0]      IwCoeffsIn_25,
    input  signed [7:0]      IwCoeffsIn_26,
    input  signed [7:0]      IwCoeffsIn_27,
    input  signed [7:0]      IwCoeffsIn_28,
    input  signed [7:0]      IwCoeffsIn_29,
    input  signed [7:0]      IwCoeffsIn_30,
    input  signed [7:0]      IwCoeffsIn_31,
    output reg signed [7:0]  OwSampleOut_0,
    output reg signed [7:0]  OwSampleOut_1,
    output reg signed [7:0]  OwSampleOut_2,
    output reg signed [7:0]  OwSampleOut_3
);

    // Delay line: tap 0 is combinational passthrough, taps 1..7 are registered
    reg signed [1:0] d1, d2, d3, d4, d5, d6, d7;

    wire signed [1:0] tap0 = IwPulseIn;
    wire signed [1:0] tap1 = d1;
    wire signed [1:0] tap2 = d2;
    wire signed [1:0] tap3 = d3;
    wire signed [1:0] tap4 = d4;
    wire signed [1:0] tap5 = d5;
    wire signed [1:0] tap6 = d6;
    wire signed [1:0] tap7 = d7;

    // Per-phase 11-bit accumulators (sum of 8 products, each up to 8 bits x 2 bits)
    wire signed [10:0] acc0 =
        IwCoeffsIn_0  * tap0 + IwCoeffsIn_4  * tap1 + IwCoeffsIn_8  * tap2 + IwCoeffsIn_12 * tap3 +
        IwCoeffsIn_16 * tap4 + IwCoeffsIn_20 * tap5 + IwCoeffsIn_24 * tap6 + IwCoeffsIn_28 * tap7;

    wire signed [10:0] acc1 =
        IwCoeffsIn_1  * tap0 + IwCoeffsIn_5  * tap1 + IwCoeffsIn_9  * tap2 + IwCoeffsIn_13 * tap3 +
        IwCoeffsIn_17 * tap4 + IwCoeffsIn_21 * tap5 + IwCoeffsIn_25 * tap6 + IwCoeffsIn_29 * tap7;

    wire signed [10:0] acc2 =
        IwCoeffsIn_2  * tap0 + IwCoeffsIn_6  * tap1 + IwCoeffsIn_10 * tap2 + IwCoeffsIn_14 * tap3 +
        IwCoeffsIn_18 * tap4 + IwCoeffsIn_22 * tap5 + IwCoeffsIn_26 * tap6 + IwCoeffsIn_30 * tap7;

    wire signed [10:0] acc3 =
        IwCoeffsIn_3  * tap0 + IwCoeffsIn_7  * tap1 + IwCoeffsIn_11 * tap2 + IwCoeffsIn_15 * tap3 +
        IwCoeffsIn_19 * tap4 + IwCoeffsIn_23 * tap5 + IwCoeffsIn_27 * tap6 + IwCoeffsIn_31 * tap7;

    // Saturating cast from 11-bit accumulator to sfix8_En7
    function signed [7:0] sat8;
        input signed [10:0] v;
        begin
            if (!v[10] && (v[9:7] != 3'b000))
                sat8 = 8'sb01111111;        // positive overflow
            else if (v[10] && (v[9:7] != 3'b111))
                sat8 = 8'sb10000000;        // negative overflow
            else
                sat8 = v[7:0];              // in range: truncate, no rounding
        end
    endfunction

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
        end else if (enb) begin
            d1 <= IwPulseIn;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            d6 <= d5;
            d7 <= d6;
            OwSampleOut_0 <= sat8(acc0);
            OwSampleOut_1 <= sat8(acc1);
            OwSampleOut_2 <= sat8(acc2);
            OwSampleOut_3 <= sat8(acc3);
        end
    end

endmodule
