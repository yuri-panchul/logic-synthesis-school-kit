// Simulation only. Portable procedural checks; no classes, DPI or UVM.

module tb_traffic_light;

    timeunit 1ns;
    timeprecision 1ps;

    localparam period         = 20;
    localparam timeout_cycles = 500;

    logic clk = 1'b0;
    logic rst = 1'b0;

    always # (period / 2) clk = ~ clk;

    logic red_generic, yellow_generic, green_generic;
    logic red_chips, yellow_chips, green_chips;
    logic [9:0] state_generic, state_chips;

    int expected     = 0;
    int checks       = 0;
    int red_slots    = 0;
    int yellow_slots = 0;
    int green_slots  = 0;
    int visits [0:9];

    traffic_light generic_dut
    (
        .clk    (clk),
        .rst    (rst),
        .red    (red_generic),
        .yellow (yellow_generic),
        .green  (green_generic),
        .state  (state_generic)
    );

    traffic_light_chips chip_dut
    (
        .clk    (clk),
        .rst    (rst),
        .red    (red_chips),
        .yellow (yellow_chips),
        .green  (green_chips),
        .state  (state_chips)
    );

    task check_state;
        logic [9:0] wanted;
        logic [2:0] lamps;

        wanted = 10'b1 << expected;
        lamps  = expected < 4 ? 3'b100 : expected < 6 ? 3'b010 : 3'b001;

        if (   state_generic !== wanted
            || state_chips   !== wanted
            || { red_generic, yellow_generic, green_generic } !== lamps
            || { red_chips,   yellow_chips,   green_chips   } !== lamps)
        begin
            $fatal (1, "state=%0d generic=%b/%b chips=%b/%b",
                expected,
                state_generic, { red_generic, yellow_generic, green_generic },
                state_chips,   { red_chips,   yellow_chips,   green_chips   });
        end

        checks = checks + 1;
    endtask

    task tick;
        @ (posedge clk);
        expected = rst ? 0 : (expected + 1) % 10;
        # 1;  // Let register updates and lamp decoding settle before sampling.
        check_state ();
    endtask

    // Called between rising edges, after tick or the focused low-phase check.
    // Checking before the next clock edge distinguishes asynchronous reset.
    task reset_now;
        rst      = 1'b1;
        expected = 0;
        # 1;  // Asynchronous register update and combinational output settling.
        check_state ();
        rst = 1'b0;
    endtask

    initial
    begin
        $dumpfile ("traffic_light.vcd");
        $dumpvars (0, tb_traffic_light);

        for (int i = 0; i < 10; i ++)
            visits [i] = 0;

        @ (posedge clk);
        # 1;  // Place the initial reset after the clock event, without a race.
        reset_now ();

        for (int round = 0; round < 12; round ++)
            for (int i = 0; i < 10; i ++)
            begin
                visits [expected] = visits [expected] + 1;

                if (red_generic)
                    red_slots = red_slots + 1;

                if (yellow_generic)
                    yellow_slots = yellow_slots + 1;

                if (green_generic)
                    green_slots = green_slots + 1;

                tick ();
            end

        if (red_slots != 48 || yellow_slots != 24 || green_slots != 48)
            $fatal (1, "4/2/4 duration mismatch");

        for (int i = 0; i < 10; i ++)
            if (visits [i] != 12)
                $fatal (1, "Missing state %0d", i);

        // Reset from every state while CLOCK is high, then while it is low.
        for (int low_phase = 0; low_phase < 2; low_phase ++)
            for (int i = 0; i < 10; i ++)
            begin
                tick ();
                reset_now ();

                repeat (i)
                    tick ();

                if (low_phase != 0)
                begin
                    // Necessary exception: exercise reset with CLOCK low and
                    // verify that a falling clock edge does not advance state.
                    @ (negedge clk);
                    # 1;  // Observe any erroneous falling-edge state update.
                    check_state ();
                end

                reset_now ();
            end

        rst      = 1'b1;
        expected = 0;

        repeat (3)
            tick ();  // Reset dominates the clock.

        rst = 1'b0;
        tick ();

        $display ("PASS traffic_light: %0d checks; 12 full cycles; red/yellow/green=48/24/48; reset and wrap",
            checks);
        $finish;
    end

    initial
    begin
        repeat (timeout_cycles) @ (posedge clk);
        $fatal (1, "Timeout after %0d clock cycles", timeout_cycles);
    end

endmodule
