module TopModule (
    input        clk,
    input        reset,
    input  [7:0] in,
    output       done
);

    typedef enum logic [1:0] {BYTE1, BYTE2, BYTE3, DONE} state_t;
    state_t state, next_state;

    always_ff_block: always @(posedge clk) begin
        if (reset)
            state <= BYTE1;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            BYTE1: next_state = in[3] ? BYTE2 : BYTE1;
            BYTE2: next_state = BYTE3;
            BYTE3: next_state = DONE;
            DONE:  next_state = in[3] ? BYTE2 : BYTE1;
            default: next_state = BYTE1;
        endcase
    end

    assign done = (state == DONE);

endmodule
