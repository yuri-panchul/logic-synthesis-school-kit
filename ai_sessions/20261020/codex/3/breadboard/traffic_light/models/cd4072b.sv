// Synthesizable functional model: two four-input OR gates.
// Physical pins: 14 = VDD, 7 = VSS, 6/8 = NC. No electrical/timing model.

module cd4072b
(
    input   p2_a,
    input   p3_b,
    input   p4_c,
    input   p5_d,
    output  p1_j,

    input   p9_e,
    input   p10_f,
    input   p11_g,
    input   p12_h,
    output  p13_k
);

    timeunit 1ns;
    timeprecision 1ps;

    assign p1_j  = p2_a | p3_b  | p4_c  | p5_d;
    assign p13_k = p9_e | p10_f | p11_g | p12_h;

endmodule
