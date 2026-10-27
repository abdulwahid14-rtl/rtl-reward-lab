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

    reg signed [1:0] delay1, delay2, delay3, delay4;
    reg signed [1:0] delay5, delay6, delay7;

    wire [255:0] coeff_bus = {
        IwCoeffsIn_31, IwCoeffsIn_30, IwCoeffsIn_29, IwCoeffsIn_28,
        IwCoeffsIn_27, IwCoeffsIn_26, IwCoeffsIn_25, IwCoeffsIn_24,
        IwCoeffsIn_23, IwCoeffsIn_22, IwCoeffsIn_21, IwCoeffsIn_20,
        IwCoeffsIn_19, IwCoeffsIn_18, IwCoeffsIn_17, IwCoeffsIn_16,
        IwCoeffsIn_15, IwCoeffsIn_14, IwCoeffsIn_13, IwCoeffsIn_12,
        IwCoeffsIn_11, IwCoeffsIn_10, IwCoeffsIn_9,  IwCoeffsIn_8,
        IwCoeffsIn_7,  IwCoeffsIn_6,  IwCoeffsIn_5,  IwCoeffsIn_4,
        IwCoeffsIn_3,  IwCoeffsIn_2,  IwCoeffsIn_1,  IwCoeffsIn_0
    };

    wire signed [7:0] coeffs [0:31];
    wire signed [1:0] taps [0:7];

    genvar c;
    generate
        for (c = 0; c < 32; c = c + 1) begin : GEN_COEFFS
            assign coeffs[c] = $signed(coeff_bus[c*8 +: 8]);
        end
    endgenerate

    assign taps[0] = IwPulseIn;
    assign taps[1] = delay1;
    assign taps[2] = delay2;
    assign taps[3] = delay3;
    assign taps[4] = delay4;
    assign taps[5] = delay5;
    assign taps[6] = delay6;
    assign taps[7] = delay7;

    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            delay1 <= 2'sd0;
            delay2 <= 2'sd0;
            delay3 <= 2'sd0;
            delay4 <= 2'sd0;
            delay5 <= 2'sd0;
            delay6 <= 2'sd0;
            delay7 <= 2'sd0;
        end else if (enb) begin
            delay1 <= IwPulseIn;
            delay2 <= delay1;
            delay3 <= delay2;
            delay4 <= delay3;
            delay5 <= delay4;
            delay6 <= delay5;
            delay7 <= delay6;
        end
    end

    reg signed [10:0] accum [0:3];
    integer p;
    integer k;

    always @* begin
        for (p = 0; p < 4; p = p + 1)
            accum[p] = 11'sd0;

        for (k = 0; k < 8; k = k + 1) begin
            for (p = 0; p < 4; p = p + 1) begin
                case (taps[k])
                    2'sb01:
                        accum[p] = accum[p] +
                                   $signed({{3{coeffs[k*4+p][7]}}, coeffs[k*4+p]});
                    2'sb11:
                        accum[p] = accum[p] -
                                   $signed({{3{coeffs[k*4+p][7]}}, coeffs[k*4+p]});
                    default:
                        accum[p] = accum[p];
                endcase
            end
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

    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            OwSampleOut_0 <= 8'sd0;
            OwSampleOut_1 <= 8'sd0;
            OwSampleOut_2 <= 8'sd0;
            OwSampleOut_3 <= 8'sd0;
        end else if (enb) begin
            OwSampleOut_0 <= saturate(accum[0]);
            OwSampleOut_1 <= saturate(accum[1]);
            OwSampleOut_2 <= saturate(accum[2]);
            OwSampleOut_3 <= saturate(accum[3]);
        end
    end

endmodule
