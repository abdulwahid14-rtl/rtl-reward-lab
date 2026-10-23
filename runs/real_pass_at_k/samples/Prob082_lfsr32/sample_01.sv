module TopModule (
    input  clk,
    input  reset,
    output [31:0] q
);

    reg [31:0] q_reg;
    assign q = q_reg;

    always @(posedge clk) begin
        if (reset)
            q_reg <= 32'h1;
        else begin
            q_reg[30] <= q_reg[31] ^ q_reg[0];
            q_reg[21] <= q_reg[22] ^ q_reg[0];
            q_reg[1]  <= q_reg[2]  ^ q_reg[0];
            q_reg[0]  <= q_reg[1]  ^ q_reg[0];

            q_reg[31] <= q_reg[0];
            q_reg[29:22] <= q_reg[30:23];
            q_reg[20:2]  <= q_reg[21:3];
        end
    end

endmodule
