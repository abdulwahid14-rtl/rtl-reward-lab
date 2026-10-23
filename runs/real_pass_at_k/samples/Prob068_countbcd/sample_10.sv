module TopModule (
    input        clk,
    input        reset,
    output [2:0] ena,
    output [15:0] q
);

    reg [3:0] d0, d1, d2, d3;

    always @(posedge clk) begin
        if (reset) begin
            d0 <= 4'd0;
            d1 <= 4'd0;
            d2 <= 4'd0;
            d3 <= 4'd0;
        end else begin
            if (d0 == 4'd9) begin
                d0 <= 4'd0;
            end else begin
                d0 <= d0 + 4'd1;
            end

            if (d0 == 4'd9) begin
                if (d1 == 4'd9) begin
                    d1 <= 4'd0;
                end else begin
                    d1 <= d1 + 4'd1;
                end
            end

            if (d0 == 4'd9 && d1 == 4'd9) begin
                if (d2 == 4'd9) begin
                    d2 <= 4'd0;
                end else begin
                    d2 <= d2 + 4'd1;
                end
            end

            if (d0 == 4'd9 && d1 == 4'd9 && d2 == 4'd9) begin
                if (d3 == 4'd9) begin
                    d3 <= 4'd0;
                end else begin
                    d3 <= d3 + 4'd1;
                end
            end
        end
    end

    assign ena[0] = (d0 == 4'd9);
    assign ena[1] = (d0 == 4'd9) && (d1 == 4'd9);
    assign ena[2] = (d0 == 4'd9) && (d1 == 4'd9) && (d2 == 4'd9);

    assign q = {d3, d2, d1, d0};

endmodule
