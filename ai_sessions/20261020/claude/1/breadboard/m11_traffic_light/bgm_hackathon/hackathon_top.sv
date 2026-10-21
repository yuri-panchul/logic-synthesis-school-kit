// Board configuration: tang_nano_9k_lcd_480_272_tm1638_hackathon
// This module uses few parameterization and relaxed typing rules

// Exercise M11 in the hackathon setup of Basics-Graphics-Music (BGM):
// https://github.com/yuri-panchul/basics-graphics-music
//
// Copy a directory such as hackathon/problems/4_binary_counter, replace its
// hackathon_top.sv with this file and add traffic_light.sv.
//
// The traffic light runs from slow_clock, one beat per second, like the
// breadboard with the 555 module.  The screen shows a traffic light,
// the 7-segment display shows it too (segment a red, g yellow, d green),
// and the eight LEDs show states 0-7 as a running light.

module hackathon_top
(
    input  logic       clock,
    input  logic       slow_clock,
    input  logic       reset,

    input  logic [7:0] key,
    output logic [7:0] led,

    // A dynamic seven-segment display

    output logic [7:0] abcdefgh,
    output logic [7:0] digit,

    // LCD screen interface

    input  logic [8:0] x,
    input  logic [8:0] y,

    output logic [4:0] red,
    output logic [5:0] green,
    output logic [4:0] blue,

    inout  logic [3:0] gpio
);

    //------------------------------------------------------------------------
    // The screen colours are called red and green already,
    // so the lights get other names

    logic [9:0] q;
    logic       light_red, light_yellow, light_green;

    traffic_light i_traffic_light
    (
        .clk    ( slow_clock   ),
        .rst    ( reset        ),
        .q      ( q            ),
        .red    ( light_red    ),
        .yellow ( light_yellow ),
        .green  ( light_green  )
    );

    assign led      = q [7:0];

    assign abcdefgh = { light_red, 2'b0, light_green, 2'b0, light_yellow, 1'b0 };
    assign digit    = 8'b0000_0001;

    //------------------------------------------------------------------------
    // A traffic light on the 480 x 272 screen: three round lamps in a dark box.
    // dx is the distance from the middle of the screen, dy1-dy3 the distances
    // from the centres of the lamps, so a lamp is where dx * dx + dy * dy < 34 * 34.

    wire [8:0] dx  = x > 240 ? x - 240 : 240 - x;
    wire [8:0] dy1 = y > 56  ? y - 56  : 56  - y;
    wire [8:0] dy2 = y > 136 ? y - 136 : 136 - y;
    wire [8:0] dy3 = y > 216 ? y - 216 : 216 - y;

    wire lamp1 = dx * dx + dy1 * dy1 < 34 * 34;
    wire lamp2 = dx * dx + dy2 * dy2 < 34 * 34;
    wire lamp3 = dx * dx + dy3 * dy3 < 34 * 34;

    always_comb
    begin
        red   = 0;
        green = 0;
        blue  = 0;

        if (x >= 196 & x < 284 & y >= 12 & y < 260)
        begin
            red   = 3;
            green = 6;
            blue  = 3;
        end

        if (lamp1)
        begin
            red   = light_red ? 31 : 7;
            green = 0;
            blue  = 0;
        end

        if (lamp2)
        begin
            red   = light_yellow ? 31 : 7;
            green = light_yellow ? 50 : 11;
            blue  = 0;
        end

        if (lamp3)
        begin
            red   = 0;
            green = light_green ? 63 : 14;
            blue  = light_green ? 8  : 2;
        end
    end

endmodule
