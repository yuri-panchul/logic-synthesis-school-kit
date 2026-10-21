// Simulation only. Both core versions in all three integration wrappers.

module tb_integrations;

    timeunit 1ns;
    timeprecision 1ps;

    localparam period         = 20;
    localparam timeout_cycles = 200;

    logic clk = 1'b0;
    logic rst = 1'b0;
    logic ena = 1'b1;

    always # (period / 2) clk = ~ clk;

    logic [7:0] ui  = '0;
    logic [7:0] key = '0;

    logic [7:0] lab_led  [0:1];
    logic [7:0] hack_led [0:1];
    logic [7:0] tt_out   [0:1];
    logic [7:0] tt_io    [0:1];
    logic [7:0] tt_oe    [0:1];

    int n_bgm = 0;
    int n_tt  = 0;
    logic [7:0] seven [0:9];

    generate
        genvar k;

        for (k = 0; k < 2; k ++)
        begin : versions
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
                .gpio     ()
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
                .gpio       ()
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
        logic [2:0] bgm_lamps;
        logic [2:0] tt_lamps;
        logic [7:0] segments;

        bgm_lamps = n_bgm < 4 ? 3'b001 : n_bgm < 6 ? 3'b010 : 3'b100;
        tt_lamps  = n_tt  < 4 ? 3'b001 : n_tt  < 6 ? 3'b010 : 3'b100;
        segments  = ui [0] ? seven [n_tt] : n_tt < 4 ? 8'h01 : n_tt < 6 ? 8'h40 : 8'h08;

        for (int j = 0; j < 2; j ++)
        begin
            if (   lab_led  [j] !== { 5'b0, bgm_lamps }
                || hack_led [j] !== { 5'b0, bgm_lamps })
                $fatal (1, "BGM output mismatch state=%0d model=%0d", n_bgm, j);

            if (   tt_out [j] !== (ena ? segments : 8'b0)
                || tt_io  [j] !== (ena ? { 5'b0, tt_lamps } : 8'b0)
                || tt_oe  [j] !== (ena ? 8'h07 : 8'b0))
                $fatal (1, "Tiny Tapeout output mismatch state=%0d model=%0d", n_tt, j);
        end
    endtask

    task tick;
        @ (posedge clk);
        n_bgm = rst || key [0] ? 0 : (n_bgm + 1) % 10;
        n_tt  = rst           ? 0 : (n_tt  + 1) % 10;
        # 1;  // Register updates and wrapper output decoding must settle.
        check_all ();
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

        @ (posedge clk);
        # 1;  // Drive reset after the clock event, without a stimulus/DUT race.
        rst   = 1'b1;
        n_bgm = 0;
        n_tt  = 0;
        # 1;  // Asynchronous reset must be observable before the next clock.
        check_all ();
        rst = 1'b0;

        // Each display mode sees all ten states; stimulus changes after sampling.
        for (int i = 0; i < 30; i ++)
        begin
            ui = 8' ((i / 10) % 2);
            tick ();
        end

        // ena blanks TT outputs but must not stop the internal state sequence.
        ena = 1'b0;

        repeat (3)
            tick ();

        ena = 1'b1;
        # 1;  // Combinational output-enable and display settling.
        check_all ();

        // Check the BGM reset button independently of the dedicated TT reset.
        key   = 8'd1;
        n_bgm = 0;
        # 1;  // Asynchronous button reset; TT must retain its own state.
        check_all ();

        repeat (2)
            tick ();

        key = '0;
        tick ();

        rst   = 1'b1;
        n_bgm = 0;
        n_tt  = 0;
        # 1;  // Asynchronous dedicated reset in all wrappers.
        check_all ();

        repeat (2)
            tick ();

        rst = 1'b0;
        tick ();

        $display ("PASS integrations: both implementations in BGM lab/hackathon and Tiny Tapeout; 30 steps, both display modes, 3 disabled cycles, independent button and dedicated resets");
        $finish;
    end

    initial
    begin
        repeat (timeout_cycles) @ (posedge clk);
        $fatal (1, "Timeout after %0d clock cycles", timeout_cycles);
    end

endmodule
