`timescale 1ns/1ps
`default_nettype none
module tb_integrations;
    reg clk=0,rst=0,ena=1;
    reg [7:0] ui=0,key=0;
    wire [7:0] lab_led[0:1],hack_led[0:1],tt_out[0:1],tt_io[0:1],tt_oe[0:1];
    integer i,j,n=0;
    reg [7:0] seven[0:9];
    reg [2:0] expected_lamps;
    reg [7:0] expected_segments;
    genvar k;
    generate for(k=0;k<2;k=k+1) begin : versions
        wire [99:0] lab_gpio;
        wire [3:0] hack_gpio;
        lab_top #(.CHIP_MODEL(k)) lab(
            .clk(clk),.slow_clk(clk),.rst(rst),.key(key[3:0]),.sw(8'b0),.led(lab_led[k]),
            .abcdefgh(),.digit(),.x(10'b0),.y(9'b0),.red(),.green(),.blue(),
            .mic(24'b0),.sound(),.uart_rx(1'b0),.uart_tx(),.gpio(lab_gpio));
        hackathon_top #(.CHIP_MODEL(k)) hack(
            .clock(clk),.slow_clock(clk),.reset(rst),.key(key),.led(hack_led[k]),
            .abcdefgh(),.digit(),.x(9'b0),.y(9'b0),.red(),.green(),.blue(),.gpio(hack_gpio));
        tt_um_timofei_traffic_light #(.USE_CHIP_MODEL(k)) tt(
            .ui_in(ui),.uo_out(tt_out[k]),.uio_in(8'b0),.uio_out(tt_io[k]),.uio_oe(tt_oe[k]),
            .ena(ena),.clk(clk),.rst_n(~rst));
    end endgenerate
    task check_all;
        begin
            expected_lamps=n<4 ? 3'b001 : n<6 ? 3'b010 : 3'b100;
            expected_segments=ui[0] ? seven[n] : n<4 ? 8'h01 : n<6 ? 8'h40 : 8'h08;
            #1;
            for(j=0;j<2;j=j+1) begin
                if(lab_led[j]!=={5'b0,expected_lamps} || hack_led[j]!=={5'b0,expected_lamps})
                    $fatal(1,"BGM output mismatch state=%0d model=%0d",n,j);
                if(tt_out[j]!==(ena ? expected_segments : 8'b0) || tt_io[j]!==(ena ? {5'b0,expected_lamps} : 8'b0) || tt_oe[j]!==(ena ? 8'h07 : 8'b0))
                    $fatal(1,"Tiny Tapeout output mismatch state=%0d model=%0d",n,j);
            end
        end
    endtask
    initial begin
        seven[0]=8'h3f;seven[1]=8'h06;seven[2]=8'h5b;seven[3]=8'h4f;seven[4]=8'h66;
        seven[5]=8'h6d;seven[6]=8'h7d;seven[7]=8'h07;seven[8]=8'h7f;seven[9]=8'h6f;
        #2;rst=1;check_all();rst=0;check_all();
        for(i=0;i<30;i=i+1) begin
            ui=0;check_all();ui=1;check_all();ena=0;check_all();ena=1;
            #4;clk=1;n=(n+1)%10;check_all();#4;clk=0;check_all();
        end
        // BGM's key[0] is a reset button. TT uses its dedicated rst_n.
        key=1;rst=1;n=0;check_all();key=0;rst=0;check_all();
        $display("PASS integrations: both implementations in BGM lab/hackathon and Tiny Tapeout; 30 steps, both display modes, ena and reset");
        $finish;
    end
endmodule
`default_nettype wire
