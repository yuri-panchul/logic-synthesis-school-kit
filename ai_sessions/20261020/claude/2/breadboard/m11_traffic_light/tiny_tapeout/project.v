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

    // The light should change about once a second.  The demo board makes
    // clk itself and can set it anywhere from 1 Hz to 66.5 MHz, so set the
    // project clock to 1 Hz (clock_hz: 1 in info.yaml) and clk drives the
    // traffic light directly.  Do not make a slow clock from a counter in an
    // ASIC: keep one clock and use a clock enable when you need a slow tick.

    wire [9:0] q;
    wire       red, yellow, green;

    traffic_light i_traffic_light (
        .clk    ( clk      ),
        .rst    ( ~ rst_n  ),
        .q      ( q        ),
        .red    ( red      ),
        .yellow ( yellow   ),
        .green  ( green    )
    );

    // 7-segment display: uo_out [0] is segment a, ..., uo_out [6] is g,
    // uo_out [7] is the dot.  Segment a (top) is red, g (middle) yellow,
    // d (bottom) green.

    assign uo_out  = { 1'b0, yellow, 2'b0, green, 2'b0, red };

    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // List all unused inputs to prevent warnings

    wire _unused = & { ena, ui_in, uio_in, q, 1'b0 };

endmodule
