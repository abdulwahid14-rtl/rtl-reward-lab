module TopModule (
    input        clk,
    input        reset,
    input  [7:0] in,
    output       done
);

    localparam S0 = 2'd0,
               S1 = 2'd1,
               S2 = 2'd2;

    reg [1:0] state;
    reg       doneR;

    always @(posedge clk) begin
        if (reset) begin
            state <= S0;
            doneR <= 1'b0;
        end else begin
            case (state)
                S0: begin
                    if (in[3])
                        state <= S1;
                    else
                        state <= S0;
                    doneR <= 1'b0;
                end
                S1: begin
                    state <= S2;
                    doneR <= 1'b0;
                end
                S2: begin
                    state <= S0;
                    doneR <= 1'b1;
                end
                default: begin
                    state <= S0;
                    doneR <= 1'b0;
                end
            endcase
        end
    end

    assign done = doneR;

endmodule
