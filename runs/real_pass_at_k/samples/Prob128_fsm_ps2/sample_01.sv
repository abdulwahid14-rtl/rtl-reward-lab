module TopModule (
    input        clk,
    input        reset,
    input  [7:0] in,
    output       done
);

    typedef enum logic [1:0] {
        BYTE1 = 2'd0,
        BYTE2 = 2'd1,
        BYTE3 = 2'd2
    } state_t;

    state_t state, next_state;
    logic done_reg;

    always_comb begin
        case (state)
            BYTE1: next_state = in[3] ? BYTE2 : BYTE1;
            BYTE2: next_state = BYTE3;
            BYTE3: next_state = BYTE1;
            default: next_state = BYTE1;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state    <= BYTE1;
            done_reg <= 1'b0;
        end else begin
            state    <= next_state;
            done_reg <= (state == BYTE3);
        end
    end

    assign done = done_reg;

endmodule
