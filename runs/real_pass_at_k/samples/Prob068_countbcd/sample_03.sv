module TopModule (
    input        clk,
    input        reset,
    output [2:0] ena,
    output [15:0] q
);

    reg [3:0] d0, d1, d2, d3;

    assign q = {d3, d2, d1, d0};
    assign ena[0] = (d0 == 4'd9);
    assign ena[1] = ena[0] & (d1 == 4'd9);
    assign ena[2] = ena[1] & (d2 == 4'd9);

    always @(posedge clk) begin
        if (reset) begin
            d0 <= 4'd0;
            d1 <= 4'd0;
            d2 <= 4'd0;
            d3 <= 4'd0;
        end else begin
            if (d0 == 4'd9)
                d0 <= 4'd0;
            else
                d0 <= d0 + 4'd1;

            if (ena[0]) begin
                if (d1 == 4'd9)
                    d1 <= 4'd0;
                else
                    d1 <= d1 + 4'd1;
            end

            if (ena[1]) begin
                if (d2 == 4'd9)
                    d2 <= 4'd0;
                else
                    d2 <= d2 + 4'd1;
            end

            if (ena[2]) begin
                if (d3 == 4'd9)
                    d3 <= 4'd0;
                else
                    d3 <= d3 + 4'd1;
            end
        end
    end

endmodule
