module TopModule (
    input  clk,
    input  d,
    output q
);
    reg q;

    always @(posedge clk) begin
        q <= d;
    end

endmodule
