`timescale 1ns/1ps
`default_nettype none
// Full BGM lab interface. Requires w_key>=1 and w_led>=3.
module lab_top
# (
    parameter  CHIP_MODEL = 0,
               clk_mhz       = 50,
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
    input wire clk,
    input wire slow_clk,
    input wire rst,

    // Keys, switches, LEDs

    input wire [w_key   - 1:0] key,
    input wire [w_sw    - 1:0] sw,
    output logic [w_led   - 1:0] led,

    // A dynamic seven-segment display

    output logic [          7:0] abcdefgh,
    output logic [w_digit - 1:0] digit,

    // Graphics

    input wire [w_x     - 1:0] x,
    input wire [w_y     - 1:0] y,

    output logic [w_red   - 1:0] red,
    output logic [w_green - 1:0] green,
    output logic [w_blue  - 1:0] blue,

    // Microphone, sound output and UART

    input wire [         23:0] mic,
    output wire [         15:0] sound,

    input wire uart_rx,
    output wire uart_tx,

    // General-purpose Input/Output

    inout wire [w_gpio  - 1:0] gpio
);


    wire lamp_red, lamp_yellow, lamp_green;
    wire [9:0] state;
    wire exercise_reset = rst | key[0];
    generate
        if (CHIP_MODEL == 0) begin : generic_version
            traffic_light dut(slow_clk,exercise_reset,lamp_red,lamp_yellow,lamp_green,state);
        end else begin : chip_version
            traffic_light_chips dut(slow_clk,exercise_reset,lamp_red,lamp_yellow,lamp_green,state);
        end
    endgenerate
    // Infrastructure LEDs and graphics use active-high logical signals.
    assign led = w_led'({5'b0,lamp_green,lamp_yellow,lamp_red});
    assign red   = {w_red{lamp_red | lamp_yellow}};
    assign green = {w_green{lamp_green | lamp_yellow}};
    assign blue = '0;
    assign abcdefgh = '0;
    assign digit = '0;
    assign sound = '0;
    assign uart_tx = 1'b1;
    assign gpio = 'z;
    wire unused_inputs = &{1'b0,clk,sw,key,x,y,mic,uart_rx,state};
endmodule
`default_nettype wire
