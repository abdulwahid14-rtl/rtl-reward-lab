module TopModule (
    input wire IwClk_500M,
    input wire IwRst_n_500M,
    input wire enb,
    input wire signed [1:0] IwPulseIn,
    input wire signed [7:0] IwCoeffsIn_0,
    input wire signed [7:0] IwCoeffsIn_1,
    input wire signed [7:0] IwCoeffsIn_2,
    input wire signed [7:0] IwCoeffsIn_3,
    input wire signed [7:0] IwCoeffsIn_4,
    input wire signed [7:0] IwCoeffsIn_5,
    input wire signed [7:0] IwCoeffsIn_6,
    input wire signed [7:0] IwCoeffsIn_7,
    input wire signed [7:0] IwCoeffsIn_8,
    input wire signed [7:0] IwCoeffsIn_9,
    input wire signed [7:0] IwCoeffsIn_10,
    input wire signed [7:0] IwCoeffsIn_11,
    input wire signed [7:0] IwCoeffsIn_12,
    input wire signed [7:0] IwCoeffsIn_13,
    input wire signed [7:0] IwCoeffsIn_14,
    input wire signed [7:0] IwCoeffsIn_15,
    input wire signed [7:0] IwCoeffsIn_16,
    input wire signed [7:0] IwCoeffsIn_17,
    input wire signed [7:0] IwCoeffsIn_18,
    input wire signed [7:0] IwCoeffsIn_19,
    input wire signed [7:0] IwCoeffsIn_20,
    input wire signed [7:0] IwCoeffsIn_21,
    input wire signed [7:0] IwCoeffsIn_22,
    input wire signed [7:0] IwCoeffsIn_23,
    input wire signed [7:0] IwCoeffsIn_24,
    input wire signed [7:0] IwCoeffsIn_25,
    input wire signed [7:0] IwCoeffsIn_26,
    input wire signed [7:0] IwCoeffsIn_27,
    input wire signed [7:0] IwCoeffsIn_28,
    input wire signed [7:0] IwCoeffsIn_29,
    input wire signed [7:0] IwCoeffsIn_30,
    input wire signed [7:0] IwCoeffsIn_31,
    output wire signed [7:0] OwSampleOut_0,
    output wire signed [7:0] OwSampleOut_1,
    output wire signed [7:0] OwSampleOut_2,
    output wire signed [7:0] OwSampleOut_3
);

    wire signed [7:0] coeff [0:31];
    reg signed [1:0] history [0:6];
    reg signed [10:0] sum [0:3];
    reg signed [10:0] acc [0:3];

    assign coeff[0]  = IwCoeffsIn_0;
    assign coeff[1]  = IwCoeffsIn_1;
    assign coeff[2]  = IwCoeffsIn_2;
    assign coeff[3]  = IwCoeffsIn_3;
    assign coeff[4]  = IwCoeffsIn_4;
    assign coeff[5]  = IwCoeffsIn_5;
    assign coeff[6]  = IwCoeffsIn_6;
    assign coeff[7]  = IwCoeffsIn_7;
    assign coeff[8]  = IwCoeffsIn_8;
    assign coeff[9]  = IwCoeffsIn_9;
    assign coeff[10] = IwCoeffsIn_10;
    assign coeff[11] = IwCoeffsIn_11;
    assign coeff[12] = IwCoeffsIn_12;
    assign coeff[13] = IwCoeffsIn_13;
    assign coeff[14] = IwCoeffsIn_14;
    assign coeff[15] = IwCoeffsIn_15;
    assign coeff[16] = IwCoeffsIn_16;
    assign coeff[17] = IwCoeffsIn_17;
    assign coeff[18] = IwCoeffsIn_18;
    assign coeff[19] = IwCoeffsIn_19;
    assign coeff[20] = IwCoeffsIn_20;
    assign coeff[21] = IwCoeffsIn_21;
    assign coeff[22] = IwCoeffsIn_22;
    assign coeff[23] = IwCoeffsIn_23;
    assign coeff[24] = IwCoeffsIn_24;
    assign coeff[25] = IwCoeffsIn_25;
    assign coeff[26] = IwCoeffsIn_26;
    assign coeff[27] = IwCoeffsIn_27;
    assign coeff[28] = IwCoeffsIn_28;
    assign coeff[29] = IwCoeffsIn_29;
    assign coeff[30] = IwCoeffsIn_30;
    assign coeff[31] = IwCoeffsIn_31;

    function automatic signed [10:0] tap_product;
        input signed [1:0] sample;
        input signed [7:0] coefficient;
        reg signed [10:0] extended_coeff;
        begin
            extended_coeff = {{3{coefficient[7]}}, coefficient};
            case (sample)
                2'sb01: tap_product = extended_coeff;
                2'sb11: tap_product = -extended_coeff;
                default: tap_product = 11'sd0;
            endcase
        end
    endfunction

    function automatic signed [7:0] saturate;
        input signed [10:0] value;
        begin
            if (value > 11'sd127)
                saturate = 8'sb01111111;
            else if (value < -11'sd128)
                saturate = 8'sb10000000;
            else
                saturate = value[7:0];
        end
    endfunction

    integer p, t;
    always @* begin
        for (p = 0; p < 4; p = p + 1) begin
            sum[p] = tap_product(IwPulseIn, coeff[p]);
            for (t = 1; t < 8; t = t + 1)
                sum[p] = sum[p] + tap_product(history[t-1], coeff[p + 4*t]);
        end
    end

    integer i;
    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            for (i = 0; i < 7; i = i + 1)
                history[i] <= 2'sd0;
            for (i = 0; i < 4; i = i + 1)
                acc[i] <= 11'sd0;
        end else if (enb) begin
            history[0] <= IwPulseIn;
            for (i = 1; i < 7; i = i + 1)
                history[i] <= history[i-1];
            for (i = 0; i < 4; i = i + 1)
                acc[i] <= sum[i];
        end
    end

    assign OwSampleOut_0 = saturate(acc[0]);
    assign OwSampleOut_1 = saturate(acc[1]);
    assign OwSampleOut_2 = saturate(acc[2]);
    assign OwSampleOut_3 = saturate(acc[3]);

endmodule
