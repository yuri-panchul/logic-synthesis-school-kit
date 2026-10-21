// Testbench for exercise M11.
//
// Runs the generic design (traffic_light.sv) and the chip-level design
// (traffic_light_chips.sv) side by side and compares both with a reference
// model: a state number from 0 to 9 and the colour that belongs to it.
// Works with Icarus Verilog, Verilator (--binary) and Questa.

module tb;

    logic       clk;
    logic       rst;

    logic [9:0] q,      q_chips;
    logic       red,    red_chips;
    logic       yellow, yellow_chips;
    logic       green,  green_chips;

    traffic_light i_generic
    (
        .clk    ( clk    ),
        .rst    ( rst    ),
        .q      ( q      ),
        .red    ( red    ),
        .yellow ( yellow ),
        .green  ( green  )
    );

    traffic_light_chips i_chips
    (
        .clk    ( clk          ),
        .rst    ( rst          ),
        .q      ( q_chips      ),
        .red    ( red_chips    ),
        .yellow ( yellow_chips ),
        .green  ( green_chips  )
    );

    //------------------------------------------------------------------------
    // Clock with a period of 10 time units.
    // On the breadboard one period is about a second.

    initial
    begin
        clk = 1'b0;

        forever
            # 5 clk = ~ clk;
    end

    //------------------------------------------------------------------------
    // Reference model: the number of the state

    logic [3:0] state;

    always @ (posedge clk or posedge rst)
        if (rst)
            state <= 4'd0;
        else if (state == 4'd9)
            state <= 4'd0;
        else
            state <= state + 4'd1;

    wire [9:0] q_expected      = 10'b1 << state;
    wire       red_expected    = state <= 4'd3;
    wire       yellow_expected = state == 4'd4 || state == 4'd5;
    wire       green_expected  = state >= 4'd6;

    //------------------------------------------------------------------------
    // Checks at every falling edge, half a period after the state changes

    int cycle, n_checks, n_errors;

    function automatic string light_name (input logic r, input logic y, input logic g);
        case ({ r, y, g })
        3'b100:  return "red   ";
        3'b010:  return "yellow";
        3'b001:  return "green ";
        3'b000:  return "dark  ";
        default: return "mixed ";
        endcase
    endfunction

    function automatic logic is_correct
    (
        input logic [9:0] q_actual,
        input logic       r,
        input logic       y,
        input logic       g
    );
        return    q_actual === q_expected
               && r        === red_expected
               && y        === yellow_expected
               && g        === green_expected;
    endfunction

    // Clock cycles of each colour during the first full period after reset

    int n_red, n_yellow, n_green, n_period;

    initial
    begin
        cycle    = 0;
        n_checks = 0;
        n_errors = 0;
        n_red    = 0;
        n_yellow = 0;
        n_green  = 0;
        n_period = 0;

        forever
        begin
            logic ok_generic, ok_chips;

            @ (negedge clk);
            cycle ++;

            ok_generic = is_correct (q,       red,       yellow,       green);
            ok_chips   = is_correct (q_chips, red_chips, yellow_chips, green_chips);

            n_checks += 2;

            if (! ok_generic)
                n_errors ++;

            if (! ok_chips)
                n_errors ++;

            $display ("%5d  %b    %b  %s  %s  %s",
                cycle, rst, q, light_name (red, yellow, green),
                ok_generic ? "ok     " : "WRONG  ", ok_chips ? "ok" : "WRONG");

            if (! rst && n_period < 10)
            begin
                n_period ++;

                if (red)
                    n_red ++;

                if (yellow)
                    n_yellow ++;

                if (green)
                    n_green ++;
            end
        end
    end

    //------------------------------------------------------------------------
    // Stimulus

    initial
    begin
        $dumpfile ("tb.vcd");

        `ifdef __ICARUS__
            $dumpvars (0, tb);  // Without a scope Icarus also tries to dump $unit
        `else
            $dumpvars;
        `endif

        $display ("cycle  rst  Q9..Q0      light   generic  chips");

        // Reset at the start, released between two clock edges

        rst = 1'b1;
        # 12 rst = 1'b0;

        repeat (24) @ (posedge clk);

        // Reset in the middle of a state: both designs go to state 0 at once,
        // without waiting for the clock, like RESET of the 4017

        # 2 rst = 1'b1;
        repeat (2) @ (posedge clk);
        # 7 rst = 1'b0;

        repeat (12) @ (posedge clk);
        @ (negedge clk);
        # 1;  // Let the last check print first

        $display ("One period after reset: red %0d, yellow %0d, green %0d clock cycles",
            n_red, n_yellow, n_green);

        if (n_errors == 0 && n_red == 4 && n_yellow == 2 && n_green == 4)
            $display ("PASS: %0d checks, no errors", n_checks);
        else
            $display ("FAIL: %0d errors in %0d checks", n_errors, n_checks);

        $finish;
    end

endmodule
