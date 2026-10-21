`timescale 1ns / 1ps
`default_nettype none

// Simulation only. Portable procedural checks; no classes, DPI or UVM.

module tb_traffic_light;

    logic clk = 1'b0;
    logic rst = 1'b0;

    wire red_generic, yellow_generic, green_generic;
    wire red_chips, yellow_chips, green_chips;
    wire [9:0] state_generic, state_chips;

    int expected = 0;
    int checks   = 0;
    int visits [0:9];
    int red_slots = 0, yellow_slots = 0, green_slots = 0;

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
        begin
            wanted = 10'b1 << expected;

            if (expected < 4)
                lamps = 3'b100;
            else if (expected < 6)
                lamps = 3'b010;
            else
                lamps = 3'b001;

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
        end
    endtask

    task pulse;
        begin
            # 4;
            clk = 1'b1;
            expected = rst ? 0 : (expected + 1) % 10;

            # 1;
            check_state ();

            # 4;
            clk = 1'b0;

            # 1;
            check_state ();  // No advance on the falling edge.
        end
    endtask

    task reset_at_current_level;
        begin
            # 2;
            rst = 1'b1;
            expected = 0;

            # 1;
            check_state ();  // Reset does not wait for a clock edge.

            # 2;
            rst = 1'b0;

            # 1;
            check_state ();
        end
    endtask

    initial
    begin
        $dumpfile ("traffic_light.vcd");
        $dumpvars (0, tb_traffic_light);

        for (int i = 0; i < 10; i ++)
            visits [i] = 0;

        reset_at_current_level ();

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

                pulse ();
            end

        if (red_slots != 48 || yellow_slots != 24 || green_slots != 48)
            $fatal (1, "4/2/4 duration mismatch");

        for (int i = 0; i < 10; i ++)
            if (visits [i] != 12)
                $fatal (1, "Missing state %0d", i);

        // Asynchronous reset from every reachable state, at both clock levels.

        for (int round = 0; round < 2; round ++)
            for (int i = 0; i < 10; i ++)
            begin
                reset_at_current_level ();
                clk = 1'b0;

                repeat (i)
                    pulse ();

                if (round == 1)
                begin
                    clk = 1'b1;
                    expected = (expected + 1) % 10;
                    # 1;
                end

                reset_at_current_level ();
                clk = 1'b0;
                # 1;
                check_state ();
            end

        rst = 1'b1;
        expected = 0;
        # 1;

        repeat (3)
            pulse ();  // Reset dominates the clock.

        rst = 1'b0;
        # 1;
        check_state ();

        $display ("PASS traffic_light: %0d checks; 12 full cycles; red/yellow/green=48/24/48; reset and wrap",
            checks);
        $finish;
    end

    initial
    begin
        # 100000;
        $fatal (1, "Timeout");
    end

endmodule

`default_nettype wire
