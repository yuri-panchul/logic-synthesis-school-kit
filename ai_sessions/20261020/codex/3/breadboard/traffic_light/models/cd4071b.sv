// Synthesizable functional model: four two-input OR gates.
// Physical supply pins: 14 = VDD, 7 = VSS. No electrical/timing model.

module cd4071b
(
    input   p1_a,
    input   p2_b,
    input   p5_c,
    input   p6_d,
    input   p8_e,
    input   p9_f,
    input   p12_g,
    input   p13_h,

    output  p3_j,
    output  p4_k,
    output  p10_l,
    output  p11_m
);

    timeunit 1ns;
    timeprecision 1ps;

    assign p3_j  = p1_a  | p2_b;
    assign p4_k  = p5_c  | p6_d;
    assign p10_l = p8_e  | p9_f;
    assign p11_m = p12_g | p13_h;

endmodule
