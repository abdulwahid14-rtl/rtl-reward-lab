module TopModule (
    input        clk,
    input        reset,
    input  [7:0] in,
    output       done
);

    reg [1:0] state;
    reg       done_reg;

    localparam BYTE1 = 2'd0;
    localparam BYTE2 = 2'd1;
    localparam BYTE3 = 2'd2;

    always @(posedge clk) begin
        if (reset) begin
            state    <= BYTE1;
            done_reg <= 1'b0;
        end else begin
            case (state)
                BYTE1: begin
                    if (in[3])
                        state <= BYTE2;
                    else
                        state <= BYTE1;
                    done_reg <= 1'b0;
                end
                BYTE2: begin
                    state    <= BYTE3;
                    done_reg <= 1'b0;
                end
                BYTE3: begin
                    state    <= BYTE1;
                    done_reg <= 1'b1;
                end
                default: begin
                    state    <= BYTE1;
                    done_reg <= 1'b0;
                end
            endcase
        end
    end

    assign done = done_reg;

endmodule
