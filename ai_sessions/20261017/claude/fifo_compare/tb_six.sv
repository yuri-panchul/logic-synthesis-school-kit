`timescale 1ns/1ps
// The six-cycle scenario the user gave Codex, run on both circuits and the RTL:
// push A, push B, push C, push D + pop, push E + pop, pop.  A..E = 1..5.
module tb_six;
  localparam T = 20000;                       // 50 kHz: the low half is 10 us, far above the 40105 ripple time
  reg clk = 0, rst = 0, push = 0, pop = 0;
  reg [2:0] d = 0;
  always #(T/2) clk = ~clk;

  wire [3:0] mq;  wire mdor, mdir;            // mine: BB8 variant B, typical corner
  bb8_sync mine (.clk(clk), .rst(rst), .push(push), .pop(pop), .d0(d[0]), .d1(d[1]), .d2(d[2]),
                 .q(mq), .dor(mdor), .dir(mdir));
  wire [3:0] cq;  wire ce, cf, si, so, w, r;  // Codex: fifo40105_proposal, 4 x 16
  fifo40105_proposal #(.WIDTH(4)) codex (clk, rst, push, pop, {1'b0,d}, cq, ce, cf, si, so, w, r);
  wire [3:0] rq;  wire re, rf;                // the unchanged RTL, width 4, depth 16
  flip_flop_fifo_empty_full_optimized_and_debug_2 #(.width(4), .depth(16)) rtl
    (.clk(clk), .rst(rst), .push(push), .pop(pop), .write_data({1'b0,d}), .read_data(rq),
     .empty(re), .full(rf), .debug_ptrs(), .debug_valid(), .debug_data());

  task cyc (input p, input pp, input [2:0] v, input integer n);
    begin
      push = p; pop = pp; d = v;              // called in the low half, before the edge
      @(posedge clk); #1;
      @(negedge clk); #(T/4);                 // settled, after the falling-edge strobes
      $display("cycle %0d  push=%b pop=%b data=%0d | RTL head=%0d empty=%b | mine head=%0d empty=%b | Codex head=%0d empty=%b",
               n, p, pp, v, rq, re, mq, ~mdor, cq, ce);
    end
  endtask
  initial begin
    #(T/4) rst = 1; #(T) rst = 0;
    @(negedge clk); #(T/4);
    cyc(1,0,1,1); cyc(1,0,2,2); cyc(1,0,3,3); cyc(1,1,4,4); cyc(1,1,5,5); cyc(0,1,0,6);
    // drain and print what is left
    push = 0; pop = 1;
    repeat (2) begin @(posedge clk); #1; @(negedge clk); #(T/4);
      $display("drain     | RTL head=%0d empty=%b | mine head=%0d empty=%b | Codex head=%0d empty=%b", rq, re, mq, ~mdor, cq, ce); end
    $finish;
  end
endmodule
