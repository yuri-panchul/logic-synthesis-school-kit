//----------------------------------------------------------------------------
// Hybrid: Codex's four chips (40105, 40174, 4001, 4069) plus the pop gating of
// bb8_sync, so a pop on an empty FIFO never reaches SO:
//
//   U4.E  empty  = NOT DOR          (instead of U3.D = NOR (DOR, DOR))
//   U4.F  pop_n  = NOT pop          (a spare inverter)
//   U3.D  pop_ok = NOR (pop_n, empty) = pop AND DOR  ->  40174 D6
//
// The cd4069ub model is in codex_bb8.sv.
//----------------------------------------------------------------------------

module bb8_hybrid
# (
    parameter     t_gate = 125, t_ff = 150, t_reg = 200, t_flag = 40, t_step = 25, t_hold = 25,
    parameter int fault  = 0
)
(
    input clk, rst, push, pop, d0, d1, d2,
    output [3:0] q, output dor, output dir
);
    supply1 vdd;
    supply0 gnd;
    localparam t_inv = t_gate * 0.44;   // as in bb8_codex

    wire clr_n, w, r, w_n, r_n, si, p, so, full, empty, pop_n, pop_ok;
    wire [3:0] dh;

    cd4069ub # (.t_pd (t_inv)) u4
    (
        .p1_a (rst), .p2_ay (clr_n), .p3_b (w), .p4_by (w_n), .p5_c (r), .p6_cy (r_n),
        .p7_vss (gnd), .p8_dy (so), .p9_d (p), .p10_ey (empty), .p11_e (dor), .p12_fy (pop_n), .p13_f (pop),
        .p14_vdd (vdd)
    );

    cd40174b # (.t_pd (t_reg)) u2
    (
        .p1_clear_n (clr_n), .p2_q1 (dh [0]), .p3_d1 (d0), .p4_d2 (d1), .p5_q2 (dh [1]),
        .p6_d3 (d2), .p7_q3 (dh [2]), .p8_vss (gnd), .p9_clk (clk), .p10_q4 (dh [3]),
        .p11_d4 (gnd), .p12_q5 (w), .p13_d5 (push), .p14_d6 (pop_ok), .p15_q6 (r), .p16_vdd (vdd)
    );

    cd4001b # (.t_pd (t_gate)) u3
    (
        .p1_a (clk), .p2_b (w_n), .p3_j (si), .p4_k (p), .p5_c (clk), .p6_d (r_n), .p7_vss (gnd),
        .p8_e (dir), .p9_f (dir), .p10_l (full), .p11_m (pop_ok), .p12_g (pop_n), .p13_h (empty),
        .p14_vdd (vdd)
    );

    cd74hc40105 # (.t_flag (t_flag), .t_step (t_step), .t_hold (t_hold)) u_a
    (
        .p1_oe (gnd), .p2_dir (dir), .p3_si (si), .p4_d0 (dh [0]), .p5_d1 (dh [1]), .p6_d2 (dh [2]),
        .p7_d3 (dh [3]), .p8_gnd (gnd), .p9_mr (rst), .p10_q3 (q [3]), .p11_q2 (q [2]),
        .p12_q1 (q [1]), .p13_q0 (q [0]), .p14_dor (dor), .p15_so (so), .p16_vcc (vdd)
    );
endmodule
