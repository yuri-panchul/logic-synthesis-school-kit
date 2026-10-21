`timescale 1ns/1ps
`default_nettype none
// Simulation only. Portable procedural checks; no classes, DPI or UVM.
module tb_traffic_light;
    reg clk = 1'b0;
    reg rst = 1'b0;
    wire r0,y0,g0,r1,y1,g1;
    wire [9:0] s0,s1;
    integer expected = 0;
    integer checks = 0;
    integer visits [0:9];
    integer red_slots = 0, yellow_slots = 0, green_slots = 0;
    integer i,round;
    traffic_light generic_dut(clk,rst,r0,y0,g0,s0);
    traffic_light_chips chip_dut(clk,rst,r1,y1,g1,s1);

    task check_state;
        reg [9:0] wanted;
        reg [2:0] lamps;
        begin
            wanted = 10'b1 << expected;
            if (expected < 4) lamps=3'b100;
            else if (expected < 6) lamps=3'b010;
            else lamps=3'b001;
            if (s0 !== wanted || s1 !== wanted || {r0,y0,g0} !== lamps || {r1,y1,g1} !== lamps)
                $fatal(1,"state=%0d generic=%b/%b chips=%b/%b",expected,s0,{r0,y0,g0},s1,{r1,y1,g1});
            checks=checks+1;
        end
    endtask
    task pulse;
        begin
            #4; clk=1'b1;
            expected=rst ? 0 : (expected+1)%10;
            #1; check_state();
            #4; clk=1'b0;
            #1; check_state(); // no advance on the falling edge
        end
    endtask
    task reset_at_current_level;
        begin
            #2; rst=1'b1; expected=0;
            #1; check_state(); // reset does not wait for a clock edge
            #2; rst=1'b0;
            #1; check_state();
        end
    endtask
    initial begin
        $dumpfile("traffic_light.vcd");
        $dumpvars(0,tb_traffic_light);
        for(i=0;i<10;i=i+1) visits[i]=0;
        reset_at_current_level();
        for(round=0;round<12;round=round+1)
            for(i=0;i<10;i=i+1) begin
                visits[expected]=visits[expected]+1;
                if(r0) red_slots=red_slots+1;
                if(y0) yellow_slots=yellow_slots+1;
                if(g0) green_slots=green_slots+1;
                pulse();
            end
        if(red_slots!=48 || yellow_slots!=24 || green_slots!=48)
            $fatal(1,"4/2/4 duration mismatch");
        for(i=0;i<10;i=i+1)
            if(visits[i]!=12) $fatal(1,"missing state %0d",i);
        // Asynchronous reset from every reachable state, at both clock levels.
        for(round=0;round<2;round=round+1)
            for(i=0;i<10;i=i+1) begin
                reset_at_current_level(); clk=1'b0;
                repeat(i) pulse();
                if(round==1) begin clk=1'b1; expected=(expected+1)%10; #1; end
                reset_at_current_level(); clk=1'b0; #1; check_state();
            end
        rst=1'b1; expected=0; #1;
        repeat(3) pulse(); // reset dominates the clock
        rst=1'b0; #1; check_state();
        $display("PASS traffic_light: %0d checks; 12 full cycles; red/yellow/green=48/24/48; reset and wrap",checks);
        $finish;
    end
    initial begin #100000; $fatal(1,"timeout"); end
endmodule
`default_nettype wire
