# A prompt for an LSSK exercise instruction

## Sources of information

*private article doc*

LSSK tab in
https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit?usp=sharing

https://habr.com/en/articles/1071736/

https://github.com/yuri-panchul/basics-graphics-music

https://verilog-meetup.com/2026/07/31/an-improved-way-of-teaching-school-kids-digital-electronics-using-venerable-small-scale-integration-ics/

https://verilog-meetup.com/2026/07/23/a-prequel-to-fpga-and-asic-design-using-small-scale-integration-chips/

https://makerfaire.com/maker/entry/learn-chip-design-from-breadboards-to-fpga-to-your-own-asic-78900/

## The purpose of exercises

Here is an announcement presentation I delivered at Maker Faire's New Product Showcase:

Logic Synthesis School Kit: from AND/OR gates on a breadboard to your own CPU on an FPGA. This is the name of a new project presented Maker Faire's New Product Showcase. Friday, September 25 · 2:00–5:00 p.m. at the Make: Le Tigre Stage.

The target audience is high school and university students interested in learning digital design.

Students begin by wiring simple chips on a breadboard, then move to SystemVerilog, the language professional chip designers use, to configure an FPGA (Field-Programmable Gate Array), a chip whose internal circuitry can be rewired after manufacturing. The exercises go well beyond the traditional AND/OR gates and counters. Students build finite state machines that recognize input sequences, such as a code lock, and round-robin arbiters that fairly share a resource among competing requests. Next they build processor building blocks such as FIFO buffers and arithmetic logic units (ALUs), first from medium-scale ICs on the breadboard, then in SystemVerilog on the FPGA. Finally, students build their own CPU inside the FPGA, based on the open
RISC-V architecture. Designed from the perspective of a working chip designer, the kit skips outdated busywork like hand-assembling clock generators and focuses on the skills modern chip design actually requires.

Why is the product significant?

Traditional breadboard education stops at gates, counters, and simple logic. Arduino and Raspberry Pi education jumps to software running on an already-designed processor. Neither teaches students how the processor itself is designed. Two levels of abstraction are missing: the register-transfer level (RTL), which describes how data moves between registers on each clock cycle, and the microarchitecture level, which describes how a CPU's pipeline and arithmetic blocks are organized. Also missing from high school electronics education is the core method of modern chip design: describing hardware in a language like SystemVerilog and letting synthesis tools turn it into circuits.

Our kit fills that gap by connecting classic breadboard exercises to FPGA-based design, so students see the whole path from a single gate to a working processor. This early, hands-on experience benefits not only future chip designers but any student who wants to understand how hardware and software interact in modern digital systems, from graphics processors to networking devices to machine-learning accelerators.

## SystemVerilog rules

## General plan

For an exercise create the following a single web page that has the following sections:

1. Exercise ID and name

Explanation what what it is. How it is used in digital designs. Why learning it is important.

2. Key logic or state element or block description

Symbol for the key components if necessary (OR, AND, XOR, NOT, D-flip-flop, Mux).

Truth table if necessary.

Waveform diagram if necessary.

3. Table of the parts you need

4. Functionality of each CMOS chip required

Pin diagram and pin description. Polarity

5. Schematic 1: gates, flip-flop and other elements in generic fashion, without link to a specific chip.

6. Schematic 2: connections between the chips but without placing them on breadboard

7. Schematics 3. breadboard diagram.

8. A synthesizable SystemVerilog design that corresponds to Schematic 1: gates, flip-flop and other elements in generic fashion, without link to a specific chip.

9. SystemVerilog modules for each CMOS chip used in the breadbord exercise. Preferrably synthesizable. At least with a comment whether it is a synthesizable or simulatable model.

10. A SystemVerilog design that corresponds to Schematic 2: connections between the chips. Should have the same interface as (8).

11. A testbench for (8) and (10). Should be compartible with Icarus Verilog 13, Questa and the latest Verilator.

12. How to instantiate (8) or (10) in lab_top module within Basics-Graphics-Music (BGM) infrastructure.

13. How to instantiate (8) or (10) in hackaton_top module within Basics-Graphics-Music (BGM) infrastructure.

14. How to instantiate (8) or (10) in project.v module in TinyTapeout infrastructure given the connections to switches and 7-segment display board:

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

15. Other information as necessary.

## The first instruction

First let's create such instruction for Timofei's design described in https://habr.com/en/articles/1071736/

"Также стоит отметить специальный случай конечного автомата, в котором N состояний меняются каждый такт по простому циклу 0 => 1 => 2 => … => N-1 => 0. Им является например простой светофор, который дает красный цвет 4 такта, желтый цвет 2 такта и зеленый цвет 4 такта. Такой конечный автомат можно построить с помощью десятичного счетчика 4017 с дешифрированными выходами и логических элементов OR: красный = S0 | S1 | S2 | S3; желтый = S4 | S5; зеленый = S6 | S7 | S8 | S9. "

Another description in:

*private article doc*

"Another teenager, Timofei Nikiforov, figured out how to construct an interesting case of a Finite State Machine (FSM) by OR-ing the outputs of the CMOS 4017 Decade Counter IC, which has ten decoded outputs. If you OR the outputs 1-4 and connect them to a red LED, then OR the outputs 5-6 and connect to a yellow LED, then OR the outputs 7-10 and connect to a green LED - you get a traffic light controller. Assuming your clock generator runs at 1 Hz, you will get red light for 4 seconds, yellow for 2 seconds, and green for 4 seconds."

Create a new directory "breadboard", put html, css and other files in there. Also create a page that lists all the exercises, but initially it should include only Timofei's traffic light FSM.

Create subdirectory for each exercise, put both SystemVerilog files there as well, generate all the necessary scripts to run Icarus Verilog, Questa and Verilator, as well as schematic images in PNG and SVG formats.

There should be two versions of the website - English and Russian, link each English Page with Russian page and vice versa.
