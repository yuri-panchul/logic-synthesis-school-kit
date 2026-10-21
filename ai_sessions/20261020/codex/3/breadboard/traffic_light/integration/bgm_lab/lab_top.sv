// Full BGM lab interface. Requires w_key >= 1 and w_led >= 3.

module lab_top
# (
    parameter CHIP_MODEL    = 0,
    parameter clk_mhz       = 50,
    parameter w_key         = 4,
    parameter w_sw          = 8,
    parameter w_led         = 8,
    parameter w_digit       = 8,
    parameter w_gpio        = 100,

    parameter screen_width  = 640,
    parameter screen_height = 480,

    parameter w_red         = 4,
    parameter w_green       = 4,
    parameter w_blue        = 4,

    parameter w_x           = $clog2 (screen_width),
    parameter w_y           = $clog2 (screen_height)
)
(
    input                  clk,
    input                  slow_clk,
    input                  rst,

    // Keys, switches, LEDs

    input  [w_key   - 1:0] key,
    input  [w_sw    - 1:0] sw,
    output [w_led   - 1:0] led,

    // A dynamic seven-segment display

    output [          7:0] abcdefgh,
    output [w_digit - 1:0] digit,

    // Graphics

    input  [w_x     - 1:0] x,
    input  [w_y     - 1:0] y,

    output [w_red   - 1:0] red,
    output [w_green - 1:0] green,
    output [w_blue  - 1:0] blue,

    // Microphone, sound output and UART

    input  [         23:0] mic,
    output [         15:0] sound,

    input                  uart_rx,
    output                 uart_tx,

    // General-purpose Input/Output

    inout  [w_gpio  - 1:0] gpio
);

    timeunit 1ns;
    timeprecision 1ps;

    logic lamp_red, lamp_yellow, lamp_green;
    logic [9:0] state;

    wire exercise_reset = rst | key [0];

    generate
        if (CHIP_MODEL == 0)
        begin : generic_version
            traffic_light dut
            (
                .clk    (slow_clk),
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
                .clk    (slow_clk),
                .rst    (exercise_reset),
                .red    (lamp_red),
                .yellow (lamp_yellow),
                .green  (lamp_green),
                .state  (state)
            );
        end
    endgenerate

    // Infrastructure LEDs and graphics use active-high logical signals.

    assign led      = w_led' ({ 5'b0, lamp_green, lamp_yellow, lamp_red });
    assign red      = { w_red   { lamp_red   | lamp_yellow } };
    assign green    = { w_green { lamp_green | lamp_yellow } };
    assign blue     = '0;
    assign abcdefgh = '0;
    assign digit    = '0;
    assign sound    = '0;
    assign uart_tx  = 1'b1;
    assign gpio     = 'z;

    wire unused_inputs = & { 1'b0, clk, sw, key, x, y, mic, uart_rx, state };

endmodule
