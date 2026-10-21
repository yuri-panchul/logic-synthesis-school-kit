// Exercise M11: a traffic light from a decade counter and OR gates,
// after Timofei Nikiforov's breadboard design.
//
// Generic version that matches schematic 1: five D flip-flops and gates,
// not tied to any chip.  Synthesizable.

module traffic_light
(
    input  logic       clk,
    input  logic       rst,     // 1 = go to state 0 at once, like RESET of the 4017

    output logic [9:0] q,       // q [k] = 1 in state k, like outputs Q0-Q9 of the 4017
    output logic       red,
    output logic       yellow,
    output logic       green
);

    //------------------------------------------------------------------------
    // State register: a 5-bit Johnson counter (twisted ring counter).
    // Every clock it shifts left and feeds the inverted top bit into bit 0:
    //
    // state  0     1     2     3     4     5     6     7     8     9
    // r      00000 00001 00011 00111 01111 11111 11110 11100 11000 10000
    //
    // Five flip-flops give ten states, and one bit changes per clock.

    logic [4:0] r;

    always_ff @ (posedge clk or posedge rst)
        if (rst)
            r <= '0;
        else
            r <= { r [3:0], ~ r [4] };

    //------------------------------------------------------------------------
    // Decoder: ten 2-input AND gates.  Two neighbouring bits identify each state.

    assign q [0] = ~ r [4] & ~ r [0];
    assign q [1] =   r [0] & ~ r [1];
    assign q [2] =   r [1] & ~ r [2];
    assign q [3] =   r [2] & ~ r [3];
    assign q [4] =   r [3] & ~ r [4];
    assign q [5] =   r [4] &   r [0];
    assign q [6] = ~ r [0] &   r [1];
    assign q [7] = ~ r [1] &   r [2];
    assign q [8] = ~ r [2] &   r [3];
    assign q [9] = ~ r [3] &   r [4];

    //------------------------------------------------------------------------
    // Output logic: OR gates

    assign red    = q [0] | q [1] | q [2] | q [3];  // 4 clock cycles
    assign yellow = q [4] | q [5];                  // 2 clock cycles
    assign green  = q [6] | q [7] | q [8] | q [9];  // 4 clock cycles

endmodule
