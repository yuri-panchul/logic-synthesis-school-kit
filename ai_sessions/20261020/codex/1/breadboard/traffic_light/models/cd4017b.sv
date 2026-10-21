`timescale 1ns/1ps
`default_nettype none
// Synthesizable, zero-delay FUNCTIONAL model of a powered CD4017B.
// VDD pin 16 and VSS pin 8 are physical supply connections, not HDL ports.
// Binary encoding is an abstraction of the chip's five-stage Johnson counter.
// Requires reset; does not model illegal Johnson states, power-up, drive current,
// setup/hold, pulse width, propagation delay or analog glitches.
// The effective-clock expression also captures a falling INHIBIT edge while
// CLOCK is high. In the exercise INHIBIT is permanently tied low, so synthesis
// removes this gate. Do not use changing combinational clock gates in FPGA RTL.
module cd4017b (
    input  wire p14_clock,
    input  wire p13_inhibit,
    input  wire p15_reset,
    output wire p3_q0, p2_q1, p4_q2, p7_q3, p10_q4,
    output wire p1_q5, p5_q6, p6_q7, p9_q8, p11_q9,
    output wire p12_carry
);
    wire effective_clock = p14_clock & ~p13_inhibit;
    reg [3:0] count;
    always @(posedge effective_clock or posedge p15_reset)
        if (p15_reset)
            count <= 4'd0;
        else if (count == 4'd9)
            count <= 4'd0;
        else
            count <= count + 4'd1;

    assign p3_q0  = count == 4'd0;
    assign p2_q1  = count == 4'd1;
    assign p4_q2  = count == 4'd2;
    assign p7_q3  = count == 4'd3;
    assign p10_q4 = count == 4'd4;
    assign p1_q5  = count == 4'd5;
    assign p5_q6  = count == 4'd6;
    assign p6_q7  = count == 4'd7;
    assign p9_q8  = count == 4'd8;
    assign p11_q9 = count == 4'd9;
    assign p12_carry = count < 4'd5;
endmodule
`default_nettype wire
