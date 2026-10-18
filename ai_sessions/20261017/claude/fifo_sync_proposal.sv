// fifo_sync_proposal.sv
//
// A chip-level model of the proposed synchronous versions of the two FIFO exercises
// (see fifo_sync_proposal.html), checked in lockstep against the FIFO of the FPGA lab
//
//   basics-graphics-music/labs/4_microarchitecture/4_2_fifo/
//       4_2_5_optimized_ff_fifo_view_2_data_layout/flip_flop_fifo_empty_full_optimized_and_debug_2.sv
//
// with depth 16 and width 4, the size of one 40105:
//
//   bb8_sync   exercise BB8: one 40105 with push, pop and data buttons
//   p3_sync    exercise P3: FIFO A + FIFO B -> 4008 adder -> FIFO C
//
// Each 40105 becomes a synchronous FIFO.  At every rising clock edge 4013 flip-flops
// sample push and pop and a 40174 samples the data switches, as the always_ff blocks
// of the RTL do.  A 4001 NOR gate turns every sampled 1 into exactly one pulse on SI
// or SO in the low half of that clock period, and the 40105 executes the command.  By
// the next rising edge its outputs (Q0-Q3, DOR = ~empty, DIR = ~full) equal those of
// the RTL module.
//
// The netlists are written by hand from the proposal; the breadboard layout does not
// exist yet.  The chip models (40105, 4013, 4082, 4008) and the bounce model come from
// fifo_breadboard.sv, so compile the two files together:
//
//   BGM=/home/verilog/projects/basics-graphics-music
//   RTL=$BGM/labs/4_microarchitecture/4_2_fifo/4_2_5_optimized_ff_fifo_view_2_data_layout
//   iverilog -g2012 -s tb_sync_proposal -I $BGM/labs/common -I $BGM/peripherals \
//       -o sync_tb fifo_breadboard.sv fifo_sync_proposal.sv \
//       $RTL/flip_flop_fifo_empty_full_optimized_and_debug_2.sv
//   vvp -n sync_tb
//
// Add -P tb_sync_proposal.fault=N to build the circuit with deliberate fault N
// (see the netlists); the testbench must then fail.

//----------------------------------------------------------------------------
// CD4001B: quad 2-input NOR gate (TI SCHS015)
//----------------------------------------------------------------------------

module cd4001b
# (
    parameter t_pd = 125
)
(
    input  p1_a,
    input  p2_b,
    output p3_j,
    output p4_k,
    input  p5_c,
    input  p6_d,
    input  p7_vss,
    input  p8_e,
    input  p9_f,
    output p10_l,
    output p11_m,
    input  p12_g,
    input  p13_h,
    input  p14_vdd
);

    wire  powered = p14_vdd === 1'b1 && p7_vss === 1'b0;

    cmos_input_check pin1 (p1_a), pin2 (p2_b), pin5 (p5_c), pin6 (p6_d), pin8 (p8_e), pin9 (p9_f), pin12 (p12_g), pin13 (p13_h);
    logic j, k, l, m;

    // Transport delay: a glitch at the inputs comes out as a glitch

    always
    begin
        j <= # t_pd powered ? ~ (p1_a  | p2_b)  : 1'bx;
        k <= # t_pd powered ? ~ (p5_c  | p6_d)  : 1'bx;
        l <= # t_pd powered ? ~ (p8_e  | p9_f)  : 1'bx;
        m <= # t_pd powered ? ~ (p12_g | p13_h) : 1'bx;
        @ (p1_a or p2_b or p5_c or p6_d or p8_e or p9_f or p12_g or p13_h or powered);
    end

    assign p3_j  = j;
    assign p4_k  = k;
    assign p10_l = l;
    assign p11_m = m;

endmodule

//----------------------------------------------------------------------------
// CD40174B: hex D flip-flop, common rising-edge clock, common active-low CLEAR
// (TI SCHS054).  Setup and hold violations are reported as errors.
//----------------------------------------------------------------------------

module cd40174b
# (
    parameter t_pd = 200
)
(
    input  p1_clear_n,
    output p2_q1,
    input  p3_d1,
    input  p4_d2,
    output p5_q2,
    input  p6_d3,
    output p7_q3,
    input  p8_vss,
    input  p9_clk,
    output p10_q4,
    input  p11_d4,
    output p12_q5,
    input  p13_d5,
    input  p14_d6,
    output p15_q6,
    input  p16_vdd
);

    wire powered = p16_vdd === 1'b1 && p8_vss === 1'b0;
    wire clear   = ~ p1_clear_n;

    cmos_input_check pin1 (p1_clear_n), pin3 (p3_d1), pin4 (p4_d2), pin6 (p6_d3), pin9 (p9_clk), pin11 (p11_d4), pin13 (p13_d5), pin14 (p14_d6);

    wire [6:1] d = { p14_d6, p13_d5, p11_d4, p6_d3, p4_d2, p3_d1 };
    wire [6:1] q;

    for (genvar i = 1; i <= 6; i ++)
    begin : ff
        cd4013b_flip_flop # (.t_pd (t_pd)) f
            (.clk (p9_clk), .d (d [i]), .r (clear), .s (1'b0), .q (q [i]), .q_n ());
    end

    assign { p15_q6, p12_q5, p10_q4, p7_q3, p5_q2, p2_q1 } = powered ? q : 6'bx;

endmodule

//----------------------------------------------------------------------------
// A gate for deliberate fault 3 only, with transport delay
//----------------------------------------------------------------------------

module fault_and2 # (parameter t_pd = 125) (input a, input b, output logic y);
    always begin y <= # t_pd a & b; @ (a or b); end
endmodule

//----------------------------------------------------------------------------
// bb8_sync: exercise BB8 as a synchronous FIFO.
//
//   4013 #1   FF1 samples push, FF2 samples pop AND DOR (pop only when not empty)
//   4001      SI = NOR (clock, /push_r)          high in the low half after push_r = 1
//             x  = NOR (clock, /pop_r)           high in the low half after pop_r = 1
//             SO = NOR (x, x)                    falls at the falling clock edge
//   4082      pop_ok = pop AND DOR
//   40174     the data switches, sampled at the rising edge
//   40105     FIFO A
//
// Deliberate faults (parameter fault):
//   1  pop goes straight to the flip-flop, without AND DOR
//   2  no 40174: the data switches go straight to D0-D2 of the 40105
//   3  no flip-flop: SI = clock AND push (the clock-gated pulse of the Habr article)
//----------------------------------------------------------------------------

module bb8_sync
# (
    parameter     t_gate = 125,  // 4001, 4082
                  t_ff   = 150,  // 4013
                  t_reg  = 200,  // 40174
                  t_flag = 40,   // 40105
                  t_step = 25,
                  t_hold = 25,
    parameter int fault  = 0
)
(
    // OUT pins of the button and clock modules
    input        clk,
    input        rst,
    input        push,
    input        pop,
    input        d0,
    input        d1,
    input        d2,

    // LEDs
    output [3:0] q,      // Q3-Q0 of the FIFO: read_data
    output       dor,    // ~ empty
    output       dir     // ~ full
);

    supply1 vdd;
    supply0 gnd;

    wire push_r_n;   // Q1 of 4013: push sampled at the rising edge, inverted
    wire pop_r_n;    // Q2 of 4013: pop AND DOR sampled at the rising edge, inverted
    wire pop_ok;     // pop AND DOR
    wire si_nor;     // NOR (clock, /push_r)
    wire x;          // NOR (clock, /pop_r)
    wire so;         // SO of the FIFO
    wire r0, r1, r2; // the data register

    wire pop_d = fault == 1 ? pop : pop_ok;

    cd4013b # (.t_pd (t_ff)) u_u1
    (
        .p1_q1    (          ),  // not used
        .p2_q1_n  ( push_r_n ),
        .p3_clk1  ( clk      ),
        .p4_r1    ( rst      ),
        .p5_d1    ( push     ),
        .p6_s1    ( gnd      ),
        .p7_vss   ( gnd      ),
        .p8_s2    ( gnd      ),
        .p9_d2    ( pop_d    ),
        .p10_r2   ( rst      ),
        .p11_clk2 ( clk      ),
        .p12_q2_n ( pop_r_n  ),
        .p13_q2   (          ),  // not used
        .p14_vdd  ( vdd      )
    );

    cd4001b # (.t_pd (t_gate)) u_nor
    (
        .p1_a     ( clk      ),
        .p2_b     ( push_r_n ),
        .p3_j     ( si_nor   ),
        .p4_k     ( x        ),
        .p5_c     ( clk      ),
        .p6_d     ( pop_r_n  ),
        .p7_vss   ( gnd      ),
        .p8_e     ( x        ),
        .p9_f     ( x        ),
        .p10_l    ( so       ),
        .p11_m    (          ),  // not used
        .p12_g    ( gnd      ),
        .p13_h    ( gnd      ),
        .p14_vdd  ( vdd      )
    );

    cd4082b # (.t_pd (t_gate)) u_and
    (
        .p1_j     ( pop_ok   ),
        .p2_a     ( pop      ),
        .p3_b     ( dor      ),
        .p4_c     ( vdd      ),
        .p5_d     ( vdd      ),
        .p7_vss   ( gnd      ),
        .p9_e     ( gnd      ),
        .p10_f    ( gnd      ),
        .p11_g    ( gnd      ),
        .p12_h    ( gnd      ),
        .p13_k    (          ),  // not used
        .p14_vdd  ( vdd      )
    );

    cd40174b # (.t_pd (t_reg)) u_reg
    (
        .p1_clear_n ( vdd    ),
        .p2_q1      ( r0     ),
        .p3_d1      ( d0     ),
        .p4_d2      ( d1     ),
        .p5_q2      ( r1     ),
        .p6_d3      ( d2     ),
        .p7_q3      ( r2     ),
        .p8_vss     ( gnd    ),
        .p9_clk     ( clk    ),
        .p10_q4     (        ),  // not used
        .p11_d4     ( gnd    ),
        .p12_q5     (        ),  // not used
        .p13_d5     ( gnd    ),
        .p14_d6     ( gnd    ),
        .p15_q6     (        ),  // not used
        .p16_vdd    ( vdd    )
    );

    // SI, or the clock-gated pulse of fault 3

    wire si, si_and;

    if (fault == 3)
    begin : f3
        fault_and2 # (.t_pd (t_gate)) g (.a (clk), .b (push), .y (si_and));
    end

    assign si = fault == 3 ? si_and : si_nor;

    wire [2:0] fifo_d = fault == 2 ? { d2, d1, d0 } : { r2, r1, r0 };

    cd74hc40105 # (.t_flag (t_flag), .t_step (t_step), .t_hold (t_hold)) u_a
    (
        .p1_oe    ( gnd        ),
        .p2_dir   ( dir        ),
        .p3_si    ( si         ),
        .p4_d0    ( fifo_d [0] ),
        .p5_d1    ( fifo_d [1] ),
        .p6_d2    ( fifo_d [2] ),
        .p7_d3    ( gnd        ),
        .p8_gnd   ( gnd        ),
        .p9_mr    ( rst        ),
        .p10_q3   ( q [3]      ),
        .p11_q2   ( q [2]      ),
        .p12_q1   ( q [1]      ),
        .p13_q0   ( q [0]      ),
        .p14_dor  ( dor        ),
        .p15_so   ( so         ),
        .p16_vcc  ( vdd        )
    );

endmodule

//----------------------------------------------------------------------------
// p3_sync: exercise P3 with synchronous FIFOs.  A pair moves from A and B into C
// on every clock while A and B have data and C has room, as in the RTL:
//
//   go = ~ empty_A & ~ empty_B & ~ full_C;   push_C = pop_A = pop_B = go
//
//   4013 #1   FF1 samples push A, FF2 samples pop C AND DOR of C
//   4013 #2   FF1 samples push B, FF2 samples go
//   4001 #1   SI of A, SI of B, SI of C = NOR (clock, /sampled bit);
//             SO of A and B = NOR (SI of C, SI of C): A and B let go of the pair
//             one gate delay after C has taken the sum
//   4001 #2   x = NOR (clock, /pop C sampled), SO of C = NOR (x, x)
//   4082      go = DOR A AND DOR B AND DIR C;  pop C AND DOR C
//   40174     the data switches, shared by A and B
//   4008      C gets Q of A + Q of B
//
// Deliberate faults (parameter fault):
//   1  pop C goes straight to the flip-flop, without AND DOR of C
//   2  no 40174: the data switches go straight to D0-D2 of A and B
//   3  no flip-flop on push A: SI of A = clock AND push A
//   6  R of the go flip-flop tied to GND instead of reset
//----------------------------------------------------------------------------

module p3_sync
# (
    parameter     t_gate = 125,  // 4001, 4082
                  t_ff   = 150,  // 4013
                  t_reg  = 200,  // 40174
                  t_add  = 400,  // 4008
                  t_flag = 40,   // 40105
                  t_step = 25,
                  t_hold = 25,
    parameter int fault  = 0
)
(
    // OUT pins of the button and clock modules
    input        clk,
    input        rst,
    input        pushA,
    input        pushB,
    input        popC,
    input        d0,
    input        d1,
    input        d2,

    // LEDs
    output [2:0] qa,      // head of A
    output       dor_a,
    output       dir_a,
    output [2:0] qb,      // head of B
    output       dor_b,
    output       dir_b,
    output [3:0] qc,      // head of C
    output       dor_c,
    output       dir_c
);

    supply1 vdd;
    supply0 gnd;

    wire push_a_r_n, push_b_r_n, pop_c_r_n, go_r_n;
    wire go, pop_c_ok;
    wire si_a_nor, si_b, si_c, so_ab, x_c, so_c;
    wire r0, r1, r2;
    wire [3:0] sum;
    wire qa3, qb3;

    wire pop_c_d = fault == 1 ? popC : pop_c_ok;
    wire go_rst  = fault == 6 ? gnd  : rst;

    cd4013b # (.t_pd (t_ff)) u_u1
    (
        .p1_q1    (            ),  // not used
        .p2_q1_n  ( push_a_r_n ),
        .p3_clk1  ( clk        ),
        .p4_r1    ( rst        ),
        .p5_d1    ( pushA      ),
        .p6_s1    ( gnd        ),
        .p7_vss   ( gnd        ),
        .p8_s2    ( gnd        ),
        .p9_d2    ( pop_c_d    ),
        .p10_r2   ( rst        ),
        .p11_clk2 ( clk        ),
        .p12_q2_n ( pop_c_r_n  ),
        .p13_q2   (            ),  // not used
        .p14_vdd  ( vdd        )
    );

    cd4013b # (.t_pd (t_ff)) u_u2
    (
        .p1_q1    (            ),  // not used
        .p2_q1_n  ( push_b_r_n ),
        .p3_clk1  ( clk        ),
        .p4_r1    ( rst        ),
        .p5_d1    ( pushB      ),
        .p6_s1    ( gnd        ),
        .p7_vss   ( gnd        ),
        .p8_s2    ( gnd        ),
        .p9_d2    ( go         ),
        .p10_r2   ( go_rst     ),
        .p11_clk2 ( clk        ),
        .p12_q2_n ( go_r_n     ),
        .p13_q2   (            ),  // not used
        .p14_vdd  ( vdd        )
    );

    cd4001b # (.t_pd (t_gate)) u_nor1
    (
        .p1_a     ( clk        ),
        .p2_b     ( push_a_r_n ),
        .p3_j     ( si_a_nor   ),
        .p4_k     ( si_b       ),
        .p5_c     ( clk        ),
        .p6_d     ( push_b_r_n ),
        .p7_vss   ( gnd        ),
        .p8_e     ( clk        ),
        .p9_f     ( go_r_n     ),
        .p10_l    ( si_c       ),
        .p11_m    ( so_ab      ),
        .p12_g    ( si_c       ),
        .p13_h    ( si_c       ),
        .p14_vdd  ( vdd        )
    );

    cd4001b # (.t_pd (t_gate)) u_nor2
    (
        .p1_a     ( clk        ),
        .p2_b     ( pop_c_r_n  ),
        .p3_j     ( x_c        ),
        .p4_k     ( so_c       ),
        .p5_c     ( x_c        ),
        .p6_d     ( x_c        ),
        .p7_vss   ( gnd        ),
        .p8_e     ( gnd        ),
        .p9_f     ( gnd        ),
        .p10_l    (            ),  // not used
        .p11_m    (            ),  // not used
        .p12_g    ( gnd        ),
        .p13_h    ( gnd        ),
        .p14_vdd  ( vdd        )
    );

    cd4082b # (.t_pd (t_gate)) u_and
    (
        .p1_j     ( go         ),
        .p2_a     ( dor_a      ),
        .p3_b     ( dor_b      ),
        .p4_c     ( dir_c      ),
        .p5_d     ( vdd        ),
        .p7_vss   ( gnd        ),
        .p9_e     ( popC       ),
        .p10_f    ( dor_c      ),
        .p11_g    ( vdd        ),
        .p12_h    ( vdd        ),
        .p13_k    ( pop_c_ok   ),
        .p14_vdd  ( vdd        )
    );

    cd40174b # (.t_pd (t_reg)) u_reg
    (
        .p1_clear_n ( vdd      ),
        .p2_q1      ( r0       ),
        .p3_d1      ( d0       ),
        .p4_d2      ( d1       ),
        .p5_q2      ( r1       ),
        .p6_d3      ( d2       ),
        .p7_q3      ( r2       ),
        .p8_vss     ( gnd      ),
        .p9_clk     ( clk      ),
        .p10_q4     (          ),  // not used
        .p11_d4     ( gnd      ),
        .p12_q5     (          ),  // not used
        .p13_d5     ( gnd      ),
        .p14_d6     ( gnd      ),
        .p15_q6     (          ),  // not used
        .p16_vdd    ( vdd      )
    );

    cd4008b # (.t_pd (t_add)) u_add
    (
        .p1_a4    ( gnd     ),
        .p2_b3    ( qb [2]  ),
        .p3_a3    ( qa [2]  ),
        .p4_b2    ( qb [1]  ),
        .p5_a2    ( qa [1]  ),
        .p6_b1    ( qb [0]  ),
        .p7_a1    ( qa [0]  ),
        .p8_vss   ( gnd     ),
        .p9_cin   ( gnd     ),
        .p10_s1   ( sum [0] ),
        .p11_s2   ( sum [1] ),
        .p12_s3   ( sum [2] ),
        .p13_s4   ( sum [3] ),
        .p14_cout (         ),  // not used
        .p15_b4   ( gnd     ),
        .p16_vdd  ( vdd     )
    );

    // SI of A, or the clock-gated pulse of fault 3

    wire si_a, si_a_and;

    if (fault == 3)
    begin : f3
        fault_and2 # (.t_pd (t_gate)) g (.a (clk), .b (pushA), .y (si_a_and));
    end

    assign si_a = fault == 3 ? si_a_and : si_a_nor;

    wire [2:0] ab_d = fault == 2 ? { d2, d1, d0 } : { r2, r1, r0 };

    cd74hc40105 # (.t_flag (t_flag), .t_step (t_step), .t_hold (t_hold)) u_a
    (
        .p1_oe    ( gnd      ),
        .p2_dir   ( dir_a    ),
        .p3_si    ( si_a     ),
        .p4_d0    ( ab_d [0] ),
        .p5_d1    ( ab_d [1] ),
        .p6_d2    ( ab_d [2] ),
        .p7_d3    ( gnd      ),
        .p8_gnd   ( gnd      ),
        .p9_mr    ( rst      ),
        .p10_q3   ( qa3      ),  // always 0
        .p11_q2   ( qa [2]   ),
        .p12_q1   ( qa [1]   ),
        .p13_q0   ( qa [0]   ),
        .p14_dor  ( dor_a    ),
        .p15_so   ( so_ab    ),
        .p16_vcc  ( vdd      )
    );

    cd74hc40105 # (.t_flag (t_flag), .t_step (t_step), .t_hold (t_hold)) u_b
    (
        .p1_oe    ( gnd      ),
        .p2_dir   ( dir_b    ),
        .p3_si    ( si_b     ),
        .p4_d0    ( ab_d [0] ),
        .p5_d1    ( ab_d [1] ),
        .p6_d2    ( ab_d [2] ),
        .p7_d3    ( gnd      ),
        .p8_gnd   ( gnd      ),
        .p9_mr    ( rst      ),
        .p10_q3   ( qb3      ),  // always 0
        .p11_q2   ( qb [2]   ),
        .p12_q1   ( qb [1]   ),
        .p13_q0   ( qb [0]   ),
        .p14_dor  ( dor_b    ),
        .p15_so   ( so_ab    ),
        .p16_vcc  ( vdd      )
    );

    cd74hc40105 # (.t_flag (t_flag), .t_step (t_step), .t_hold (t_hold)) u_c
    (
        .p1_oe    ( gnd      ),
        .p2_dir   ( dir_c    ),
        .p3_si    ( si_c     ),
        .p4_d0    ( sum [0]  ),
        .p5_d1    ( sum [1]  ),
        .p6_d2    ( sum [2]  ),
        .p7_d3    ( sum [3]  ),
        .p8_gnd   ( gnd      ),
        .p9_mr    ( rst      ),
        .p10_q3   ( qc [3]   ),
        .p11_q2   ( qc [2]   ),
        .p12_q1   ( qc [1]   ),
        .p13_q0   ( qc [0]   ),
        .p14_dor  ( dor_c    ),
        .p15_so   ( so_c     ),
        .p16_vcc  ( vdd      )
    );

endmodule

//----------------------------------------------------------------------------
// The reference: the RTL FIFO of the lab, depth 16, width 4, without the debug
// outputs, plus the occupancy and the contents for the comparison
//----------------------------------------------------------------------------

module ref_fifo
(
    input        clk,
    input        rst,
    input        push,
    input        pop,
    input  [3:0] write_data,
    output [3:0] read_data,
    output       empty,
    output       full
);

    flip_flop_fifo_empty_full_optimized_and_debug_2 # (.width (4), .depth (16)) rtl
    (
        .clk         ( clk        ),
        .rst         ( rst        ),
        .push        ( push       ),
        .pop         ( pop        ),
        .write_data  ( write_data ),
        .read_data   ( read_data  ),
        .empty       ( empty      ),
        .full        ( full       ),
        .debug_ptrs  (            ),
        .debug_valid (            ),
        .debug_data  (            )
    );

    function automatic int count ();
        if (rtl.wr_ptr_odd_circle == rtl.rd_ptr_odd_circle)
            count = int' (rtl.wr_ptr) - int' (rtl.rd_ptr);
        else
            count = 16 - int' (rtl.rd_ptr) + int' (rtl.wr_ptr);
    endfunction

    function automatic logic [3:0] entry (input int i);  // 0 is the head
        entry = rtl.data [(int' (rtl.rd_ptr) + i) % 16];
    endfunction

endmodule

//----------------------------------------------------------------------------
// Compares one 40105 model with one reference FIFO just before a rising edge:
// occupancy, every word in order, DOR = ~ empty, DIR = ~ full, Q = read_data.
//----------------------------------------------------------------------------

`define COMPARE_FIFO(NAME, CHIP, REF, Q, DOR, DIR, WIDTH)                                  \
    begin                                                                                \
        int n_chip, n_ref;                                                               \
        logic [3:0] w_chip, w_ref, q_ref;                                                \
        n_chip = CHIP.n_words;                                                           \
        n_ref  = REF.count ();                                                           \
        if (n_chip != n_ref)                                                             \
            fail ($sformatf ("%s holds %0d words, the RTL %0d", NAME, n_chip, n_ref));   \
        else                                                                             \
            for (int i = 0; i < n_ref; i ++)                                             \
            begin                                                                        \
                w_chip = CHIP.word [16 - i];                                             \
                w_ref  = REF.entry (i);                                                  \
                if (w_chip % (1 << WIDTH) !== w_ref % (1 << WIDTH))                      \
                    fail ($sformatf ("%s word %0d is %0d, the RTL has %0d", NAME, i,     \
                        w_chip, w_ref));                                                 \
            end                                                                          \
        q_ref = REF.read_data;                                                           \
        if (DOR !== ~ REF.empty)                                                         \
            fail ($sformatf ("%s: DOR = %b, RTL empty = %b", NAME, DOR, REF.empty));     \
        if (DIR !== ~ REF.full)                                                          \
            fail ($sformatf ("%s: DIR = %b, RTL full = %b", NAME, DIR, REF.full));       \
        if (! REF.empty && Q !== q_ref % (1 << WIDTH))                                   \
            fail ($sformatf ("%s: Q = %0d, RTL read_data = %0d", NAME, Q, q_ref));       \
    end

//----------------------------------------------------------------------------
// The stimulus shared by both tests: a 2 Hz clock (rising edges at 0.25 s,
// 0.75 s ...), buttons with or without contact bounce, and random numbers.
//----------------------------------------------------------------------------

// Timing corners, in ns: gate, flip-flop, 40174, 4008, 40105 flag, ripple step, data hold.
// "slow glue" pairs slow gates and flip-flops with fast FIFOs, "fast glue" the other way.

function automatic int timing (input int corner, input int what);
    case (corner)
        0:       case (what) 0: timing = 125; 1: timing = 150; 2: timing = 200; 3: timing = 400;
                             4: timing = 40;  5: timing = 25;  default: timing = 25; endcase
        1:       case (what) 0: timing = 60;  1: timing = 60;  2: timing = 80;  3: timing = 150;
                             4: timing = 15;  5: timing = 6;   default: timing = 25; endcase
        2:       case (what) 0: timing = 250; 1: timing = 300; 2: timing = 400; 3: timing = 800;
                             4: timing = 63;  5: timing = 40;  default: timing = 38; endcase
        3:       case (what) 0: timing = 250; 1: timing = 300; 2: timing = 400; 3: timing = 800;
                             4: timing = 15;  5: timing = 6;   default: timing = 25; endcase
        default: case (what) 0: timing = 60;  1: timing = 60;  2: timing = 80;  3: timing = 150;
                             4: timing = 63;  5: timing = 40;  default: timing = 38; endcase
    endcase
endfunction

function automatic string corner_name (input int corner);
    case (corner)
        0:       corner_name = "typical";
        1:       corner_name = "fast";
        2:       corner_name = "slow";
        3:       corner_name = "slow glue, fast FIFO";
        default: corner_name = "fast glue, slow FIFO";
    endcase
endfunction

`define TEST_COMMON(N)                                                                   \
    localparam time ms = 64'd1_000_000, us = 64'd1_000;                                  \
    logic clk = 1'b0;                                                                    \
    always # (250 * ms) clk = ~ clk;                                                     \
    logic [N - 1:0] want = '0;                                                           \
    wire  [N - 1:0] bounced, btn;                                                        \
    logic use_bounce = 1'b1;                                                             \
    for (genvar i = 0; i < N; i ++)                                                      \
    begin : buttons                                                                      \
        button_with_bounce b (.want (want [i]), .out (bounced [i]));                     \
    end                                                                                  \
    assign btn = use_bounce ? bounced : want;                                            \
    int seed_v = seed;                                                                   \
    function automatic int unsigned rnd (input int unsigned n);                          \
        rnd = $unsigned ($random (seed_v)) % n;                                          \
    endfunction                                                                          \
    int n_fail = 0;                                                                      \
    task automatic fail (input string what);                                             \
        if (n_fail < 5)                                                                  \
            $display ("%s, %s corner, %0.3f s: %s", test, corner_name (corner),           \
                real'($time) / 1e9, what);                                               \
        n_fail ++;                                                                       \
    endtask                                                                              \
    bit checking = 1'b0;                                                                 \
    int n_edges  = 0;

//----------------------------------------------------------------------------
// BB8 in lockstep with one RTL FIFO
//----------------------------------------------------------------------------

module bb8_check
# (
    parameter int    corner = 0,
    parameter        t_gate = 125, t_ff = 150, t_reg = 200, t_flag = 40, t_step = 25, t_hold = 25,
    parameter int    fault  = 0,
    parameter int    seed   = 1,
    parameter bit    report = 0     // print the hold-for-three-clocks scenarios
)
(
    output logic done,
    output int   errors,
    output int   edges,
    output int   moves
);

    localparam string test = "bb8";
    localparam RST = 0, PUSH = 1, POP = 2;

    `TEST_COMMON (6)   // rst, push, pop, d0, d1, d2

    wire       rst  = btn [RST];
    wire       push = btn [PUSH];
    wire       pop  = btn [POP];
    wire [2:0] d    = btn [5:3];

    wire [3:0] q;
    wire       dor, dir;

    bb8_sync # (.t_gate (t_gate), .t_ff (t_ff), .t_reg (t_reg), .t_flag (t_flag),
        .t_step (t_step), .t_hold (t_hold), .fault (fault)) dut
    (
        .clk (clk), .rst (rst), .push (push), .pop (pop), .d0 (d [0]), .d1 (d [1]), .d2 (d [2]),
        .q (q), .dor (dor), .dir (dir)
    );

    // The RTL gets the same buttons.  As in lab_top, pop is gated with ~ empty.
    // The 40105 takes a push into a full FIFO when the same edge pops, which the
    // RTL FIFO also supports (allow_push_when_full_with_pop in its tb.sv).

    wire [3:0] r_q;
    wire       r_empty, r_full;
    wire       r_pop  = pop  & ~ r_empty;
    wire       r_push = push & (~ r_full | r_pop);

    ref_fifo ref_a (.clk (clk), .rst (rst), .push (r_push), .pop (r_pop),
        .write_data ({ 1'b0, d }), .read_data (r_q), .empty (r_empty), .full (r_full));

    always @ (posedge clk)
        if (checking && rst === 1'b0)
        begin
            n_edges ++;
            `COMPARE_FIFO ("FIFO", dut.u_a, ref_a, q, dor, dir, 4)
            cover_full       += r_full;
            cover_empty      += r_empty;
            cover_full_both  += push & r_full & pop;     // push into full, same edge pops
            cover_full_push  += push & r_full & ~ pop;   // push into full: ignored
            cover_empty_both += push & r_empty & pop;    // pop from empty, same edge pushes
        end

    int cover_full = 0, cover_empty = 0, cover_full_both = 0, cover_full_push = 0, cover_empty_both = 0;

    final
        if (report)
            $display ("bb8 coverage, %s corner: full at %0d edges, empty at %0d; push into full with pop %0d, without pop %0d; push and pop on empty %0d",
                corner_name (corner), cover_full, cover_empty, cover_full_both, cover_full_push, cover_empty_both);

    task automatic wait_before_edge (input time lead);
        @ (posedge clk);
        # (500 * ms - lead);
    endtask

    task automatic reset ();
        want [RST] = 1'b1;
        # (300 * ms);
        want [RST] = 1'b0;
        # (700 * ms);
    endtask

    task automatic pop_all (output string popped);
        popped = "";
        while (dor === 1'b1)
        begin
            wait_before_edge (100 * ms);
            popped = { popped, $sformatf (" %0d", q) };
            want [POP] = 1'b1;
            wait_before_edge (100 * ms);
            want [POP] = 1'b0;
            # (300 * ms);
        end
    endtask

    // One cycle of synchronous stimulus: the inputs change 1 us after the edge,
    // like the outputs of other flip-flops

    task automatic cycle (input bit p, input bit o, input logic [2:0] data);
        @ (posedge clk);
        # (1 * us);
        want [PUSH]  = p;
        want [POP]   = o;
        want [5:3]   = data;
    endtask

    initial
    begin
        string popped;
        int    k;

        done   = 1'b0;
        edges  = 0;
        moves  = 0;
        errors = 0;

        # (37_300_000);  // people do not press buttons in step with the clock
        reset ();
        checking = 1'b1;

        // 1. The question: push pressed 100 ms before a rising edge and held for
        //    three clock periods, data 5, then pop until empty

        wait_before_edge (100 * ms);
        want [5:3]  = 3'd5;
        want [PUSH] = 1'b1;
        # (1500 * ms);
        want [PUSH] = 1'b0;
        # (200 * ms);
        want [5:3]  = 3'd0;
        # (1000 * ms);

        if (report && corner == 0 && fault == 0)
            $display ("bb8: push held for 3 clock periods: the FIFO holds %0d words, the RTL %0d",
                dut.u_a.n_words, ref_a.count ());

        pop_all (popped);

        if (report && corner == 0 && fault == 0)
            $display ("bb8: popped%s", popped);

        // 2. The same with the data switches changed while push is held:
        //    1 before the first edge, 2 and 3 before the next ones

        wait_before_edge (100 * ms);
        want [5:3]  = 3'd1;
        want [PUSH] = 1'b1;
        # (200 * ms);
        want [5:3]  = 3'd2;
        # (500 * ms);
        want [5:3]  = 3'd3;
        # (800 * ms);
        want [PUSH] = 1'b0;
        # (200 * ms);
        want [5:3]  = 3'd0;
        # (1000 * ms);

        pop_all (popped);

        if (report && corner == 0 && fault == 0)
            $display ("bb8: data 1, 2, 3 at the three edges: popped%s", popped);

        // 3. The tests of tb.sv of the lab, with synchronous inputs

        use_bounce = 1'b0;

        for (int i = 0; i < 16; i ++)                 // fill
            cycle (1, 0, 3' (i));
        cycle (1, 0, 3'd7);                           // push into a full FIFO: ignored
        for (int i = 0; i < 16; i ++)                 // empty
            cycle (0, 1, 3'd0);
        cycle (0, 1, 3'd0);                           // pop from an empty FIFO: ignored

        for (int i = 0; i < 8; i ++)                  // fill half, then back-to-back
            cycle (1, 0, 3' (i));
        for (int i = 0; i < 80; i ++)
            cycle (1, 1, 3' (i * 5));
        for (int i = 0; i < 9; i ++)
            cycle (0, 1, 3'd0);

        for (int i = 0; i < 16; i ++)                 // full, then push and pop together
            cycle (1, 0, 3' (i));
        for (int i = 0; i < 10; i ++)
            cycle (1, 1, 3' (i + 2));

        // 4. Random synchronous inputs, in phases that fill, drain and hover

        for (int phase = 0; phase < 12; phase ++)
        begin
            int p_push, p_pop;
            p_push = phase % 3 == 0 ? 80 : phase % 3 == 1 ? 20 : 50;
            p_pop  = phase % 3 == 0 ? 20 : phase % 3 == 1 ? 80 : 50;

            repeat (150)
                cycle (rnd (100) < p_push, rnd (100) < p_pop, 3' (rnd (8)));
        end

        cycle (0, 0, 3'd0);

        // 5. Random button presses with bounce at any moment, and a few resets

        use_bounce = 1'b1;

        repeat (400)
        begin
            # (rnd (700_000) * us + 7);  // never exactly on a clock edge
            case (rnd (9))
                0, 1, 2:   want [PUSH] = ~ want [PUSH];
                3, 4, 5:   want [POP]  = ~ want [POP];
                6, 7:      begin k = 3 + rnd (3); want [k] = ~ want [k]; end
                default:   if (rnd (4) == 0)
                           begin
                               want [RST] = 1'b1;
                               # ((100 + rnd (500)) * ms);
                               want [RST] = 1'b0;
                           end
            endcase
        end

        want = '0;
        # (2000 * ms);

        errors = n_fail;
        edges  = n_edges;
        done   = 1'b1;
    end

endmodule

//----------------------------------------------------------------------------
// P3 in lockstep with three RTL FIFOs
//----------------------------------------------------------------------------

module p3_check
# (
    parameter int    corner = 0,
    parameter        t_gate = 125, t_ff = 150, t_reg = 200, t_add = 400,
                     t_flag = 40, t_step = 25, t_hold = 25,
    parameter int    fault  = 0,
    parameter int    seed   = 1,
    parameter bit    report = 0
)
(
    output logic done,
    output int   errors,
    output int   edges,
    output int   moves
);

    localparam string test = "p3";
    localparam RST = 0, PUSH_A = 1, PUSH_B = 2, POP_C = 3;

    `TEST_COMMON (7)   // rst, push A, push B, pop C, d0, d1, d2

    wire       rst   = btn [RST];
    wire       pushA = btn [PUSH_A];
    wire       pushB = btn [PUSH_B];
    wire       popC  = btn [POP_C];
    wire [2:0] d     = btn [6:4];

    wire [2:0] qa, qb;
    wire [3:0] qc;
    wire       dor_a, dir_a, dor_b, dir_b, dor_c, dir_c;

    p3_sync # (.t_gate (t_gate), .t_ff (t_ff), .t_reg (t_reg), .t_add (t_add), .t_flag (t_flag),
        .t_step (t_step), .t_hold (t_hold), .fault (fault)) dut
    (
        .clk (clk), .rst (rst), .pushA (pushA), .pushB (pushB), .popC (popC),
        .d0 (d [0]), .d1 (d [1]), .d2 (d [2]),
        .qa (qa), .dor_a (dor_a), .dir_a (dir_a),
        .qb (qb), .dor_b (dor_b), .dir_b (dir_b),
        .qc (qc), .dor_c (dor_c), .dir_c (dir_c)
    );

    // The RTL version of P3: three FIFOs and the transfer condition

    wire [3:0] ra_q, rb_q, rc_q;
    wire       ra_empty, ra_full, rb_empty, rb_full, rc_empty, rc_full;

    wire go      = ~ ra_empty & ~ rb_empty & ~ rc_full;
    wire r_push_a = pushA & (~ ra_full | go);
    wire r_push_b = pushB & (~ rb_full | go);
    wire r_pop_c  = popC  & ~ rc_empty;

    ref_fifo ref_a (.clk (clk), .rst (rst), .push (r_push_a), .pop (go),
        .write_data ({ 1'b0, d }), .read_data (ra_q), .empty (ra_empty), .full (ra_full));

    ref_fifo ref_b (.clk (clk), .rst (rst), .push (r_push_b), .pop (go),
        .write_data ({ 1'b0, d }), .read_data (rb_q), .empty (rb_empty), .full (rb_full));

    ref_fifo ref_c (.clk (clk), .rst (rst), .push (go), .pop (r_pop_c),
        .write_data (ra_q + rb_q), .read_data (rc_q), .empty (rc_empty), .full (rc_full));

    int    n_moves  = 0;
    string popped_c = "";

    // The word that the breadboard pops at the next falling edge
    always @ (posedge clk)
        if (popC === 1'b1 && dor_c === 1'b1 && rst === 1'b0)
            popped_c = { popped_c, $sformatf (" %0d", qc) };

    always @ (posedge clk)
        if (checking && rst === 1'b0)
        begin
            n_edges ++;
            n_moves += go;
            `COMPARE_FIFO ("A", dut.u_a, ref_a, qa, dor_a, dir_a, 3)
            `COMPARE_FIFO ("B", dut.u_b, ref_b, qb, dor_b, dir_b, 3)
            `COMPARE_FIFO ("C", dut.u_c, ref_c, qc, dor_c, dir_c, 4)
            cover_full_a    += ra_full;
            cover_full_b    += rb_full;
            cover_full_c    += rc_full;
            cover_go_run    += go & go_before;          // pairs on consecutive clocks
            cover_full_a_go += pushA & ra_full & go;    // push into full A while a pair leaves
            cover_empty_c   += popC & rc_empty & go;    // pop C on empty C while a pair arrives
            go_before        = go;
        end

    bit go_before = 1'b0;
    int cover_full_a = 0, cover_full_b = 0, cover_full_c = 0, cover_go_run = 0, cover_full_a_go = 0, cover_empty_c = 0;

    final
        if (report)
            $display ("p3 coverage, %s corner: A full at %0d edges, B %0d, C %0d; pairs on consecutive clocks %0d; push into full A while a pair leaves %0d; pop C on empty C while a pair arrives %0d",
                corner_name (corner), cover_full_a, cover_full_b, cover_full_c, cover_go_run, cover_full_a_go, cover_empty_c);

    task automatic wait_before_edge (input time lead);
        @ (posedge clk);
        # (500 * ms - lead);
    endtask

    task automatic reset ();
        want [RST] = 1'b1;
        # (300 * ms);
        want [RST] = 1'b0;
        # (700 * ms);
    endtask

    // Hold a button for three clock periods; the data switches show
    // data [0], data [1], data [2] at the three rising edges

    task automatic hold_3 (input int b, input logic [2:0] d1, d2, d3);
        wait_before_edge (100 * ms);
        want [6:4] = d1;
        want [b]   = 1'b1;
        # (200 * ms);
        want [6:4] = d2;
        # (500 * ms);
        want [6:4] = d3;
        # (800 * ms);
        want [b]   = 1'b0;
        # (200 * ms);
        want [6:4] = 3'd0;
        # (1000 * ms);
    endtask

    task automatic cycle (input bit pa, input bit pb, input bit pc, input logic [2:0] data);
        @ (posedge clk);
        # (1 * us);
        want [PUSH_A] = pa;
        want [PUSH_B] = pb;
        want [POP_C]  = pc;
        want [6:4]    = data;
    endtask

    initial
    begin
        int    moves_before;
        int    k;

        done   = 1'b0;
        edges  = 0;
        moves  = 0;
        errors = 0;

        # (37_300_000);
        reset ();
        checking = 1'b1;

        // 1. Push A held for three clocks with 1, 2, 3; push B held with 4, 5, 6;
        //    then pop C held for three clocks

        moves_before = n_moves;
        hold_3 (PUSH_A, 3'd1, 3'd2, 3'd3);
        hold_3 (PUSH_B, 3'd4, 3'd5, 3'd6);

        if (report && corner == 0 && fault == 0)
            $display ("p3: push A and push B held for 3 clocks each: %0d pairs moved, C holds %0d words",
                n_moves - moves_before, dut.u_c.n_words);

        popped_c = "";
        wait_before_edge (100 * ms);
        want [POP_C] = 1'b1;
        # (1500 * ms);
        want [POP_C] = 1'b0;
        # (1000 * ms);

        if (report && corner == 0 && fault == 0)
            $display ("p3: pop C held for 3 clocks: popped%s, C holds %0d words", popped_c, dut.u_c.n_words);

        // 2. Random synchronous inputs.  The phases fill and drain A, B and C.

        use_bounce = 1'b0;

        for (int phase = 0; phase < 16; phase ++)
        begin
            int pa, pb, pc;
            case (phase % 4)
                0: begin pa = 70; pb = 70; pc = 10; end   // C fills up
                1: begin pa = 70; pb = 10; pc = 50; end   // A fills up
                2: begin pa = 10; pb = 30; pc = 90; end   // all drain
                3: begin pa = 50; pb = 50; pc = 50; end
            endcase

            repeat (150)
                cycle (rnd (100) < pa, rnd (100) < pb, rnd (100) < pc, 3' (rnd (8)));
        end

        cycle (0, 0, 0, 3'd0);

        // 3. Random button presses with bounce, and a few resets

        use_bounce = 1'b1;

        repeat (500)
        begin
            # (rnd (700_000) * us + 7);  // never exactly on a clock edge
            case (rnd (11))
                0, 1, 2:   want [PUSH_A] = ~ want [PUSH_A];
                3, 4, 5:   want [PUSH_B] = ~ want [PUSH_B];
                6, 7:      want [POP_C]  = ~ want [POP_C];
                8, 9:      begin k = 4 + rnd (3); want [k] = ~ want [k]; end
                default:   if (rnd (3) == 0)
                           begin
                               want [RST] = 1'b1;
                               # ((100 + rnd (500)) * ms);
                               want [RST] = 1'b0;
                           end
            endcase
        end

        want = '0;
        # (2000 * ms);

        errors = n_fail;
        edges  = n_edges;
        moves  = n_moves;
        done   = 1'b1;
    end

endmodule

//----------------------------------------------------------------------------
// Both tests in the five timing corners
//----------------------------------------------------------------------------

module tb_sync_proposal;

    import lssk_rules::*;

    parameter int fault = 0;

    localparam int N = 5;

    wire [N - 1:0]      done_bb8, done_p3;
    wire [32 * N - 1:0] err_bb8, err_p3, edges_bb8, edges_p3, moves_p3;

    for (genvar i = 0; i < N; i ++)
    begin : corner
        bb8_check # (.corner (i), .t_gate (timing (i, 0)), .t_ff (timing (i, 1)), .t_reg (timing (i, 2)),
            .t_flag (timing (i, 4)), .t_step (timing (i, 5)), .t_hold (timing (i, 6)),
            .fault (fault), .seed (i + 1), .report (1)) bb8
        (
            .done (done_bb8 [i]), .errors (err_bb8 [32 * i +: 32]), .edges (edges_bb8 [32 * i +: 32]),
            .moves ()
        );

        p3_check # (.corner (i), .t_gate (timing (i, 0)), .t_ff (timing (i, 1)), .t_reg (timing (i, 2)),
            .t_add (timing (i, 3)), .t_flag (timing (i, 4)), .t_step (timing (i, 5)), .t_hold (timing (i, 6)),
            .fault (fault), .seed (i + 11), .report (1)) p3
        (
            .done (done_p3 [i]), .errors (err_p3 [32 * i +: 32]), .edges (edges_p3 [32 * i +: 32]),
            .moves (moves_p3 [32 * i +: 32])
        );
    end

    initial
    begin
        int total;

        wait (& done_bb8 && & done_p3);

        total = violations;

        for (int i = 0; i < N; i ++)
        begin
            $display ("%-21s bb8: %0d errors in %0d edges;  p3: %0d errors in %0d edges, %0d pairs moved",
                { corner_name (i), ":" }, err_bb8 [32 * i +: 32], edges_bb8 [32 * i +: 32],
                err_p3 [32 * i +: 32], edges_p3 [32 * i +: 32], moves_p3 [32 * i +: 32]);
            total += err_bb8 [32 * i +: 32] + err_p3 [32 * i +: 32];
        end

        if (violations != 0)
            $display ("%0d violations of setup, hold or floating-input rules", violations);

        if (fault != 0 && total == 0)
            $display ("fault %0d: NOT DETECTED", fault);
        else if (fault != 0)
            $display ("fault %0d: detected", fault);
        else if (total == 0)
            $display ("PASS");
        else
            $display ("FAIL");

        $finish;
    end

endmodule
