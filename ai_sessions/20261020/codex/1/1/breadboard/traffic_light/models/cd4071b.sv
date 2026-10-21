`timescale 1ns/1ps
`default_nettype none
// Synthesizable, ideal powered CD4071B. Four two-input OR gates.
// Physical-only pins: 14=VDD, 7=VSS. No electrical/timing model.
module cd4071b (
    input  wire p1_a, p2_b, p5_c, p6_d, p8_e, p9_f, p12_g, p13_h,
    output wire p3_j, p4_k, p10_l, p11_m
);
    assign p3_j  = p1_a  | p2_b;
    assign p4_k  = p5_c  | p6_d;
    assign p10_l = p8_e  | p9_f;
    assign p11_m = p12_g | p13_h;
endmodule
`default_nettype wire
