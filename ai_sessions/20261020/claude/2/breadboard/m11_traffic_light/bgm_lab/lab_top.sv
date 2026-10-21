// Exercise M11 on an FPGA board with the Basics-Graphics-Music (BGM) labs:
// https://github.com/yuri-panchul/basics-graphics-music
//
// Copy a lab directory, for example labs/1_basics/1_06_binary_counter,
// replace its lab_top.sv with this file and add traffic_light.sv.
// For the chip-level design add traffic_light_chips.sv, cd4017.sv, cd4071.sv
// and cd4072.sv instead, and change the module name below.
//
// The traffic light runs from slow_clk, the 1 Hz clock that every BGM board
// wrapper makes, so it changes state once a second, like the breadboard with
// the 555 module.  Reset is the reset button of the board.
// The 7-segment display shows the light: segment a red, g yellow, d green.
// The LEDs show the state as a running light.

`include "config.svh"

module lab_top
# (
    parameter  clk_mhz       = 50,
               w_key         = 4,
               w_sw          = 8,
               w_led         = 8,
               w_digit       = 8,
               w_gpio        = 100,

               screen_width  = 640,
               screen_height = 480,

               w_red         = 4,
               w_green       = 4,
               w_blue        = 4,

               w_x           = $clog2 ( screen_width  ),
               w_y           = $clog2 ( screen_height )
)
(
    input                        clk,
    input                        slow_clk,
    input                        rst,

    // Keys, switches, LEDs

    input        [w_key   - 1:0] key,
    input        [w_sw    - 1:0] sw,
    output logic [w_led   - 1:0] led,

    // A dynamic seven-segment display

    output logic [          7:0] abcdefgh,
    output logic [w_digit - 1:0] digit,

    // Graphics

    input        [w_x     - 1:0] x,
    input        [w_y     - 1:0] y,

    output logic [w_red   - 1:0] red,
    output logic [w_green - 1:0] green,
    output logic [w_blue  - 1:0] blue,

    // Microphone, sound output and UART

    input        [         23:0] mic,
    output       [         15:0] sound,

    input                        uart_rx,
    output                       uart_tx,

    // General-purpose Input/Output

    inout        [w_gpio  - 1:0] gpio
);

    //------------------------------------------------------------------------

       assign red        = '0;
       assign green      = '0;
       assign blue       = '0;
       assign sound      = '0;
       assign uart_tx    = '1;

    //------------------------------------------------------------------------

    // lab_top already has ports named red and green (the screen colours),
    // so the lights get other names here

    logic [9:0] q;
    logic       light_red, light_yellow, light_green;

    traffic_light i_traffic_light
    (
        .clk    ( slow_clk     ),
        .rst    ( rst          ),
        .q      ( q            ),
        .red    ( light_red    ),
        .yellow ( light_yellow ),
        .green  ( light_green  )
    );

    //------------------------------------------------------------------------

    //   --a--
    //  |     |
    //  f     b
    //  |     |
    //   --g--
    //  |     |
    //  e     c
    //  |     |
    //   --d--  h

    assign abcdefgh = { light_red, 2'b0, light_green, 2'b0, light_yellow, 1'b0 };
    assign digit    = w_digit' (1);

    assign led      = w_led' (q);

endmodule
