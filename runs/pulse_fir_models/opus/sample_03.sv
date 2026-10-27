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

    // Coefficient array
    wire signed [7:0] c [0:31];
    assign c[0]  = IwCoeffsIn_0;   assign c[1]  = IwCoeffsIn_1;
    assign c[2]  = IwCoeffsIn_2;   assign c[3]  = IwCoeffsIn_3;
    assign c[4]  = IwCoeffsIn_4;   assign c[5]  = IwCoeffsIn_5;
    assign c[6]  = IwCoeffsIn_6;   assign c[7]  = IwCoeffsIn_7;
    assign c[8]  = IwCoeffsIn_8;   assign c[9]  = IwCoeffsIn_9;
    assign c[10] = IwCoeffsIn_10;  assign c[11] = IwCoeffsIn_11;
    assign c[12] = IwCoeffsIn_12;  assign c[13] = IwCoeffsIn_13;
    assign c[14] = IwCoeffsIn_14;  assign c[15] = IwCoeffsIn_15;
    assign c[16] = IwCoeffsIn_16;  assign c[17] = IwCoeffsIn_17;
    assign c[18] = IwCoeffsIn_18;  assign c[19] = IwCoeffsIn_19;
    assign c[20] = IwCoeffsIn_20;  assign c[21] = IwCoeffsIn_21;
    assign c[22] = IwCoeffsIn_22;  assign c[23] = IwCoeffsIn_23;
    assign c[24] = IwCoeffsIn_24;  assign c[25] = IwCoeffsIn_25;
    assign c[26] = IwCoeffsIn_26;  assign c[27] = IwCoeffsIn_27;
    assign c[28] = IwCoeffsIn_28;  assign c[29] = IwCoeffsIn_29;
    assign c[30] = IwCoeffsIn_30;  assign c[31] = IwCoeffsIn_31;

    // Delay line: tap 0 combinational, taps 1..7 registered
    reg  signed [1:0] dly [1:7];
    wire signed [1:0] tap [0:7];
    assign tap[0] = IwPulseIn;
    genvar g;
    generate
        for (g = 1; g < 8; g = g + 1) begin : g_tap
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

    // Polyphase accumulation
    reg signed [12:0] full [0:3];
    reg signed [10:0] acc  [0:3];
    reg signed [7:0]  sat  [0:3];
    integer p, k;
    always @* begin
        for (p = 0; p < 4; p = p + 1) begin
            full[p] = 13'sd0;
            for (k = 0; k < 8; k = k + 1)
                full[p] = full[p] + ($signed(tap[k]) * $signed(c[p + 4*k]));
            acc[p] = full[p][10:0];
            if (acc[p] > 11'sd127)
                sat[p] = 8'sb01111111;
            else if (acc[p] < -11'sd128)
                sat[p] = 8'sb10000000;
            else
                sat[p] = acc[p][7:0];
        end
    end

    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            OwSampleOut_0 <= 8'sd0;
            OwSampleOut_1 <= 8'sd0;
            OwSampleOut_2 <= 8'sd0;
            OwSampleOut_3 <= 8'sd0;
        end else if (enb) begin
            OwSampleOut_0 <= sat[0];
            OwSampleOut_1 <= sat[1];
            OwSampleOut_2 <= sat[2];
            OwSampleOut_3 <= sat[3];
        end
    end

endmodule
