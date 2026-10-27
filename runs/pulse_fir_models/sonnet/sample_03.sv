module TopModule (
    input  wire               IwClk_500M,
    input  wire               IwRst_n_500M,
    input  wire               enb,
    input  wire signed [1:0]  IwPulseIn,
    input  wire signed [7:0]  IwCoeffsIn_0,
    input  wire signed [7:0]  IwCoeffsIn_1,
    input  wire signed [7:0]  IwCoeffsIn_2,
    input  wire signed [7:0]  IwCoeffsIn_3,
    input  wire signed [7:0]  IwCoeffsIn_4,
    input  wire signed [7:0]  IwCoeffsIn_5,
    input  wire signed [7:0]  IwCoeffsIn_6,
    input  wire signed [7:0]  IwCoeffsIn_7,
    input  wire signed [7:0]  IwCoeffsIn_8,
    input  wire signed [7:0]  IwCoeffsIn_9,
    input  wire signed [7:0]  IwCoeffsIn_10,
    input  wire signed [7:0]  IwCoeffsIn_11,
    input  wire signed [7:0]  IwCoeffsIn_12,
    input  wire signed [7:0]  IwCoeffsIn_13,
    input  wire signed [7:0]  IwCoeffsIn_14,
    input  wire signed [7:0]  IwCoeffsIn_15,
    input  wire signed [7:0]  IwCoeffsIn_16,
    input  wire signed [7:0]  IwCoeffsIn_17,
    input  wire signed [7:0]  IwCoeffsIn_18,
    input  wire signed [7:0]  IwCoeffsIn_19,
    input  wire signed [7:0]  IwCoeffsIn_20,
    input  wire signed [7:0]  IwCoeffsIn_21,
    input  wire signed [7:0]  IwCoeffsIn_22,
    input  wire signed [7:0]  IwCoeffsIn_23,
    input  wire signed [7:0]  IwCoeffsIn_24,
    input  wire signed [7:0]  IwCoeffsIn_25,
    input  wire signed [7:0]  IwCoeffsIn_26,
    input  wire signed [7:0]  IwCoeffsIn_27,
    input  wire signed [7:0]  IwCoeffsIn_28,
    input  wire signed [7:0]  IwCoeffsIn_29,
    input  wire signed [7:0]  IwCoeffsIn_30,
    input  wire signed [7:0]  IwCoeffsIn_31,
    output wire signed [7:0]  OwSampleOut_0,
    output wire signed [7:0]  OwSampleOut_1,
    output wire signed [7:0]  OwSampleOut_2,
    output wire signed [7:0]  OwSampleOut_3
);

    wire signed [7:0] c [0:31];
    assign c[0]  = IwCoeffsIn_0;  assign c[1]  = IwCoeffsIn_1;
    assign c[2]  = IwCoeffsIn_2;  assign c[3]  = IwCoeffsIn_3;
    assign c[4]  = IwCoeffsIn_4;  assign c[5]  = IwCoeffsIn_5;
    assign c[6]  = IwCoeffsIn_6;  assign c[7]  = IwCoeffsIn_7;
    assign c[8]  = IwCoeffsIn_8;  assign c[9]  = IwCoeffsIn_9;
    assign c[10] = IwCoeffsIn_10; assign c[11] = IwCoeffsIn_11;
    assign c[12] = IwCoeffsIn_12; assign c[13] = IwCoeffsIn_13;
    assign c[14] = IwCoeffsIn_14; assign c[15] = IwCoeffsIn_15;
    assign c[16] = IwCoeffsIn_16; assign c[17] = IwCoeffsIn_17;
    assign c[18] = IwCoeffsIn_18; assign c[19] = IwCoeffsIn_19;
    assign c[20] = IwCoeffsIn_20; assign c[21] = IwCoeffsIn_21;
    assign c[22] = IwCoeffsIn_22; assign c[23] = IwCoeffsIn_23;
    assign c[24] = IwCoeffsIn_24; assign c[25] = IwCoeffsIn_25;
    assign c[26] = IwCoeffsIn_26; assign c[27] = IwCoeffsIn_27;
    assign c[28] = IwCoeffsIn_28; assign c[29] = IwCoeffsIn_29;
    assign c[30] = IwCoeffsIn_30; assign c[31] = IwCoeffsIn_31;

    reg signed [1:0] dly [1:7];
    wire signed [1:0] tap [0:7];
    assign tap[0] = IwPulseIn;
    genvar t;
    generate
        for (t = 1; t < 8; t = t + 1) begin : g_tap
            assign tap[t] = dly[t];
        end
    endgenerate

    integer i;
    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            for (i = 1; i < 8; i = i + 1) dly[i] <= 2'sd0;
        end else if (enb) begin
            dly[1] <= IwPulseIn;
            for (i = 2; i < 8; i = i + 1) dly[i] <= dly[i-1];
        end
    end

    reg signed [10:0] acc [0:3];
    reg signed [7:0]  outr [0:3];
    reg signed [10:0] s;
    integer p, k;

    reg signed [10:0] accn [0:3];
    always @* begin
        for (p = 0; p < 4; p = p + 1) begin
            s = 11'sd0;
            for (k = 0; k < 8; k = k + 1)
                s = s + ($signed(c[p + 4*k]) * $signed(tap[k]));
            accn[p] = s;
        end
    end

    function signed [7:0] sat;
        input signed [10:0] v;
        begin
            if (!v[10] && (|v[9:7]))
                sat = 8'sb01111111;
            else if (v[10] && !(&v[9:7]))
                sat = 8'sb10000000;
            else
                sat = v[7:0];
        end
    endfunction

    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            for (p = 0; p < 4; p = p + 1) outr[p] <= 8'sd0;
        end else if (enb) begin
            for (p = 0; p < 4; p = p + 1) outr[p] <= sat(accn[p]);
        end
    end

    assign OwSampleOut_0 = outr[0];
    assign OwSampleOut_1 = outr[1];
    assign OwSampleOut_2 = outr[2];
    assign OwSampleOut_3 = outr[3];

endmodule
