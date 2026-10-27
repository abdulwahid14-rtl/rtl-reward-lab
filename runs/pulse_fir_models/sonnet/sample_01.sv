module TopModule (
    input                    IwClk_500M,
    input                    IwRst_n_500M,
    input                    enb,
    input  signed [1:0]      IwPulseIn,
    input  signed [7:0]      IwCoeffsIn_0,  IwCoeffsIn_1,  IwCoeffsIn_2,  IwCoeffsIn_3,
    input  signed [7:0]      IwCoeffsIn_4,  IwCoeffsIn_5,  IwCoeffsIn_6,  IwCoeffsIn_7,
    input  signed [7:0]      IwCoeffsIn_8,  IwCoeffsIn_9,  IwCoeffsIn_10, IwCoeffsIn_11,
    input  signed [7:0]      IwCoeffsIn_12, IwCoeffsIn_13, IwCoeffsIn_14, IwCoeffsIn_15,
    input  signed [7:0]      IwCoeffsIn_16, IwCoeffsIn_17, IwCoeffsIn_18, IwCoeffsIn_19,
    input  signed [7:0]      IwCoeffsIn_20, IwCoeffsIn_21, IwCoeffsIn_22, IwCoeffsIn_23,
    input  signed [7:0]      IwCoeffsIn_24, IwCoeffsIn_25, IwCoeffsIn_26, IwCoeffsIn_27,
    input  signed [7:0]      IwCoeffsIn_28, IwCoeffsIn_29, IwCoeffsIn_30, IwCoeffsIn_31,
    output signed [7:0]      OwSampleOut_0,
    output signed [7:0]      OwSampleOut_1,
    output signed [7:0]      OwSampleOut_2,
    output signed [7:0]      OwSampleOut_3
);

    wire signed [7:0] c [0:31];
    assign c[0]=IwCoeffsIn_0;   assign c[1]=IwCoeffsIn_1;   assign c[2]=IwCoeffsIn_2;   assign c[3]=IwCoeffsIn_3;
    assign c[4]=IwCoeffsIn_4;   assign c[5]=IwCoeffsIn_5;   assign c[6]=IwCoeffsIn_6;   assign c[7]=IwCoeffsIn_7;
    assign c[8]=IwCoeffsIn_8;   assign c[9]=IwCoeffsIn_9;   assign c[10]=IwCoeffsIn_10; assign c[11]=IwCoeffsIn_11;
    assign c[12]=IwCoeffsIn_12; assign c[13]=IwCoeffsIn_13; assign c[14]=IwCoeffsIn_14; assign c[15]=IwCoeffsIn_15;
    assign c[16]=IwCoeffsIn_16; assign c[17]=IwCoeffsIn_17; assign c[18]=IwCoeffsIn_18; assign c[19]=IwCoeffsIn_19;
    assign c[20]=IwCoeffsIn_20; assign c[21]=IwCoeffsIn_21; assign c[22]=IwCoeffsIn_22; assign c[23]=IwCoeffsIn_23;
    assign c[24]=IwCoeffsIn_24; assign c[25]=IwCoeffsIn_25; assign c[26]=IwCoeffsIn_26; assign c[27]=IwCoeffsIn_27;
    assign c[28]=IwCoeffsIn_28; assign c[29]=IwCoeffsIn_29; assign c[30]=IwCoeffsIn_30; assign c[31]=IwCoeffsIn_31;

    reg signed [1:0] dly [1:7];
    wire signed [1:0] tap [0:7];
    assign tap[0] = IwPulseIn;
    genvar g;
    generate
        for (g = 1; g < 8; g = g + 1) begin : gt
            assign tap[g] = dly[g];
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

    reg signed [10:0] sum [0:3];
    reg signed [10:0] acc [0:3];
    integer p, k;
    always @* begin
        for (p = 0; p < 4; p = p + 1) begin
            sum[p] = 11'sd0;
            for (k = 0; k < 8; k = k + 1) begin
                sum[p] = sum[p] + ($signed({{3{c[p+4*k][7]}}, c[p+4*k]}) * $signed({{9{tap[k][1]}}, tap[k]}));
            end
        end
    end

    always @(posedge IwClk_500M or negedge IwRst_n_500M) begin
        if (!IwRst_n_500M) begin
            for (i = 0; i < 4; i = i + 1) acc[i] <= 11'sd0;
        end else if (enb) begin
            for (i = 0; i < 4; i = i + 1) acc[i] <= sum[i];
        end
    end

    function signed [7:0] sat;
        input signed [10:0] v;
        begin
            if (v[10:7] == 4'b0000 || v[10:7] == 4'b1111)
                sat = v[7:0];
            else if (v[10])
                sat = 8'sb10000000;
            else
                sat = 8'sb01111111;
        end
    endfunction

    assign OwSampleOut_0 = sat(acc[0]);
    assign OwSampleOut_1 = sat(acc[1]);
    assign OwSampleOut_2 = sat(acc[2]);
    assign OwSampleOut_3 = sat(acc[3]);

endmodule
