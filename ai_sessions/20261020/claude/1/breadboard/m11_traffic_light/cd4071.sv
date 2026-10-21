// CD4071B: quad 2-input OR gate.
//
// Ports in pin order, named as in the datasheet.  The power pins, VSS (7)
// and VDD (14), are left out.  Synthesizable.

module cd4071
(
    input  logic a,  // Pin 1
    input  logic b,  // Pin 2
    output logic j,  // Pin 3:  j = a | b
    output logic k,  // Pin 4:  k = c | d
    input  logic c,  // Pin 5
    input  logic d,  // Pin 6
                     // Pin 7:  VSS
    input  logic e,  // Pin 8
    input  logic f,  // Pin 9
    output logic l,  // Pin 10: l = e | f
    output logic m,  // Pin 11: m = g | h
    input  logic g,  // Pin 12
    input  logic h   // Pin 13
                     // Pin 14: VDD
);

    assign j = a | b;
    assign k = c | d;
    assign l = e | f;
    assign m = g | h;

endmodule
