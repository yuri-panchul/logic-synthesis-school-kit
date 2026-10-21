`timescale 1ns/1ps
`default_nettype none
module tb_cmos;
    reg [7:0] a=0;
    wire [3:0] or2;
    wire [1:0] or4;
    reg clk=0, inhibit=0, rst=0;
    wire [9:0] q;
    wire carry;
    integer i,expected=0;
    cd4071b g2(a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],or2[0],or2[1],or2[2],or2[3]);
    cd4072b g4(a[0],a[1],a[2],a[3],or4[0],a[4],a[5],a[6],a[7],or4[1]);
    cd4017b counter(clk,inhibit,rst,q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],carry);
    task check_counter;
        begin
            #1;
            if(q!==(10'b1<<expected) || carry!==(expected<5))
                $fatal(1,"4017 state/carry mismatch: expected=%0d q=%b carry=%b",expected,q,carry);
        end
    endtask
    initial begin
        for(i=0;i<256;i=i+1) begin
            a=8'(i); #1;
            if(or2 !== {(|a[7:6]),(|a[5:4]),(|a[3:2]),(|a[1:0])} || or4 !== {(|a[7:4]),(|a[3:0])})
                $fatal(1,"OR pin truth-table mismatch input=%h",a);
        end
        rst=1;expected=0;check_counter();rst=0;
        for(i=0;i<30;i=i+1) begin
            #2;clk=1;expected=(expected+1)%10;check_counter();
            #2;clk=0;check_counter();
        end
        inhibit=1;
        repeat(4) begin #2;clk=1;check_counter();#2;clk=0;check_counter();end
        // Releasing inhibit when CLOCK is low is not a count event.
        inhibit=0;check_counter();
        // A rising clock counts; raising inhibit while clock is high does not.
        clk=1;expected=1;check_counter();inhibit=1;check_counter();
        // Falling inhibit while CLOCK is high counts according to the chip function.
        inhibit=0;expected=2;check_counter();
        rst=1;expected=0;check_counter();inhibit=1;clk=0;check_counter();
        clk=1;check_counter();inhibit=0;check_counter(); // reset dominates both clock inputs
        $display("PASS CMOS: 256 OR input combinations; 30 count edges; carry, inhibit and asynchronous reset");
        $finish;
    end
endmodule
`default_nettype wire
