module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [7:0] in,
    output logic        done
);

    typedef enum logic [1:0] {
        WAIT_BYTE1 = 2'd0,
        WAIT_BYTE2 = 2'd1,
        WAIT_BYTE3 = 2'd2
    } state_t;

    state_t state;

    always_ff @(posedge clk) begin
        if (reset) begin
            state <= WAIT_BYTE1;
            done  <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                WAIT_BYTE1: begin
                    if (in[3])
                        state <= WAIT_BYTE2;
                    else
                        state <= WAIT_BYTE1;
                end

                WAIT_BYTE2: begin
                    state <= WAIT_BYTE3;
                end

                WAIT_BYTE3: begin
                    state <= WAIT_BYTE1;
                    done  <= 1'b1;
                end

                default: begin
                    state <= WAIT_BYTE1;
                end
            endcase
        end
    end

endmodule
