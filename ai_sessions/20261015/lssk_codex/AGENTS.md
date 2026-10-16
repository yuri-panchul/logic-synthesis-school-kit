Read the following materials:

https://docs.google.com/document/d/1lVcfQOqSg-6YrX_VTWy0q345JGLUEWaLRE-17egVzpo/edit?usp=sharing

LSSK tab in
https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit?usp=sharing

https://habr.com/en/articles/1071736/

https://verilog-meetup.com/2026/07/31/an-improved-way-of-teaching-school-kids-digital-electronics-using-venerable-small-scale-integration-ics/

https://verilog-meetup.com/2026/07/23/a-prequel-to-fpga-and-asic-design-using-small-scale-integration-chips/

Create two instructions how to start - one in Russian, another in English based on images in https://verilog-meetup.com/2026/07/23/a-prequel-to-fpga-and-asic-design-using-small-scale-integration-chips/ and parts from https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit?usp=sharing

Both instructions should be in HTML.

Next create an HTML file with a list of all breadboard exercises mentioned in https://verilog-meetup.com/2026/07/31/an-improved-way-of-teaching-school-kids-digital-electronics-using-venerable-small-scale-integration-ics/ and https://habr.com/en/articles/1071736/ (they overlap). For each exercise put a list of the necessary components from https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit?usp=sharing , including the number of jumpers, leds or led arrays etc.

Then create five spreadsheets (CSV files) and five HTML files with lists of components needed for the following five kits:

1. Basics, the minimum exercises to cover basic exercises in my list.

2. Comprehensive, to cover all the exercises.

3. FIFO exercise.

4. 2-request round robin arbiter exercise.

5. FSM kit exercise with an option to give the student his own custom FSM task to design a circuit that recognizes a specific sequences of pressing the button.

Estimate the number of jumpers, buttons etc with cost and price to sell such a kit.



For the background information here is a presentation I delivered at Maker Faire's New Product Showcase:

Logic Synthesis School Kit: from AND/OR gates on a breadboard to your own CPU on an FPGA. This is the name of a new project presented Maker Faire's New Product Showcase. Friday, September 25 · 2:00–5:00 p.m. at the Make: Le Tigre Stage.

The target audience is high school and university students interested in learning digital design.

Students begin by wiring simple chips on a breadboard, then move to SystemVerilog, the language professional chip designers use, to configure an FPGA (Field-Programmable Gate Array), a chip whose internal circuitry can be rewired after manufacturing. The exercises go well beyond the traditional AND/OR gates and counters. Students build finite state machines that recognize input sequences, such as a code lock, and round-robin arbiters that fairly share a resource among competing requests. Next they build processor building blocks such as FIFO buffers and arithmetic logic units (ALUs), first from medium-scale ICs on the breadboard, then in SystemVerilog on the FPGA. Finally, students build their own CPU inside the FPGA, based on the open
RISC-V architecture. Designed from the perspective of a working chip designer, the kit skips outdated busywork like hand-assembling clock generators and focuses on the skills modern chip design actually requires.

Why is the product significant?

Traditional breadboard education stops at gates, counters, and simple logic. Arduino and Raspberry Pi education jumps to software running on an already-designed processor. Neither teaches students how the processor itself is designed. Two levels of abstraction are missing: the register-transfer level (RTL), which describes how data moves between registers on each clock cycle, and the microarchitecture level, which describes how a CPU's pipeline and arithmetic blocks are organized. Also missing from high school electronics education is the core method of modern chip design: describing hardware in a language like SystemVerilog and letting synthesis tools turn it into circuits.

Our kit fills that gap by connecting classic breadboard exercises to FPGA-based design, so students see the whole path from a single gate to a working processor. This early, hands-on experience benefits not only future chip designers but any student who wants to understand how hardware and software interact in modern digital systems, from graphics processors to networking devices to machine-learning accelerators.
