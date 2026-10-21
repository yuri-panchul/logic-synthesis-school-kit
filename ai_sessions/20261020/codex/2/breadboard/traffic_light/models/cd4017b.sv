`timescale 1ns / 1ps
`default_nettype none

// Synthesizable, zero-delay functional model of a powered CD4017B.
// Physical supply pins: 16 = VDD, 8 = VSS; they are not HDL ports.
// Binary encoding abstracts the chip's five-stage Johnson counter.
// Reset is required. Illegal Johnson-state recovery and electrical effects
// (current, setup/hold, pulse width and propagation delay) are not modeled.

module cd4017b
(
    input  wire p14_clock,
    input  wire p13_inhibit,
    input  wire p15_reset,

    output wire p3_q0,
    output wire p2_q1,
    output wire p4_q2,
    output wire p7_q3,
    output wire p10_q4,
    output wire p1_q5,
    output wire p5_q6,
    output wire p6_q7,
    output wire p9_q8,
    output wire p11_q9,
    output wire p12_carry
);

    // Falling INHIBIT while CLOCK is high is also a count event.
    // INHIBIT is tied low in this exercise, so synthesis removes the gate.
    // This models the chip; it is not a recommendation to gate FPGA clocks.

    wire effective_clock = p14_clock & ~ p13_inhibit;

    logic [3:0] count;

    always_ff @ (posedge effective_clock or posedge p15_reset)
        if (p15_reset)
            count <= '0;
        else if (count == 4'd9)
            count <= '0;
        else
            count <= count + 1'b1;

    assign p3_q0     = (count == 4'd0);
    assign p2_q1     = (count == 4'd1);
    assign p4_q2     = (count == 4'd2);
    assign p7_q3     = (count == 4'd3);
    assign p10_q4    = (count == 4'd4);
    assign p1_q5     = (count == 4'd5);
    assign p5_q6     = (count == 4'd6);
    assign p6_q7     = (count == 4'd7);
    assign p9_q8     = (count == 4'd8);
    assign p11_q9    = (count == 4'd9);
    assign p12_carry = (count <  4'd5);

endmodule

`default_nettype wire
