`timescale 1ns / 1ps
`default_nettype none

// Synthesizable generic FSM. The state output uses one-hot encoding.
// Reset is asynchronous and active high; it selects S0.

module traffic_light
(
    input  wire       clk,
    input  wire       rst,

    output wire       red,
    output wire       yellow,
    output wire       green,
    output logic [9:0] state
);

    wire [9:0] next_state = { state [8:0], state [9] };

    // State register

    always_ff @ (posedge clk or posedge rst)
        if (rst)
            state <= 10'b00_0000_0001;
        else
            state <= next_state;

    // Moore outputs depend only on the current state.

    assign red    = | state [3:0];
    assign yellow = | state [5:4];
    assign green  = | state [9:6];

endmodule

`default_nettype wire
