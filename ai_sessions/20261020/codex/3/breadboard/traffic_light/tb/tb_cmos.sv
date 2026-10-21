// Simulation only. Chip pin truth tables and 4017 clock semantics.

module tb_cmos;

    timeunit 1ns;
    timeprecision 1ps;

    localparam period         = 20;
    localparam timeout_cycles = 500;

    logic clk     = 1'b0;
    logic inhibit = 1'b0;
    logic rst     = 1'b0;
    logic [7:0] a = '0;

    always # (period / 2) clk = ~ clk;

    logic [3:0] or2;
    logic [1:0] or4;
    logic [9:0] q;
    logic carry;

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
        if (q !== (10'b1 << expected) || carry !== (expected < 5))
            $fatal (1, "4017 state/carry mismatch: expected=%0d q=%b carry=%b",
                expected, q, carry);
    endtask

    task tick;
        @ (posedge clk);
        expected = rst ? 0 : inhibit ? expected : (expected + 1) % 10;
        # 1;  // Counter register and decoded output settling.
        check_counter ();
    endtask

    initial
    begin
        @ (posedge clk);
        # 1;  // Assert reset after the clock event, without a stimulus/DUT race.
        rst      = 1'b1;
        expected = 0;
        # 1;  // Check asynchronous reset before the next clock edge.
        check_counter ();

        // Inputs are changed after sampling, safely before the next clock edge.
        for (int i = 0; i < 256; i ++)
        begin
            a = 8' (i);
            tick ();

            if (   or2 !== { (| a [7:6]), (| a [5:4]), (| a [3:2]), (| a [1:0]) }
                || or4 !== { (| a [7:4]), (| a [3:0]) })
                $fatal (1, "OR pin truth-table mismatch input=%h", a);
        end

        rst = 1'b0;

        repeat (30)
            tick ();

        inhibit = 1'b1;
        # 1;  // Raising inhibit while CLOCK is high must not count.
        check_counter ();

        repeat (4)
            tick ();

        // Necessary exception: falling INHIBIT with CLOCK low must not count.
        // Posedge-only stimulus cannot test this half of the chip's truth table.
        @ (negedge clk);
        inhibit = 1'b0;
        # 1;  // Settle the effective clock and output decode before checking.
        check_counter ();

        tick ();

        inhibit = 1'b1;
        # 1;  // Raising inhibit with CLOCK high must not count.
        check_counter ();

        inhibit  = 1'b0;
        expected = (expected + 1) % 10;
        # 1;  // Falling inhibit with CLOCK high IS a count event.
        check_counter ();

        rst      = 1'b1;
        expected = 0;
        # 1;  // Reset must act without waiting for the next clock edge.
        check_counter ();

        inhibit = 1'b1;
        tick ();
        inhibit = 1'b0;
        # 1;  // Reset also dominates the falling-INHIBIT count event.
        check_counter ();

        repeat (2)
            tick ();

        $display ("PASS CMOS: 256 OR input combinations; 30 count edges; carry, inhibit and asynchronous reset");
        $finish;
    end

    initial
    begin
        repeat (timeout_cycles) @ (posedge clk);
        $fatal (1, "Timeout after %0d clock cycles", timeout_cycles);
    end

endmodule
