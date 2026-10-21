`timescale 1ns / 1ps
`default_nettype none

// Simulation only. Both core versions in all three integration wrappers.

module tb_integrations;

    logic clk = 1'b0, rst = 1'b0, ena = 1'b1;
    logic [7:0] ui = '0, key = '0;

    wire [7:0] lab_led  [0:1];
    wire [7:0] hack_led [0:1];
    wire [7:0] tt_out   [0:1];
    wire [7:0] tt_io    [0:1];
    wire [7:0] tt_oe    [0:1];

    int n = 0;
    logic [7:0] seven [0:9];
    logic [2:0] expected_lamps;
    logic [7:0] expected_segments;

    generate
        genvar k;

        for (k = 0; k < 2; k ++)
        begin : versions
            wire [99:0] lab_gpio;
            wire [ 3:0] hack_gpio;

            lab_top # (.CHIP_MODEL (k)) lab
            (
                .clk      (clk),
                .slow_clk (clk),
                .rst      (rst),
                .key      (key [3:0]),
                .sw       (8'b0),
                .led      (lab_led [k]),
                .abcdefgh (),
                .digit    (),
                .x        (10'b0),
                .y        (9'b0),
                .red      (),
                .green    (),
                .blue     (),
                .mic      (24'b0),
                .sound    (),
                .uart_rx  (1'b0),
                .uart_tx  (),
                .gpio     (lab_gpio)
            );

            hackathon_top # (.CHIP_MODEL (k)) hack
            (
                .clock      (clk),
                .slow_clock (clk),
                .reset      (rst),
                .key        (key),
                .led        (hack_led [k]),
                .abcdefgh   (),
                .digit      (),
                .x          (9'b0),
                .y          (9'b0),
                .red        (),
                .green      (),
                .blue       (),
                .gpio       (hack_gpio)
            );

            tt_um_timofei_traffic_light # (.USE_CHIP_MODEL (k)) tt
            (
                .ui_in   (ui),
                .uo_out  (tt_out [k]),
                .uio_in  (8'b0),
                .uio_out (tt_io [k]),
                .uio_oe  (tt_oe [k]),
                .ena     (ena),
                .clk     (clk),
                .rst_n   (~ rst)
            );
        end
    endgenerate

    task check_all;
        begin
            expected_lamps    = n < 4 ? 3'b001 : n < 6 ? 3'b010 : 3'b100;
            expected_segments = ui [0] ? seven [n] : n < 4 ? 8'h01 : n < 6 ? 8'h40 : 8'h08;

            # 1;

            for (int j = 0; j < 2; j ++)
            begin
                if (   lab_led  [j] !== { 5'b0, expected_lamps }
                    || hack_led [j] !== { 5'b0, expected_lamps })
                    $fatal (1, "BGM output mismatch state=%0d model=%0d", n, j);

                if (   tt_out [j] !== (ena ? expected_segments : 8'b0)
                    || tt_io  [j] !== (ena ? { 5'b0, expected_lamps } : 8'b0)
                    || tt_oe  [j] !== (ena ? 8'h07 : 8'b0))
                    $fatal (1, "Tiny Tapeout output mismatch state=%0d model=%0d", n, j);
            end
        end
    endtask

    initial
    begin
        seven [0] = 8'h3f;
        seven [1] = 8'h06;
        seven [2] = 8'h5b;
        seven [3] = 8'h4f;
        seven [4] = 8'h66;
        seven [5] = 8'h6d;
        seven [6] = 8'h7d;
        seven [7] = 8'h07;
        seven [8] = 8'h7f;
        seven [9] = 8'h6f;

        # 2;
        rst = 1'b1;
        check_all ();
        rst = 1'b0;
        check_all ();

        for (int i = 0; i < 30; i ++)
        begin
            ui = '0;
            check_all ();
            ui = 8'd1;
            check_all ();
            ena = 1'b0;
            check_all ();
            ena = 1'b1;

            # 4;
            clk = 1'b1;
            n = (n + 1) % 10;
            check_all ();

            # 4;
            clk = 1'b0;
            check_all ();
        end

        // BGM key[0] is a reset button. TT uses its dedicated rst_n.

        key = 8'd1;
        rst = 1'b1;
        n = 0;
        check_all ();
        key = '0;
        rst = 1'b0;
        check_all ();

        $display ("PASS integrations: both implementations in BGM lab/hackathon and Tiny Tapeout; 30 steps, both display modes, ena and reset");
        $finish;
    end

endmodule

`default_nettype wire
