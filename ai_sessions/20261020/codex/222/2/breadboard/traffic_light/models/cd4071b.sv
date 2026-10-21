`timescale 1ns / 1ps
`default_nettype none

// Synthesizable functional model: four two-input OR gates.
// Physical supply pins: 14 = VDD, 7 = VSS. No electrical/timing model.

module cd4071b
(
    input  wire p1_a,
    input  wire p2_b,
    input  wire p5_c,
    input  wire p6_d,
    input  wire p8_e,
    input  wire p9_f,
    input  wire p12_g,
    input  wire p13_h,

    output wire p3_j,
    output wire p4_k,
    output wire p10_l,
    output wire p11_m
);

    assign p3_j  = p1_a  | p2_b;
    assign p4_k  = p5_c  | p6_d;
    assign p10_l = p8_e  | p9_f;
    assign p11_m = p12_g | p13_h;

endmodule

`default_nettype wire
