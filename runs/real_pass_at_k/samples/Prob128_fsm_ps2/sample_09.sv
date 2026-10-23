module TopModule (
    input        clk,
    input        reset,
    input  [7:0] in,
    output       done
);

    localparam S_BYTE1 = 2'd0,
               S_BYTE2 = 2'd1,
               S_BYTE3 = 2'd2;

    reg [1:0] state, next_state;
    reg       done_reg;

    always @(*) begin
        case (state)
            S_BYTE1: next_state = in[3] ? S_BYTE2 : S_BYTE1;
            S_BYTE2: next_state = S_BYTE3;
            S_BYTE3: next_state = S_BYTE1;
            default: next_state = S_BYTE1;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            state    <= S_BYTE1;
            done_reg <= 1'b0;
        end else begin
            state    <= next_state;
            done_reg <= (state == S_BYTE3);
        end
    end

    assign done = done_reg;

endmodule
