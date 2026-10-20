//----------------------------------------------------------------------------
// Codex's 4 x 16 circuit (fifo_40105_proposal.html, 17 Oct 2026, 23:41), wired
// with the same chip models as bb8_sync so both run in the same harness.
// D3 is tied low because the harness has three data buttons, as BB8 does.
//----------------------------------------------------------------------------

module cd4069ub
# (parameter t_pd = 55)
(
    input  p1_a,  output p2_ay, input p3_b, output p4_by, input p5_c, output p6_cy,
    input  p7_vss, output p8_dy, input p9_d, output p10_ey, input p11_e, output p12_fy,
    input  p13_f, input p14_vdd
);
    wire powered = p14_vdd === 1'b1 && p7_vss === 1'b0;
    cmos_input_check pin1 (p1_a), pin3 (p3_b), pin5 (p5_c), pin9 (p9_d), pin11 (p11_e), pin13 (p13_f);
    logic a, b, c, d, e, f;
    always
    begin
        a <= # t_pd powered ? ~ p1_a  : 1'bx;
        b <= # t_pd powered ? ~ p3_b  : 1'bx;
        c <= # t_pd powered ? ~ p5_c  : 1'bx;
        d <= # t_pd powered ? ~ p9_d  : 1'bx;
        e <= # t_pd powered ? ~ p11_e : 1'bx;
        f <= # t_pd powered ? ~ p13_f : 1'bx;
        @ (p1_a or p3_b or p5_c or p9_d or p11_e or p13_f or powered);
    end
    assign { p2_ay, p4_by, p6_cy, p8_dy, p10_ey, p12_fy } = { a, b, c, d, e, f };
endmodule

module bb8_codex
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
    localparam t_inv = t_gate * 0.44;   // CD4069UB is about 0.44 x the CD4001B delay (55 / 125 ns typ. at 5 V)

    wire clr_n, w, r, w_n, r_n, si, p, so, full, empty;
    wire [3:0] dh;

    cd4069ub # (.t_pd (t_inv)) u4
    (
        .p1_a (rst), .p2_ay (clr_n), .p3_b (w), .p4_by (w_n), .p5_c (r), .p6_cy (r_n),
        .p7_vss (gnd), .p8_dy (so), .p9_d (p), .p10_ey (), .p11_e (gnd), .p12_fy (), .p13_f (gnd),
        .p14_vdd (vdd)
    );

    cd40174b # (.t_pd (t_reg)) u2
    (
        .p1_clear_n (clr_n), .p2_q1 (dh [0]), .p3_d1 (d0), .p4_d2 (d1), .p5_q2 (dh [1]),
        .p6_d3 (d2), .p7_q3 (dh [2]), .p8_vss (gnd), .p9_clk (clk), .p10_q4 (dh [3]),
        .p11_d4 (gnd), .p12_q5 (w), .p13_d5 (push), .p14_d6 (pop), .p15_q6 (r), .p16_vdd (vdd)
    );

    cd4001b # (.t_pd (t_gate)) u3
    (
        .p1_a (clk), .p2_b (w_n), .p3_j (si), .p4_k (p), .p5_c (clk), .p6_d (r_n), .p7_vss (gnd),
        .p8_e (dir), .p9_f (dir), .p10_l (full), .p11_m (empty), .p12_g (dor), .p13_h (dor),
        .p14_vdd (vdd)
    );

    cd74hc40105 # (.t_flag (t_flag), .t_step (t_step), .t_hold (t_hold)) u_a
    (
        .p1_oe (gnd), .p2_dir (dir), .p3_si (si), .p4_d0 (dh [0]), .p5_d1 (dh [1]), .p6_d2 (dh [2]),
        .p7_d3 (dh [3]), .p8_gnd (gnd), .p9_mr (rst), .p10_q3 (q [3]), .p11_q2 (q [2]),
        .p12_q1 (q [1]), .p13_q0 (q [0]), .p14_dor (dor), .p15_so (so), .p16_vcc (vdd)
    );
endmodule
