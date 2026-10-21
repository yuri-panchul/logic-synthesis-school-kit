// CD4017B: CMOS decade counter with 10 decoded outputs.
//
// Model of the chip as seen at its pins.  The power pins, VDD (16) and VSS (8),
// are left out.  Synthesizable.
//
// The chip counts on a rising edge of CLOCK while CLOCK INHIBIT is low, and
// also on a falling edge of CLOCK INHIBIT while CLOCK is high: CLOCK INHIBIT
// gates the clock.  The model does the same with an AND gate in the clock path.
// In an FPGA design keep clock_inhibit at 0; then the gate is just a wire.
//
// Inside, the counter is a 5-stage Johnson counter with a decoder, the same
// circuit as traffic_light.sv.  The real chip also has extra gates that bring
// the counter into the ten-state sequence from any state after power-up;
// the model needs a reset instead.

module cd4017
(
    input  logic       clock,          // Pin 14
    input  logic       clock_inhibit,  // Pin 13: 1 = hold the count
    input  logic       reset,          // Pin 15: 1 = count 0 (Q0 = 1) at once

    output logic [9:0] q,              // Pins 3 2 4 7 10 1 5 6 9 11 = Q0 ... Q9
    output logic       carry_out       // Pin 12: 1 for counts 0-4, 0 for counts 5-9
);

    wire gated_clock = clock & ~ clock_inhibit;

    logic [4:0] r;

    always_ff @ (posedge gated_clock or posedge reset)
        if (reset)
            r <= '0;
        else
            r <= { r [3:0], ~ r [4] };

    assign q [0] = ~ r [4] & ~ r [0];
    assign q [1] =   r [0] & ~ r [1];
    assign q [2] =   r [1] & ~ r [2];
    assign q [3] =   r [2] & ~ r [3];
    assign q [4] =   r [3] & ~ r [4];
    assign q [5] =   r [4] &   r [0];
    assign q [6] = ~ r [0] &   r [1];
    assign q [7] = ~ r [1] &   r [2];
    assign q [8] = ~ r [2] &   r [3];
    assign q [9] = ~ r [3] &   r [4];

    assign carry_out = ~ r [4];

endmodule
