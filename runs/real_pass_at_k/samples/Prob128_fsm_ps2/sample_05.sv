module TopModule (
    input        clk,
    input        reset,
    input  [7:0] in,
    output       done
);

    reg [1:0] count;
    reg       done_r;

    always @(posedge clk) begin
        if (reset) begin
            count  <= 2'd0;
            done_r <= 1'b0;
        end else begin
            done_r <= 1'b0;
            case (count)
                2'd0: begin
                    if (in[3]) begin
                        count <= 2'd1;
                    end else begin
                        count <= 2'd0;
                    end
                end
                2'd1: begin
                    count <= 2'd2;
                end
                2'd2: begin
                    count  <= 2'd0;
                    done_r <= 1'b1;
                end
                default: begin
                    count <= 2'd0;
                end
            endcase
        end
    end

    assign done = done_r;

endmodule
