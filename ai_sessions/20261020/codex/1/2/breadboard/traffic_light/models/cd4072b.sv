`timescale 1ns / 1ps
`default_nettype none

// Synthesizable functional model: two four-input OR gates.
// Physical pins: 14 = VDD, 7 = VSS, 6/8 = NC. No electrical/timing model.

module cd4072b
(
    input  wire p2_a,
    input  wire p3_b,
    input  wire p4_c,
    input  wire p5_d,
    output wire p1_j,

    input  wire p9_e,
    input  wire p10_f,
    input  wire p11_g,
    input  wire p12_h,
    output wire p13_k
);

    assign p1_j  = p2_a | p3_b  | p4_c  | p5_d;
    assign p13_k = p9_e | p10_f | p11_g | p12_h;

endmodule

`default_nettype wire
