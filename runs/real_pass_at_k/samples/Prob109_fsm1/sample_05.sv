module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

    typedef enum logic { A, B } state_t;
    state_t state, next_state;

    always_comb begin
        case (state)
            A: next_state = in ? A : B;
            B: next_state = in ? B : A;
            default: next_state = B;
        endcase
    end

    always_ff @(posedge clk, posedge areset) begin
        if (areset)
            state <= B;
        else
            state <= next_state;
    end

    assign out = (state == B);

endmodule
