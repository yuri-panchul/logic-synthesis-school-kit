// CD4072B: dual 4-input OR gate.
//
// Ports in pin order, named as in the datasheet.  The power pins, VSS (7)
// and VDD (14), are left out, and so are the unconnected pins 6 and 8.
// Synthesizable.

module cd4072
(
    output logic j,  // Pin 1:  j = a | b | c | d
    input  logic a,  // Pin 2
    input  logic b,  // Pin 3
    input  logic c,  // Pin 4
    input  logic d,  // Pin 5
                     // Pin 6:  not connected
                     // Pin 7:  VSS
                     // Pin 8:  not connected
    input  logic e,  // Pin 9
    input  logic f,  // Pin 10
    input  logic g,  // Pin 11
    input  logic h,  // Pin 12
    output logic k   // Pin 13: k = e | f | g | h
                     // Pin 14: VDD
);

    assign j = a | b | c | d;
    assign k = e | f | g | h;

endmodule
