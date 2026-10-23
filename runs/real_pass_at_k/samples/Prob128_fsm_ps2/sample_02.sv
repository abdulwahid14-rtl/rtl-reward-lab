module TopModule(
    input        clk,
    input        reset,
    input  [7:0] in,
    output       done
);

    parameter BYTE1 = 2'b00;
    parameter BYTE2 = 2'b01;
    parameter BYTE3 = 2'b10;

    reg [1:0] state, next_state;
    reg       done_reg;

    always @(*) begin
        case (state)
            BYTE1: next_state = in[3] ? BYTE2 : BYTE1;
            BYTE2: next_state = BYTE3;
            BYTE3: next_state = BYTE1;
            default: next_state = BYTE1;
        endcase
    end

    always @(posedge clk) begin
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
