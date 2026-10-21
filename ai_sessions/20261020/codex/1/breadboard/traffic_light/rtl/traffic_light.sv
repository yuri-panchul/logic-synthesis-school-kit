`timescale 1ns/1ps
`default_nettype none
// Synthesizable generic FSM. State is a one-hot vector, not a decimal pin number.
module traffic_light (
    input  wire       clk,
    input  wire       rst,       // asynchronous, active high; reset selects S0
    output wire       red,
    output wire       yellow,
    output wire       green,
    output reg  [9:0] state
);
    always @(posedge clk or posedge rst)
        if (rst)
            state <= 10'b0000000001;
        else
            state <= {state[8:0], state[9]};

    assign red    = |state[3:0];
    assign yellow = |state[5:4];
    assign green  = |state[9:6];
endmodule
`default_nettype wire
