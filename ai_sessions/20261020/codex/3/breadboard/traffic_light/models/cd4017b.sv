// Synthesizable, zero-delay functional model of a powered CD4017B.
// Physical supply pins: 16 = VDD, 8 = VSS; they are not HDL ports.
// Binary encoding abstracts the chip's five-stage Johnson counter.
// Reset is required. Illegal Johnson-state recovery and electrical effects
// (current, setup/hold, pulse width and propagation delay) are not modeled.

module cd4017b
(
    input   p14_clock,
    input   p13_inhibit,
    input   p15_reset,

    output  p3_q0,
    output  p2_q1,
    output  p4_q2,
    output  p7_q3,
    output  p10_q4,
    output  p1_q5,
    output  p5_q6,
    output  p6_q7,
    output  p9_q8,
    output  p11_q9,
    output  p12_carry
);

    timeunit 1ns;
    timeprecision 1ps;

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
