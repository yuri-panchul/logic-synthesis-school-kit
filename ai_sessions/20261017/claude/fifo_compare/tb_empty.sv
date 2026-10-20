`timescale 1ns/1ps
// Push and pop together on an empty FIFO: the case Codex's testbench rejects as illegal.
// Reference: the lab's lab_top gating, pop = ~empty & key[0], on the unchanged RTL.
module tb_empty;
  parameter SI_DELAY=40, SO_DELAY=80;
  localparam T=20000;
  reg clk=0,rst=0,push=0,pop=0; reg [3:0] data=4'h7;
  wire [3:0] hw_q, rtl_q; wire hw_e,hw_f,si,so,w,r, rtl_e,rtl_f;
  fifo40105_proposal #(.WIDTH(4),.SI_DELAY(SI_DELAY),.SO_DELAY(SO_DELAY)) dut
    (clk,rst,push,pop,data,hw_q,hw_e,hw_f,si,so,w,r);
  flip_flop_fifo_empty_full_optimized_and_debug_2 #(.width(4),.depth(16)) ref_gated
    (.clk(clk),.rst(rst),.push(push & ~rtl_f),.pop(pop & ~rtl_e),.write_data(data),
     .read_data(rtl_q),.empty(rtl_e),.full(rtl_f),.debug_ptrs(),.debug_valid(),.debug_data());
  always #(T/2) clk=~clk;
  initial begin
    #1000 rst=1; #2000 rst=0;
    @(negedge clk); push=1; pop=1;          // both buttons on the same edge, FIFO empty
    @(negedge clk); push=0; pop=0;
    @(negedge clk); #(T/4);
    $display("SI_delay=%0d SO_delay=%0d  circuit: empty=%b q=%h   RTL with lab_top gating: empty=%b q=%h  -> %s",
      SI_DELAY,SO_DELAY,hw_e,hw_q,rtl_e,rtl_q,(hw_e===rtl_e)?"same":"DIFFERENT");
    $finish;
  end
endmodule
