// Testbench for exercise M11.
//
// Runs the generic design (traffic_light.sv) and the chip-level design
// (traffic_light_chips.sv) side by side and compares both with a reference
// model: a state number from 0 to 9 and the colour that belongs to it.
// Works with Icarus Verilog, Verilator (--binary) and Questa.
//
// Like the testbenches of Basics-Graphics-Music, it drives and samples
// signals only at rising clock edges.

module tb;

    logic       clk;
    logic       rst;

    wire  [9:0] q,      q_chips;
    wire        red,    red_chips;
    wire        yellow, yellow_chips;
    wire        green,  green_chips;

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
        clk = '0;

        forever
            # 5 clk = ~ clk;
    end

    //------------------------------------------------------------------------
    // Reference model: the number of the state.
    // Like RESET of the 4017, rst sets state 0 at once, without the clock.

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

    wire ok_generic =    q            === q_expected
                      && red          === red_expected
                      && yellow       === yellow_expected
                      && green        === green_expected;

    wire ok_chips   =    q_chips      === q_expected
                      && red_chips    === red_expected
                      && yellow_chips === yellow_expected
                      && green_chips  === green_expected;

    //------------------------------------------------------------------------
    // Checking at every rising clock edge.  At the edge both designs and the
    // model still show the clock cycle that ends there, the same values that
    // a flip-flop would sample.

    function automatic string light_name (input logic r, input logic y, input logic g);
        case ({ r, y, g })
        3'b100:  return "red   ";
        3'b010:  return "yellow";
        3'b001:  return "green ";
        3'b000:  return "dark  ";
        default: return "mixed ";
        endcase
    endfunction

    // Initial values are fine in a testbench, and the checker samples rst at
    // the clock edge on purpose, although the designs reset asynchronously

    // verilator lint_off PROCASSINIT
    // verilator lint_off SYNCASYNCNET

    logic was_reset = 1'b0;
    logic done      = 1'b0;  // Set by the stimulus before $finish

    int cycle    = 0;
    int n_checks = 0;
    int n_errors = 0;

    // Clock cycles of each colour during the first full period after reset

    int n_period = 0;
    int n_red    = 0;
    int n_yellow = 0;
    int n_green  = 0;

    always @ (posedge clk)
    begin
        if (rst)
            was_reset <= 1'b1;

        if ((rst | was_reset) & ~ done)
        begin
            cycle    <= cycle + 1;
            n_checks <= n_checks + 2;
            n_errors <= n_errors + (ok_generic ? 0 : 1) + (ok_chips ? 0 : 1);

            $display ("%5d  %b    %b  %s  %s  %s",
                cycle + 1, rst, q, light_name (red, yellow, green),
                ok_generic ? "ok     " : "WRONG  ", ok_chips ? "ok" : "WRONG");
        end

        if (was_reset & ~ rst & n_period < 10)
        begin
            n_period <= n_period + 1;
            n_red    <= n_red    + (red    ? 1 : 0);
            n_yellow <= n_yellow + (yellow ? 1 : 0);
            n_green  <= n_green  + (green  ? 1 : 0);
        end
    end

    //------------------------------------------------------------------------
    // Driving reset

    initial
    begin
        $dumpfile ("tb.vcd");

        `ifdef __ICARUS__
            $dumpvars (0, tb);  // Without a scope Icarus also tries to dump $unit
        `else
            $dumpvars;
        `endif

        $display ("cycle  rst  Q9..Q0      light   generic  chips");

        // Before reset the state is unknown, as after power-up

        rst <= 'x;
        repeat (3) @ (posedge clk);
        rst <= '1;
        repeat (3) @ (posedge clk);
        rst <= '0;

        repeat (24) @ (posedge clk);

        // Reset in the middle of the ring.  Both designs must go to state 0
        // at once, not at the next clock edge, like RESET of the 4017.

        rst <= '1;
        repeat (2) @ (posedge clk);
        rst <= '0;

        repeat (12) @ (posedge clk);

        // Stop checking one clock edge before $finish, so that every
        // simulator reports the same number of checks

        done <= '1;
        @ (posedge clk);

        $finish;
    end

    //------------------------------------------------------------------------

    final
    begin
        $display ("One period after reset: red %0d, yellow %0d, green %0d clock cycles",
            n_red, n_yellow, n_green);

        if (n_errors == 0 && n_red == 4 && n_yellow == 2 && n_green == 4)
            $display ("PASS: %0d checks, no errors", n_checks);
        else
            $display ("FAIL: %0d errors in %0d checks", n_errors, n_checks);
    end

endmodule
