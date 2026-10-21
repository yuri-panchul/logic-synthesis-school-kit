`timescale 1ns / 1ps
`default_nettype none

// Simulation only. Chip pin truth tables and 4017 clock semantics.

module tb_cmos;

    logic [7:0] a = '0;
    logic clk = 1'b0, inhibit = 1'b0, rst = 1'b0;

    wire [3:0] or2;
    wire [1:0] or4;
    wire [9:0] q;
    wire carry;

    int expected = 0;

    cd4071b g2
    (
        .p1_a  (a [0]),
        .p2_b  (a [1]),
        .p5_c  (a [2]),
        .p6_d  (a [3]),
        .p8_e  (a [4]),
        .p9_f  (a [5]),
        .p12_g (a [6]),
        .p13_h (a [7]),
        .p3_j  (or2 [0]),
        .p4_k  (or2 [1]),
        .p10_l (or2 [2]),
        .p11_m (or2 [3])
    );

    cd4072b g4
    (
        .p2_a  (a [0]),
        .p3_b  (a [1]),
        .p4_c  (a [2]),
        .p5_d  (a [3]),
        .p1_j  (or4 [0]),
        .p9_e  (a [4]),
        .p10_f (a [5]),
        .p11_g (a [6]),
        .p12_h (a [7]),
        .p13_k (or4 [1])
    );

    cd4017b counter
    (
        .p14_clock   (clk),
        .p13_inhibit (inhibit),
        .p15_reset   (rst),
        .p3_q0       (q [0]),
        .p2_q1       (q [1]),
        .p4_q2       (q [2]),
        .p7_q3       (q [3]),
        .p10_q4      (q [4]),
        .p1_q5       (q [5]),
        .p5_q6       (q [6]),
        .p6_q7       (q [7]),
        .p9_q8       (q [8]),
        .p11_q9      (q [9]),
        .p12_carry   (carry)
    );

    task check_counter;
        begin
            # 1;

            if (q !== (10'b1 << expected) || carry !== (expected < 5))
                $fatal (1, "4017 state/carry mismatch: expected=%0d q=%b carry=%b",
                    expected, q, carry);
        end
    endtask

    initial
    begin
        for (int i = 0; i < 256; i ++)
        begin
            a = 8' (i);
            # 1;

            if (   or2 !== { (| a [7:6]), (| a [5:4]), (| a [3:2]), (| a [1:0]) }
                || or4 !== { (| a [7:4]), (| a [3:0]) })
                $fatal (1, "OR pin truth-table mismatch input=%h", a);
        end

        rst = 1'b1;
        expected = 0;
        check_counter ();
        rst = 1'b0;

        for (int i = 0; i < 30; i ++)
        begin
            # 2;
            clk = 1'b1;
            expected = (expected + 1) % 10;
            check_counter ();

            # 2;
            clk = 1'b0;
            check_counter ();
        end

        inhibit = 1'b1;

        repeat (4)
        begin
            # 2;
            clk = 1'b1;
            check_counter ();

            # 2;
            clk = 1'b0;
            check_counter ();
        end

        // Releasing inhibit when CLOCK is low is not a count event.

        inhibit = 1'b0;
        check_counter ();

        // A rising clock counts; raising inhibit while CLOCK is high does not.

        clk = 1'b1;
        expected = 1;
        check_counter ();
        inhibit = 1'b1;
        check_counter ();

        // Falling inhibit while CLOCK is high counts.

        inhibit = 1'b0;
        expected = 2;
        check_counter ();

        // Reset dominates both clock inputs.

        rst = 1'b1;
        expected = 0;
        check_counter ();
        inhibit = 1'b1;
        clk = 1'b0;
        check_counter ();
        clk = 1'b1;
        check_counter ();
        inhibit = 1'b0;
        check_counter ();

        $display ("PASS CMOS: 256 OR input combinations; 30 count edges; carry, inhibit and asynchronous reset");
        $finish;
    end

endmodule

`default_nettype wire
