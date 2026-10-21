`timescale 1ns / 1ps
`default_nettype none

// The BGM module is spelled hackathon_top, with "h".

module hackathon_top
# (
    parameter CHIP_MODEL = 0
)
(
    input  wire       clock,
    input  wire       slow_clock,
    input  wire       reset,

    input  wire [7:0] key,
    output wire [7:0] led,

    // A dynamic seven-segment display

    output wire [7:0] abcdefgh,
    output wire [7:0] digit,

    // LCD screen interface

    input  wire [8:0] x,
    input  wire [8:0] y,

    output wire [4:0] red,
    output wire [5:0] green,
    output wire [4:0] blue,

    inout  wire [3:0] gpio
);

    wire lamp_red, lamp_yellow, lamp_green;
    wire [9:0] state;

    wire exercise_reset = reset | key [0];

    generate
        if (CHIP_MODEL == 0)
        begin : generic_version
            traffic_light dut
            (
                .clk    (slow_clock),
                .rst    (exercise_reset),
                .red    (lamp_red),
                .yellow (lamp_yellow),
                .green  (lamp_green),
                .state  (state)
            );
        end
        else
        begin : chip_version
            traffic_light_chips dut
            (
                .clk    (slow_clock),
                .rst    (exercise_reset),
                .red    (lamp_red),
                .yellow (lamp_yellow),
                .green  (lamp_green),
                .state  (state)
            );
        end
    endgenerate

    assign led      = { 5'b0, lamp_green, lamp_yellow, lamp_red };
    assign red      = { 5 { lamp_red   | lamp_yellow } };
    assign green    = { 6 { lamp_green | lamp_yellow } };
    assign blue     = '0;
    assign abcdefgh = '0;
    assign digit    = '0;
    assign gpio     = 'z;

    wire unused_inputs = & { 1'b0, clock, key, x, y, state };

endmodule

`default_nettype wire
