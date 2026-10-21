`timescale 1ns / 1ps
`default_nettype none

// Synthesizable Tiny Tapeout top; compile as SystemVerilog.
// Set the external project clock to 1 Hz.
// Set USE_CHIP_MODEL to 1 to synthesize the pin-connected version.

module tt_um_timofei_traffic_light
# (
    parameter USE_CHIP_MODEL = 0
)
(
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    wire red, yellow, green;
    wire [9:0] state;

    generate
        if (USE_CHIP_MODEL == 0)
        begin : generic_version
            traffic_light dut
            (
                .clk    (clk),
                .rst    (~ rst_n),
                .red    (red),
                .yellow (yellow),
                .green  (green),
                .state  (state)
            );
        end
        else
        begin : chip_version
            traffic_light_chips dut
            (
                .clk    (clk),
                .rst    (~ rst_n),
                .red    (red),
                .yellow (yellow),
                .green  (green),
                .state  (state)
            );
        end
    endgenerate

    // TT output order [7:0] = { dp, g, f, e, d, c, b, a }; active high.
    // DIP 0 = 0: top/middle/bottom bar represents red/yellow/green.
    // DIP 0 = 1: show state number 0..9, not seconds remaining.

    logic [7:0] decimal_segments;

    always_comb
    begin
        decimal_segments = '0;

        case (state)
        10'b00_0000_0001: decimal_segments = 8'h3f;
        10'b00_0000_0010: decimal_segments = 8'h06;
        10'b00_0000_0100: decimal_segments = 8'h5b;
        10'b00_0000_1000: decimal_segments = 8'h4f;
        10'b00_0001_0000: decimal_segments = 8'h66;
        10'b00_0010_0000: decimal_segments = 8'h6d;
        10'b00_0100_0000: decimal_segments = 8'h7d;
        10'b00_1000_0000: decimal_segments = 8'h07;
        10'b01_0000_0000: decimal_segments = 8'h7f;
        10'b10_0000_0000: decimal_segments = 8'h6f;
        default:         decimal_segments = '0;
        endcase
    end

    wire [7:0] bars = { 1'b0, yellow, 2'b00, green, 2'b00, red };

    assign uo_out  = ena ? (ui_in [0] ? decimal_segments : bars) : '0;
    assign uio_out = ena ? { 5'b0, green, yellow, red } : '0;
    assign uio_oe  = ena ? 8'b0000_0111 : '0;

    wire unused_inputs = & { 1'b0, ui_in [7:1], uio_in };

endmodule

`default_nettype wire
