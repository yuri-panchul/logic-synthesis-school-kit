#!/usr/bin/env python3
"""Compare the unmodified supplied RTL with independent transaction queues.

This checks width=4, depth=16 behavior, not a CD74HC40105 breadboard adapter.
The three archived RTL sources include config.svh but use no definitions from
it. A temporary empty include satisfies that dependency without changing RTL.
"""
from collections import Counter, deque
from pathlib import Path
import hashlib
import json
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'research/reference'
DEPTH = 16
MASK = 15


def make_vectors():
    a, b, sums = deque(), deque(), deque()
    vectors, accepted = [], []
    coverage = Counter()

    def outputs():
        return int(len(a) < DEPTH), int(len(b) < DEPTH), int(bool(sums)), sums[0] if sums else 0

    def cycle(av=0, bv=0, sr=0, ad=0, bd=0, rst=0):
        if rst:
            a.clear(); b.clear(); sums.clear()
            coverage['resets'] += 1
        before = outputs()
        if not rst:
            join = bool(a and b and len(sums) < DEPTH)
            push_a, push_b = av and before[0], bv and before[1]
            pop_sum = sr and before[2]
            coverage['joins'] += join
            coverage['join_without_external_buttons'] += join and not (av or bv or sr)
            coverage['output_full_stall'] += bool(a and b and len(sums) == DEPTH)
            coverage['full_output_pop_without_join'] += bool(a and b and len(sums) == DEPTH and pop_sum)
            coverage['input_a_full'] += len(a) == DEPTH
            coverage['input_b_full'] += len(b) == DEPTH
            coverage['simultaneous_input_join_output'] += bool(push_a and push_b and join and pop_sum)
            coverage['a_waiting_for_b'] += bool(a and not b)
            coverage['b_waiting_for_a'] += bool(b and not a)
            if pop_sum:
                accepted.append(sums.popleft())
            # A join consumes old heads, before either new input is appended.
            if join:
                total = a.popleft() + b.popleft()
                coverage['arithmetic_overflow'] += total > MASK
                sums.append(total & MASK)
            if push_a:
                a.append(ad)
            if push_b:
                b.append(bd)
        vectors.append((rst, av, bv, sr, ad, bd, *before, *outputs()))

    cycle(rst=1)
    for value in [1, 2, 3]: cycle(av=1, ad=value)
    for _ in range(4): cycle()
    for value in [4, 5, 6]: cycle(bv=1, bd=value)
    for _ in range(4): cycle()
    for _ in range(6): cycle(sr=1)
    assert accepted == [5, 7, 9], accepted
    cycle(rst=1)
    # Saturate SUM, then A and B. Pop from full SUM: the supplied RTL
    # intentionally waits another cycle before accepting the next joined pair.
    for n in range(64): cycle(av=1, bv=1, ad=n & MASK, bd=(n+7) & MASK)
    cycle(sr=1)
    for _ in range(100): cycle(sr=1)
    # Independently fill the opposite operand queue and release it later.
    for n in range(24): cycle(bv=1, bd=n & MASK)
    for n in range(24): cycle(av=1, sr=1, ad=(n+3) & MASK)
    for _ in range(24): cycle(sr=1)
    for n in range(50): cycle(av=1, bv=1, sr=1, ad=n & MASK, bd=15)
    # Reset with queued work, then exercise deterministic random stalls.
    for _ in range(5): cycle(av=1, bv=1, ad=15, bd=15)
    cycle(rst=1)
    rng = random.Random(20261015)
    for n in range(2000):
        cycle(av=rng.randrange(2), bv=rng.randrange(2), sr=rng.randrange(2),
              ad=rng.randrange(16), bd=rng.randrange(16), rst=int(n in [731, 1549]))
    for _ in range(100): cycle(sr=1)
    cycle(rst=1)
    for _ in range(3): cycle(sr=1)
    for label in ['joins', 'join_without_external_buttons', 'output_full_stall',
                  'full_output_pop_without_join', 'input_a_full', 'input_b_full',
                  'simultaneous_input_join_output', 'a_waiting_for_b',
                  'b_waiting_for_a', 'arithmetic_overflow', 'resets']:
        assert coverage[label] > 0, label
    return vectors, coverage


TB = r'''`timescale 1ns/1ps
module tb;
    reg clk=0, rst=1, av=0, bv=0, sr=0;
    reg [3:0] ad=0, bd=0;
    wire ar, br, sv;
    wire [3:0] sd;
    always #5 clk=~clk;
    a_plus_b_using_wrapped_fifos #(.width(4), .depth(16)) dut
      (.clk(clk), .rst(rst), .a_valid(av), .a_ready(ar), .a_data(ad),
       .b_valid(bv), .b_ready(br), .b_data(bd),
       .sum_valid(sv), .sum_ready(sr), .sum_data(sd));
    integer f, count=0, fields;
    integer ir, ia, ib, isr, iad, ibd;
    integer pre_ar, pre_br, pre_sv, pre_sd, post_ar, post_br, post_sv, post_sd;
    task check;
        input integer ea, eb, ev, ed;
        input integer phase;
        begin
            if (ar !== ea[0] || br !== eb[0] || sv !== ev[0] ||
                (ev != 0 && sd !== ed[3:0]))
                $fatal(1, "cycle=%0d phase=%0d actual ar/br/sv/sd=%b/%b/%b/%h expected=%0d/%0d/%0d/%h",
                       count, phase, ar, br, sv, sd, ea, eb, ev, ed[3:0]);
        end
    endtask
    initial begin
        // Ensure an asynchronous reset event before the first vector.
        #1 rst=0; #1 rst=1;
        f=$fopen("vectors.txt", "r");
        if (!f) $fatal(1, "Cannot open vectors");
        while (!$feof(f)) begin
            fields=$fscanf(f, "%d %d %d %d %d %d %d %d %d %d %d %d %d %d\n",
                ir, ia, ib, isr, iad, ibd,
                pre_ar, pre_br, pre_sv, pre_sd, post_ar, post_br, post_sv, post_sd);
            if (fields == 14) begin
                @(negedge clk);
                rst=ir; av=ia; bv=ib; sr=isr; ad=iad; bd=ibd;
                #1; check(pre_ar, pre_br, pre_sv, pre_sd, 0);
                @(posedge clk);
                #1; check(post_ar, post_br, post_sv, post_sd, 1);
                count=count+1;
            end else if (fields != -1) $fatal(1, "Invalid vector");
        end
        $fclose(f);
        $display("PASS supplied FIFO RTL: %0d cycles, outputs checked before and after every edge", count);
        $finish;
    end
endmodule
'''


def main():
    vectors, coverage = make_vectors()
    sources = [REFERENCE / name for name in [
        'a_plus_b_using_wrapped_fifos.sv', 'ff_fifo_wrapped_in_valid_ready.sv',
        'flip_flop_fifo.sv']]
    with tempfile.TemporaryDirectory(prefix='lssk-fifo-') as temporary:
        work = Path(temporary)
        (work / 'config.svh').write_text('// Test-only empty include; no RTL macros are used.\n')
        (work / 'tb.sv').write_text(TB)
        (work / 'vectors.txt').write_text(''.join(' '.join(map(str, row))+'\n' for row in vectors))
        subprocess.run(['iverilog', '-g2012', '-s', 'tb', '-I', str(work), '-o', str(work/'sim'),
                        str(work/'tb.sv'), *map(str, sources)], cwd=work, check=True)
        subprocess.run(['vvp', str(work/'sim')], cwd=work, check=True)
    print('PASS directed ordering: A=1,2,3; B=4,5,6; SUM=5,7,9')
    print('Coverage:', json.dumps(coverage, sort_keys=True))
    print('RTL SHA256:', json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, sort_keys=True))
    print('This validates the reference transaction behavior, not physical FIFO pulse routing.')


if __name__ == '__main__':
    main()
