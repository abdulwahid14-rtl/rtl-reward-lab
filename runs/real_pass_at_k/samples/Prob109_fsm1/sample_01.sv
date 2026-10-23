module TopModule (
    input  clk,
    input  areset,
    input  in,
    output out
);

    reg state;
    localparam A = 1'b0, B = 1'b1;

    always @(posedge clk, posedge areset) begin
        if (areset)
            state <= B;
        else begin
            case (state)
                A: state <= in ? A : B;
                B: state <= in ? B : A;
            endcase
        end
    end

    assign out = state;

endmodule
