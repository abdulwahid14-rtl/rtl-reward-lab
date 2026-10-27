module TopModule (
    input  wire              IwClk_500M,
    input  wire              IwRst_n_500M,
    input  wire              enb,
    input  wire signed [1:0] IwPulseIn,
    input  wire signed [7:0] IwCoeffsIn_0,
    input  wire signed [7:0] IwCoeffsIn_1,
    input  wire signed [7:0] IwCoeffsIn_2,
    input  wire signed [7:0] IwCoeffsIn_3,
    input  wire signed [7:0] IwCoeffsIn_4,
    input  wire signed [7:0] IwCoeffsIn_5,
    input  wire signed [7:0] IwCoeffsIn_6,
    input  wire signed [7:0] IwCoeffsIn_7,
    input  wire signed [7:0] IwCoeffsIn_8,
    input  wire signed [7:0] IwCoeffsIn_9,
    input  wire signed [7:0] IwCoeffsIn_10,
    input  wire signed [7:0] IwCoeffsIn_11,
    input  wire signed [7:0] IwCoeffsIn_12,
    input  wire signed [7:0] IwCoeffsIn_13,
    input  wire signed [7:0] IwCoeffsIn_14,
    input  wire signed [7:0] IwCoeffsIn_15,
    input  wire signed [7:0] IwCoeffsIn_16,
    input  wire signed [7:0] IwCoeffsIn_17,
    input  wire signed [7:0] IwCoeffsIn_18,
    input  wire signed [7:0] IwCoeffsIn_19,
    input  wire signed [7:0] IwCoeffsIn_20,
    input  wire signed [7:0] IwCoeffsIn_21,
    input  wire signed [7:0] IwCoeffsIn_22,
    input  wire signed [7:0] IwCoeffsIn_23,
    input  wire signed [7:0] IwCoeffsIn_24,
    input  wire signed [7:0] IwCoeffsIn_25,
    input  wire signed [7:0] IwCoeffsIn_26,
    input  wire signed [7:0] IwCoeffsIn_27,
    input  wire signed [7:0] IwCoeffsIn_28,
    input  wire signed [7:0] IwCoeffsIn_29,
    input  wire signed [7:0] IwCoeffsIn_30,
    input  wire signed [7:0] IwCoeffsIn_31,
    output wire signed [7:0] OwSampleOut_0,
    output wire signed [7:0] OwSampleOut_1,
    output wire signed [7:0] OwSampleOut_2,
    output wire signed [7:0] OwSampleOut_3
);

    wire signed [7:0] coeff [0:31];
    wire signed [1:0] tap [0:7];
    reg  signed [1:0] history [1:7];
    reg  signed [10:0] phase_sum [0:3];
    reg  signed [10:0] phase_acc [0:3];

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

    assign tap[0] = IwPulseIn;

    genvar g;
    generate
        for (g = 1; g < 8; g = g + 1) begin : gen_taps
            assign tap[g] = history[g];
        end
    endgenerate

    integer p;
    integer t;
    always @* begin
        for (p = 0; p < 4; p = p + 1) begin
            phase_sum[p] = 11'sd0;
            for (t = 0; t < 8; t = t + 1) begin
                case (tap[t])
                    2'b01:
                        phase_sum[p] = phase_sum[p] +
                            $signed({{3{coeff[p + 4*t][7]}},
                                     coeff[p + 4*t]});
                    2'b11:
                        phase_sum[p] = phase_sum[p] -
                            $signed({{3{coeff[p + 4*t][7]}},
                                     coeff[p + 4*t]});
                    default:
                        phase_sum[p] = phase_sum[p];
                endcase
            end
        end
    end

    integer i;
    integer j;
    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            for (i = 1; i < 8; i = i + 1)
                history[i] <= 2'sd0;
            for (j = 0; j < 4; j = j + 1)
                phase_acc[j] <= 11'sd0;
        end else if (enb) begin
            history[1] <= IwPulseIn;
            for (i = 2; i < 8; i = i + 1)
                history[i] <= history[i-1];
            for (j = 0; j < 4; j = j + 1)
                phase_acc[j] <= phase_sum[j];
        end
    end

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

    assign OwSampleOut_0 = saturate(phase_acc[0]);
    assign OwSampleOut_1 = saturate(phase_acc[1]);
    assign OwSampleOut_2 = saturate(phase_acc[2]);
    assign OwSampleOut_3 = saturate(phase_acc[3]);

endmodule
