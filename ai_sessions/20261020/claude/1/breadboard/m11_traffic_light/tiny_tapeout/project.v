/*
 * Exercise M11 on Tiny Tapeout: Timofei's traffic light on the 7-segment
 * display of the demo board.
 *
 * Add traffic_light.sv to source_files in info.yaml next to project.v.
 * Rename the module to tt_um_<your GitHub name>_<project name> and use the
 * same name as top_module in info.yaml.
 */

`default_nettype none

module tt_um_example (
    input  wire [7:0] ui_in,    // DIP switches, INPUT Pmod, RP2350 GPIO17-24
    output wire [7:0] uo_out,   // 7-segment display, OUTPUT Pmod, RP2350 GPIO33-40
    input  wire [7:0] uio_in,   // BIDIR Pmod, RP2350 GPIO25-32
    output wire [7:0] uio_out,  //   (same pins)
    output wire [7:0] uio_oe,   //   1 = your design drives the pin
    input  wire       ena,      // set by the on-chip project mux, not a board pin
    input  wire       clk,      // RP2350 GPIO16
    input  wire       rst_n     // RP2350 GPIO14
);

    // The light should change about once a second, much slower than clk.
    // A counter divides clk, and DIP switches 1-5 (ui_in [4:0] = n) choose
    // its bit: slow_clk = clk / 2 ^ (n + 1).  With clk at 10 MHz, n = 22
    // (switches 5-1 = 10110) gives 1.2 Hz.  DIP switch 8 (ui_in [7]) = 1
    // runs the light from clk itself, for stepping the clock by hand.
    //
    // Like slow_clk in BGM, slow_clk is a counter bit used as a clock.
    // The generic design has no clock enable, and at about 1 Hz the timing
    // of this clock does not matter.  Change the switches during reset.

    reg [31:0] div;

    always @ (posedge clk or negedge rst_n)
        if (! rst_n)
            div <= 32'd0;
        else
            div <= div + 32'd1;

    wire slow_clk = ui_in [7] ? clk : div [ui_in [4:0]];

    wire [9:0] q;
    wire       red, yellow, green;

    traffic_light i_traffic_light (
        .clk    ( slow_clk ),
        .rst    ( ~ rst_n  ),
        .q      ( q        ),
        .red    ( red      ),
        .yellow ( yellow   ),
        .green  ( green    )
    );

    // 7-segment display: uo_out [0] is segment a, ..., uo_out [6] is g,
    // uo_out [7] is the dot.  Segment a (top) is red, g (middle) yellow,
    // d (bottom) green, and the dot blinks with slow_clk.

    assign uo_out  = { slow_clk, yellow, 2'b0, green, 2'b0, red };

    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // List all unused inputs to prevent warnings

    wire _unused = & { ena, ui_in [6:5], uio_in, q, 1'b0 };

endmodule
