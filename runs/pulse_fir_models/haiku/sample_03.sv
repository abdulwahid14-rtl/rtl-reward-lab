module TopModule (
    input              IwClk_500M,
    input              IwRst_n_500M,
    input              enb,
    input  signed [1:0] IwPulseIn,
    input  signed [7:0] IwCoeffsIn_0,
    input  signed [7:0] IwCoeffsIn_1,
    input  signed [7:0] IwCoeffsIn_2,
    input  signed [7:0] IwCoeffsIn_3,
    input  signed [7:0] IwCoeffsIn_4,
    input  signed [7:0] IwCoeffsIn_5,
    input  signed [7:0] IwCoeffsIn_6,
    input  signed [7:0] IwCoeffsIn_7,
    input  signed [7:0] IwCoeffsIn_8,
    input  signed [7:0] IwCoeffsIn_9,
    input  signed [7:0] IwCoeffsIn_10,
    input  signed [7:0] IwCoeffsIn_11,
    input  signed [7:0] IwCoeffsIn_12,
    input  signed [7:0] IwCoeffsIn_13,
    input  signed [7:0] IwCoeffsIn_14,
    input  signed [7:0] IwCoeffsIn_15,
    input  signed [7:0] IwCoeffsIn_16,
    input  signed [7:0] IwCoeffsIn_17,
    input  signed [7:0] IwCoeffsIn_18,
    input  signed [7:0] IwCoeffsIn_19,
    input  signed [7:0] IwCoeffsIn_20,
    input  signed [7:0] IwCoeffsIn_21,
    input  signed [7:0] IwCoeffsIn_22,
    input  signed [7:0] IwCoeffsIn_23,
    input  signed [7:0] IwCoeffsIn_24,
    input  signed [7:0] IwCoeffsIn_25,
    input  signed [7:0] IwCoeffsIn_26,
    input  signed [7:0] IwCoeffsIn_27,
    input  signed [7:0] IwCoeffsIn_28,
    input  signed [7:0] IwCoeffsIn_29,
    input  signed [7:0] IwCoeffsIn_30,
    input  signed [7:0] IwCoeffsIn_31,
    output reg signed [7:0] OwSampleOut_0,
    output reg signed [7:0] OwSampleOut_1,
    output reg signed [7:0] OwSampleOut_2,
    output reg signed [7:0] OwSampleOut_3
);

    // Delay line: tap 0 is combinational, taps 1..7 are registered
    reg signed [1:0] dly [1:7];
    wire signed [1:0] tap [0:7];

    assign tap[0] = IwPulseIn;
    genvar g;
    generate
        for (g = 1; g < 8; g = g + 1) begin : G_TAP
            assign tap[g] = dly[g];
        end
    endgenerate

    integer i;
    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            for (i = 1; i < 8; i = i + 1)
                dly[i] <= 2'sd0;
        end else if (enb) begin
            dly[1] <= IwPulseIn;
            for (i = 2; i < 8; i = i + 1)
                dly[i] <= dly[i-1];
        end
    end

    // Coefficient table: coef[p][k] = phase p, tap k
    wire signed [7:0] coef [0:3][0:7];

    // Phase p, tap k uses IwCoeffsIn_{p + 4k}
    assign coef[0][0] = IwCoeffsIn_0;
    assign coef[0][1] = IwCoeffsIn_4;
    assign coef[0][2] = IwCoeffsIn_8;
    assign coef[0][3] = IwCoeffsIn_12;
    assign coef[0][4] = IwCoeffsIn_16;
    assign coef[0][5] = IwCoeffsIn_20;
    assign coef[0][6] = IwCoeffsIn_24;
    assign coef[0][7] = IwCoeffsIn_28;

    assign coef[1][0] = IwCoeffsIn_1;
    assign coef[1][1] = IwCoeffsIn_5;
    assign coef[1][2] = IwCoeffsIn_9;
    assign coef[1][3] = IwCoeffsIn_13;
    assign coef[1][4] = IwCoeffsIn_17;
    assign coef[1][5] = IwCoeffsIn_21;
    assign coef[1][6] = IwCoeffsIn_25;
    assign coef[1][7] = IwCoeffsIn_29;

    assign coef[2][0] = IwCoeffsIn_2;
    assign coef[2][1] = IwCoeffsIn_6;
    assign coef[2][2] = IwCoeffsIn_10;
    assign coef[2][3] = IwCoeffsIn_14;
    assign coef[2][4] = IwCoeffsIn_18;
    assign coef[2][5] = IwCoeffsIn_22;
    assign coef[2][6] = IwCoeffsIn_26;
    assign coef[2][7] = IwCoeffsIn_30;

    assign coef[3][0] = IwCoeffsIn_3;
    assign coef[3][1] = IwCoeffsIn_7;
    assign coef[3][2] = IwCoeffsIn_11;
    assign coef[3][3] = IwCoeffsIn_15;
    assign coef[3][4] = IwCoeffsIn_19;
    assign coef[3][5] = IwCoeffsIn_23;
    assign coef[3][6] = IwCoeffsIn_27;
    assign coef[3][7] = IwCoeffsIn_31;

    // Products and sums per phase
    // Product of sfix2 (Q?) x sfix8_En7 -> signed 10-bit (max |2*-128| = 256 needs 10 bits; use 11 for accumulator)
    reg signed [10:0] acc [0:3];

    integer p, k;
    reg signed [10:0] sum;
    reg signed [10:0] prod;

    always @* begin
        for (p = 0; p < 4; p = p + 1) begin
            sum = 11'sd0;
            for (k = 0; k < 8; k = k + 1) begin
                prod = $signed(tap[k]) * $signed(coef[p][k]);
                sum = sum + prod;
            end
            acc[p] = sum;
        end
    end

    // Output registers with saturation (11-bit -> 8-bit)
    function signed [7:0] sat8;
        input signed [10:0] v;
        begin
            if (!v[10] && (v[9:7] != 3'b000))
                sat8 = 8'sb01111111;
            else if (v[10] && (v[9:7] != 3'b111))
                sat8 = 8'sb10000000;
            else
                sat8 = v[7:0];
        end
    endfunction

    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            OwSampleOut_0 <= 8'sd0;
            OwSampleOut_1 <= 8'sd0;
            OwSampleOut_2 <= 8'sd0;
            OwSampleOut_3 <= 8'sd0;
        end else if (enb) begin
            OwSampleOut_0 <= sat8(acc[0]);
            OwSampleOut_1 <= sat8(acc[1]);
            OwSampleOut_2 <= sat8(acc[1]);
            OwSampleOut_3 <= sat8(acc[3]);
        end
    end

}
