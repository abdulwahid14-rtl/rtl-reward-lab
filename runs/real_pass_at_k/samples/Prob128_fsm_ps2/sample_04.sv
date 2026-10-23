module TopModule (
    input  logic       clk,
    input  logic        reset,
    input  logic [7:0]  in,
    output logic        done
);

    typedef enum logic [1:0] {
        WAIT  = 2'd0,
        BYTE2 = 2'd1,
        BYTE3 = 2'd2,
        DONE  = 2'd3
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            WAIT:  next_state = in[3] ? BYTE2 : WAIT;
            BYTE2: next_state = BYTE3;
            BYTE3: next_state = DONE;
            DONE:  next_state = in[3] ? BYTE2 : WAIT;
            default: next_state = WAIT;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            state <= WAIT;
        else
            state <= next_state;
    end

    assign done = (state == DONE);

endmodule
