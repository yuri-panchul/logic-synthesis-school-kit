"""Proposal: synchronous FIFO exercises that behave like the RTL FIFO of the FPGA lab.

Writes fifo_sync_proposal.html.  It runs the lockstep check of fifo_sync_proposal.sv
(the circuit and its deliberate faults, in five timing corners) and two waveform
scenarios with Icarus Verilog, so every number and waveform on the page comes from a
simulation.  Not part of generate.py: the proposal is not published yet.

    python3 tools/fifo_sync_proposal.py
"""

import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from html import escape

import arbiter
import fifo
import generate
from arbiter import gate_shape, gnd_symbol, lab_svg, rpath
from lssk_data import CATALOG, KITS

ROOT = generate.ROOT
BGM = "/home/verilog/projects/basics-graphics-music"
RTL_DIR = BGM + "/labs/4_microarchitecture/4_2_fifo/4_2_5_optimized_ff_fifo_view_2_data_layout"
RTL_FILE = RTL_DIR + "/flip_flop_fifo_empty_full_optimized_and_debug_2.sv"
RTL_NAME = "flip_flop_fifo_empty_full_optimized_and_debug_2"
OUT = "fifo_sync_proposal.html"
FAULTS = {
    1: "pop goes straight to its flip-flop, without AND DOR",
    2: "no 40174: the data switches go straight to D0–D2",
    3: "no flip-flop: SI = clock AND push, the pulse suggested in the Habr article",
    6: "P3: R of the go flip-flop tied to GND instead of reset",
}

# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------

WAVE_TB = r"""
`define W(NAME, SIG) \
    always @ (SIG) $fdisplay (f, "%0d %s %0d", $time, NAME, SIG); \
    initial # 2 $fdisplay (f, "%0d %s %0d", $time, NAME, SIG);

module bb8_wave;
    localparam time ms = 64'd1_000_000;
    logic clk = 1'b0;
    always # (250 * ms) clk = ~ clk;
    logic [5:0] want = '0;  // rst, push, pop, d0, d1, d2
    wire  [5:0] btn;
    for (genvar i = 0; i < 6; i ++) begin : b
        button_with_bounce bb (.want (want [i]), .out (btn [i]));
    end
    wire [3:0] q;
    wire dor, dir;
    bb8_sync dut (.clk (clk), .rst (btn [0]), .push (btn [1]), .pop (btn [2]),
        .d0 (btn [3]), .d1 (btn [4]), .d2 (btn [5]), .q (q), .dor (dor), .dir (dir));
    wire [3:0] r_q;
    wire r_empty, r_full;
    wire r_pop  = btn [2] & ~ r_empty;
    wire r_push = btn [1] & (~ r_full | r_pop);
    ref_fifo ref_a (.clk (clk), .rst (btn [0]), .push (r_push), .pop (r_pop),
        .write_data ({ 1'b0, btn [5:3] }), .read_data (r_q), .empty (r_empty), .full (r_full));
    int f = $fopen ("bb8_wave.log", "w");
    wire push_r = ~ dut.push_r_n, pop_r = ~ dut.pop_r_n;
    wire [2:0] d = btn [5:3], r = { dut.r2, dut.r1, dut.r0 };
    `W ("clk", clk) `W ("push", btn [1]) `W ("pop", btn [2]) `W ("d", d) `W ("push_r", push_r)
    `W ("pop_r", pop_r) `W ("r", r) `W ("si", dut.si) `W ("so", dut.so) `W ("n", dut.u_a.n_words)
    `W ("q", q) `W ("dor", dor) `W ("rtl_q", r_q) `W ("rtl_e", r_empty)
    always @ (posedge clk) # 1 $fdisplay (f, "%0d rtl_count %0d", $time, ref_a.count ());
    initial
    begin
        # (37_300_000); want [0] = 1'b1; # (300 * ms); want [0] = 1'b0;
        # (1650 * ms - $time);
        want [5:3] = 3'd1; want [1] = 1'b1;   // 100 ms before the rising edge at 1.75 s
        # (200 * ms);  want [5:3] = 3'd2;
        # (500 * ms);  want [5:3] = 3'd3;
        # (800 * ms);  want [1] = 1'b0;       // 100 ms before the fourth edge
        # (200 * ms);  want [5:3] = 3'd0;
        # (300 * ms);  want [2] = 1'b1;       // pop, 100 ms before the edge at 3.75 s
        # (1500 * ms); want [2] = 1'b0;
        # (900 * ms);  $fclose (f); $finish;
    end
endmodule

module p3_wave;
    localparam time ms = 64'd1_000_000;
    logic clk = 1'b0;
    always # (250 * ms) clk = ~ clk;
    logic [6:0] want = '0;  // rst, push A, push B, pop C, d0, d1, d2
    wire  [6:0] btn;
    for (genvar i = 0; i < 7; i ++) begin : b
        button_with_bounce bb (.want (want [i]), .out (btn [i]));
    end
    wire [2:0] qa, qb;
    wire [3:0] qc;
    wire dor_a, dir_a, dor_b, dir_b, dor_c, dir_c;
    p3_sync dut (.clk (clk), .rst (btn [0]), .pushA (btn [1]), .pushB (btn [2]), .popC (btn [3]),
        .d0 (btn [4]), .d1 (btn [5]), .d2 (btn [6]),
        .qa (qa), .dor_a (dor_a), .dir_a (dir_a), .qb (qb), .dor_b (dor_b), .dir_b (dir_b),
        .qc (qc), .dor_c (dor_c), .dir_c (dir_c));
    wire [3:0] ra_q, rb_q, rc_q;
    wire ra_empty, ra_full, rb_empty, rb_full, rc_empty, rc_full;
    wire go = ~ ra_empty & ~ rb_empty & ~ rc_full;
    ref_fifo ref_a (.clk (clk), .rst (btn [0]), .push (btn [1] & (~ ra_full | go)), .pop (go),
        .write_data ({ 1'b0, btn [6:4] }), .read_data (ra_q), .empty (ra_empty), .full (ra_full));
    ref_fifo ref_b (.clk (clk), .rst (btn [0]), .push (btn [2] & (~ rb_full | go)), .pop (go),
        .write_data ({ 1'b0, btn [6:4] }), .read_data (rb_q), .empty (rb_empty), .full (rb_full));
    ref_fifo ref_c (.clk (clk), .rst (btn [0]), .push (go), .pop (btn [3] & ~ rc_empty),
        .write_data (ra_q + rb_q), .read_data (rc_q), .empty (rc_empty), .full (rc_full));
    int f = $fopen ("p3_wave.log", "w");
    wire go_r = ~ dut.go_r_n;
    wire [2:0] d = btn [6:4];
    `W ("clk", clk) `W ("pushA", btn [1]) `W ("pushB", btn [2]) `W ("popC", btn [3]) `W ("d", d)
    `W ("si_a", dut.si_a) `W ("si_b", dut.si_b) `W ("na", dut.u_a.n_words) `W ("nb", dut.u_b.n_words)
    `W ("go_r", go_r) `W ("si_c", dut.si_c) `W ("so_ab", dut.so_ab) `W ("nc", dut.u_c.n_words)
    `W ("so_c", dut.so_c) `W ("qc", qc) `W ("dor_c", dor_c)
    always @ (posedge clk) # 1 $fdisplay (f, "%0d rtl_nc %0d", $time, ref_c.count ());
    initial
    begin
        # (37_300_000); want [0] = 1'b1; # (300 * ms); want [0] = 1'b0;
        # (1650 * ms - $time);
        want [6:4] = 3'd1; want [1] = 1'b1;
        # (200 * ms);  want [6:4] = 3'd2;
        # (500 * ms);  want [6:4] = 3'd3;
        # (800 * ms);  want [1] = 1'b0;
        # (200 * ms);  want [6:4] = 3'd0;
        # (300 * ms);  want [6:4] = 3'd4; want [2] = 1'b1;   // 3.65 s
        # (200 * ms);  want [6:4] = 3'd5;
        # (500 * ms);  want [6:4] = 3'd6;
        # (800 * ms);  want [2] = 1'b0;
        # (200 * ms);  want [6:4] = 3'd0;
        # (300 * ms);  want [3] = 1'b1;                     // 5.65 s
        # (1500 * ms); want [3] = 1'b0;
        # (800 * ms);  $fclose (f); $finish;
    end
endmodule
"""


def iverilog(top, out, files, params=(), cwd=None):
    cmd = (["iverilog", "-g2012", "-s", top, "-I", BGM + "/labs/common", "-I", BGM + "/peripherals", "-o", out]
           + [f"-P{top}.{k}={v}" for k, v in params] + files)
    subprocess.run(cmd, check=True, cwd=cwd or ROOT)
    return subprocess.run(["vvp", "-n", out], check=True, cwd=cwd or ROOT, capture_output=True, text=True).stdout


def run_check(tmp, fault):
    out = iverilog("tb_sync_proposal", os.path.join(tmp, f"check_{fault}"),
                   ["fifo_breadboard.sv", "fifo_sync_proposal.sv", RTL_FILE], [("fault", fault)])
    corners = []
    for m in re.finditer(r"^(.+?):\s+bb8: (\d+) errors in (\d+) edges;\s+p3: (\d+) errors in (\d+) edges, "
                         r"(\d+) pairs moved", out, re.M):
        corners.append(dict(name=m[1], bb8_err=int(m[2]), bb8_edges=int(m[3]), p3_err=int(m[4]),
                            p3_edges=int(m[5]), moves=int(m[6])))
    assert len(corners) == 5, out[-2000:]
    viol = re.search(r"^(\d+) violations", out, re.M)
    cover = {}
    for m in re.finditer(r"^(bb8|p3) coverage, (.+?) corner: (.*)$", out, re.M):
        cover[(m[1], m[2])] = [int(x) for x in re.findall(r"\d+", m[3])]
    reports = re.findall(r"^(?:bb8|p3): .*$", out, re.M)
    ok = "PASS" in out.splitlines() if fault == 0 else f"fault {fault}: detected" in out.splitlines()
    return dict(fault=fault, corners=corners, violations=int(viol[1]) if viol else 0, cover=cover,
                reports=reports, ok=ok, out=out)


def parse_wave(path):
    ev = defaultdict(list)
    with open(path) as f:
        for line in f:
            t, name, v = line.split()
            ev[name].append((int(t), None if "x" in v or "z" in v else int(v)))
    return ev


def simulate():
    tmp = tempfile.mkdtemp(prefix="lssk_sync_")
    with open(os.path.join(tmp, "wave_tb.sv"), "w") as f:
        f.write(WAVE_TB)
    files = [os.path.join(ROOT, n) for n in ("fifo_breadboard.sv", "fifo_sync_proposal.sv")] + [RTL_FILE,
                                                                                                 "wave_tb.sv"]
    with ThreadPoolExecutor(max_workers=8) as ex:
        checks = list(ex.map(lambda k: run_check(tmp, k), [0] + list(FAULTS)))
        for top in ("bb8_wave", "p3_wave"):
            iverilog(top, os.path.join(tmp, top), files, cwd=tmp)
    waves = {top: parse_wave(os.path.join(tmp, f"{top}.log")) for top in ("bb8_wave", "p3_wave")}
    return checks, waves


# ----------------------------------------------------------------------------
# Waveforms
# ----------------------------------------------------------------------------

MS = 1_000_000


def value_at(ev, t):
    v = None
    for tt, vv in ev:
        if tt > t:
            break
        v = vv
    return v


def svg_wave(ev, rows, t0, t1, held=(), label="", note_edges=()):
    """rows: (label, signal, kind) with kind 'clk', 'bit', 'bus' or 'hi' (a highlighted bit)."""
    LW, W, RH, TOP = 190, 1060, 25, 34
    px = (W - LW - 16) / (t1 - t0)
    X = lambda t: LW + (t - t0) * px
    H = TOP + RH * len(rows) + 14
    o = [f'<svg class="arb wave" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}">']
    edges = [t for t, v in ev["clk"] if v == 1 and t0 < t < t1]
    for a, b, text in held:
        o.append(f'<rect class="wv-band" x="{X(a):.1f}" y="{TOP - 6}" width="{X(b) - X(a):.1f}" '
                 f'height="{RH * len(rows) + 6}" rx="4"/>'
                 f'<text class="wv-held" x="{(X(a) + X(b)) / 2:.1f}" y="{TOP - 12}" text-anchor="middle">'
                 f'{escape(text)}</text>')
    for k, t in enumerate(edges):
        o.append(f'<path class="wv-edge" d="M{X(t):.1f},{TOP - 4} V{TOP + RH * len(rows)}"/>')
        if t in note_edges:
            o.append(f'<text class="wv-num" x="{X(t):.1f}" y="{H - 2}" text-anchor="middle">↑</text>')
    for i, (lab, sig, kind) in enumerate(rows):
        y = TOP + RH * i
        o.append(f'<text class="wv-lab" x="{LW - 10}" y="{y + 16}" text-anchor="end">{lab}</text>')
        if i % 2 == 0:
            o.append(f'<rect class="wv-row" x="{LW - 4}" y="{y}" width="{W - LW - 8}" height="{RH}"/>')
        e = ev[sig]
        pts = [(t0, value_at(e, t0))] + [(t, v) for t, v in e if t0 < t < t1]
        if kind in ("clk", "bit", "hi"):
            hi, lo = y + 5, y + RH - 5
            d, prev = [], None
            for t, v in pts:
                yy = hi if v == 1 else lo
                if prev is None:
                    d.append(f"M{X(t):.1f},{yy}")
                elif yy != prev:
                    d.append(f"H{X(t):.1f} V{yy}")
                prev = yy
            d.append(f"H{X(t1):.1f}")
            o.append(f'<path class="wv-{kind}" d="{" ".join(d)}"/>')
        else:
            segs = []
            for j, (t, v) in enumerate(pts):
                te = pts[j + 1][0] if j + 1 < len(pts) else t1
                if segs and segs[-1][2] == v:
                    segs[-1][1] = te
                else:
                    segs.append([t, te, v])
            for a, b, v in segs:
                xa, xb = X(a), X(b)
                c = min(4, (xb - xa) / 2)
                yt, yb, ym = y + 4, y + RH - 4, y + RH / 2
                if v is None:
                    o.append(f'<path class="wv-none" d="M{xa:.1f},{ym} H{xb:.1f}"/>')
                    continue
                o.append(f'<path class="wv-bus" d="M{xa:.1f},{ym} L{xa + c:.1f},{yt} H{xb - c:.1f} L{xb:.1f},{ym} '
                         f'L{xb - c:.1f},{yb} H{xa + c:.1f} Z"/>')
                if xb - xa > 14:
                    o.append(f'<text class="wv-val" x="{(xa + xb) / 2:.1f}" y="{ym + 4}" text-anchor="middle">{v}</text>')
    o.append("</svg>")
    return "".join(o)


def head_events(ev, q, valid, invert=False):
    """Bus events that show q only while valid is 1 (or 0 when invert)."""
    times = sorted({t for t, _ in ev[q]} | {t for t, _ in ev[valid]})
    out = []
    for t in times:
        v, ok = value_at(ev[q], t), value_at(ev[valid], t)
        show = ok == (0 if invert else 1)
        out.append((t, v if show else None))
    return out


def waves_html(waves):
    b = waves["bb8_wave"]
    b["head"] = head_events(b, "q", "dor")
    b["rtl_head"] = head_events(b, "rtl_q", "rtl_e", invert=True)
    rows = [("clock (555 module)", "clk", "clk"), ("push button", "push", "bit"), ("data switches", "d", "bus"),
            ("push flip-flop (Q)", "push_r", "bit"), ("40174 data register", "r", "bus"),
            ("SI = NOR (clock, Q̄)", "si", "hi"), ("pop button", "pop", "bit"),
            ("pop flip-flop (pop · DOR)", "pop_r", "bit"), ("SO", "so", "hi"),
            ("words in the 40105", "n", "bus"), ("Q0–Q3 while DOR", "head", "bus"),
            ("RTL: words", "rtl_count", "bus"), ("RTL: read_data", "rtl_head", "bus")]
    e1 = 1750 * MS
    bb8 = svg_wave(b, rows, 1300 * MS, 5900 * MS, label="BB8 waveforms",
                   held=[(1650 * MS, 3150 * MS, "push held for three clock periods"),
                         (3650 * MS, 5150 * MS, "pop held for three clock periods")],
                   note_edges={e1, e1 + 500 * MS, e1 + 1000 * MS, e1 + 2000 * MS, e1 + 2500 * MS, e1 + 3000 * MS})
    p = waves["p3_wave"]
    p["head_c"] = head_events(p, "qc", "dor_c")
    rows = [("clock", "clk", "clk"), ("push A button", "pushA", "bit"), ("push B button", "pushB", "bit"),
            ("data switches", "d", "bus"), ("SI of A", "si_a", "hi"), ("SI of B", "si_b", "hi"),
            ("words in A", "na", "bus"), ("words in B", "nb", "bus"),
            ("go flip-flop (Q)", "go_r", "bit"), ("SI of C", "si_c", "hi"), ("SO of A and B", "so_ab", "hi"),
            ("words in C", "nc", "bus"), ("RTL: words in C", "rtl_nc", "bus"),
            ("pop C button", "popC", "bit"), ("SO of C", "so_c", "hi"), ("Q of C while DOR", "head_c", "bus")]
    p3 = svg_wave(p, rows, 1300 * MS, 7700 * MS, label="P3 waveforms",
                  held=[(1650 * MS, 3150 * MS, "push A: 1, 2, 3"), (3650 * MS, 5150 * MS, "push B: 4, 5, 6"),
                        (5650 * MS, 7150 * MS, "pop C")])
    return bb8, p3


# ----------------------------------------------------------------------------
# Schematics
# ----------------------------------------------------------------------------

COL = {
    "clk": "#868e96", "rst": "#c2410c", "push": "#4263eb", "pushA": "#4263eb", "pushB": "#7048e8",
    "pop": "#ae3ec9", "popC": "#ae3ec9", "d": "#e8590c", "r": "#f08c00", "si": "#1c7ed6", "so": "#9c36b5",
    "q": "#2b8a3e", "dor": "#0c8599", "dir": "#a5734d", "go": "#66a80f", "x": "#cc5de8", "s": "#d6336c",
    "qb": "#1864ab", "sic": "#1971c2",
}


class Sch:
    def __init__(self, w, h, label):
        self.o = [f'<svg class="arb" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">']

    def add(self, s):
        self.o.append(s)

    def done(self):
        return "".join(self.o) + "</svg>"

    def wire(self, net, pts, bus=None, width=None):
        self.add(f'<path class="s-w" style="stroke:{COL[net]}" stroke-width="{width or (4 if bus else 2.2)}" '
                 f'd="{rpath(pts, 6)}"/>')
        if bus:
            (x0, y0), (x1, y1) = pts[0], pts[1]
            mx, my = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.5
            self.add(f'<path class="s-line" d="M{mx - 4},{my + 6} l8,-12"/>'
                     f'<text class="s-pin2" x="{mx + 5}" y="{my + 13}">{bus}</text>')

    def dot(self, x, y, net):
        self.add(f'<circle cx="{x}" cy="{y}" r="3.6" style="fill:{COL[net]}"/>')

    def text(self, x, y, t, anchor="start", cls="s-io", net=None):
        st = f' style="fill:{COL[net]}"' if net else ""
        self.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"{st}>{t}</text>')

    def stub(self, x, y, net, name, side="l", length=18):
        """A short wire ending in a net name, entering a pin at (x, y) from the left, right or below."""
        if side == "l":
            self.wire(net, [(x - length, y), (x, y)])
            self.text(x - length - 3, y + 4, lab_svg(name), "end", "s-sub", net)
        elif side == "r":
            self.wire(net, [(x, y), (x + length, y)])
            self.text(x + length + 3, y + 4, lab_svg(name), "start", "s-sub", net)
        else:
            self.wire(net, [(x, y), (x, y + length)])
            self.text(x, y + length + 11, lab_svg(name), "middle", "s-sub", net)

    def box(self, x, y, w, h, title, sub, pins):
        self.add(f'<rect class="s-gate" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/>'
                 f'<text class="s-tag" x="{x + w / 2}" y="{y + h / 2 - 2}" text-anchor="middle">{title}</text>'
                 f'<text class="s-sub" x="{x + w / 2}" y="{y + h / 2 + 13}" text-anchor="middle">{sub}</text>')
        for side, d, nm in pins:
            if side == "l":
                self.text(x + 5, y + d + 4, lab_svg(nm), "start", "s-pin")
            elif side == "r":
                self.text(x + w - 5, y + d + 4, lab_svg(nm), "end", "s-pin")
            elif side == "b":
                self.text(x + d, y + h - 6, lab_svg(nm), "middle", "s-pin")
            else:
                self.text(x + d, y + 14, lab_svg(nm), "middle", "s-pin")

    def ff(self, x, y, title, sub=""):
        """4013 flip-flop: D at (x, y + 18), Q-bar at (x + 64, y + 42); clock and reset stubs."""
        self.add(f'<rect class="s-gate" x="{x}" y="{y}" width="64" height="60" rx="3"/>'
                 f'<text class="s-pin" x="{x + 5}" y="{y + 22}">D</text>'
                 f'<path class="s-line" d="M{x},{y + 30} l9,6 l-9,6"/>'
                 f'<text class="s-pin" x="{x + 32}" y="{y + 56}" text-anchor="middle">R</text>'
                 f'<text class="s-pin" x="{x + 59}" y="{y + 46}" text-anchor="end">'
                 f'<tspan text-decoration="overline">Q</tspan></text>'
                 f'<text class="s-sub" x="{x + 32}" y="{y - 6}" text-anchor="middle">{title}</text>')
        if sub:
            self.add(f'<text class="s-sub2" x="{x + 32}" y="{y - 18}" text-anchor="middle">{sub}</text>')
        self.stub(x, y + 36, "clk", "clk", "l", 16)
        self.stub(x + 32, y + 60, "rst", "rst", "b", 10)

    def nor(self, x, y, w=44, h=34):
        """NOR gate centred at (x, y); inputs at (x - w/2 + 4, y -/+ 9); returns the output point."""
        s, (ox, oy) = gate_shape("OR", x, y, w=w, h=h)
        self.add(s + f'<circle class="s-gate" cx="{ox + 3:g}" cy="{oy:g}" r="3"/>')
        return (ox + 6, oy), (x - w / 2 + 5, y - 9), (x - w / 2 + 5, y + 9)

    def inverter(self, x, y, net):
        """A NOR with both inputs joined: input wire enters at (x - 40, y)."""
        out, i1, i2 = self.nor(x, y)
        self.wire(net, [(x - 40, y), (x - 32, y), (x - 32, i1[1]), i1])
        self.wire(net, [(x - 32, y), (x - 32, i2[1]), i2])
        self.dot(x - 32, y, net)
        return out

    def led(self, x, y, colour=None):
        self.add(fifo.led_symbol(x, y, up=True))
        if colour:
            self.add(f'<circle cx="{x}" cy="{y - 9}" r="2.4" fill="{colour}"/>')


def svg_bb8():
    S = Sch(1000, 470, "BB8 as a synchronous FIFO: logic diagram")
    S.add('<rect class="s-cloud3" x="120" y="20" width="376" height="390" rx="14"/>')
    S.text(132, 40, "SAMPLED AT THE RISING EDGE ↑ · PULSE IN THE LOW HALF ↓", cls="s-cap")
    # data: switches -> 40174 -> D0-D2
    S.text(14, 72, "data switches", cls="s-io")
    S.wire("d", [(14, 80), (300, 80)], bus="3")
    S.box(300, 58, 92, 58, "40174", "data register", [("l", 22, "D"), ("r", 22, "Q")])
    S.stub(346, 116, "clk", "clk", "b", 12)
    S.wire("r", [(392, 80), (620, 80)], bus="3")
    S.text(500, 72, "write_data", "middle", "s-sub", "r")
    # push
    S.text(14, 150, "push", cls="s-io")
    S.wire("push", [(14, 158), (160, 158)])
    S.ff(160, 140, "4013 · FF1", "push sampled")
    out, i1, i2 = S.nor(300, 190)
    S.wire("push", [(224, 182), (244, 182), (244, i2[1]), i2])
    S.stub(i1[0], i1[1], "clk", "clk", "l", 20)
    S.text(300, 226, "4001 NOR", "middle", "s-sub")
    S.wire("si", [out, (620, 190)])
    S.text(470, 182, "SI", "middle", "s-io", "si")
    # pop: pop AND DOR -> FF2 -> NOR -> NOR (inverter) -> SO
    S.text(14, 282, "pop", cls="s-io")
    S.wire("pop", [(14, 290), (74, 290)])
    s_, aout = gate_shape("AND", 96, 300, w=44, h=36)
    S.add(s_)
    S.text(96, 336, "4082 AND", "middle", "s-sub")
    S.wire("pop", [aout, (160, 300)])
    S.ff(160, 282, "4013 · FF2", "pop AND DOR sampled")
    out2, j1, j2 = S.nor(300, 332)
    S.wire("pop", [(224, 324), (244, 324), (244, j2[1]), j2])
    S.stub(j1[0], j1[1], "clk", "clk", "l", 20)
    S.text(300, 368, "4001 NOR", "middle", "s-sub")
    S.wire("x", [out2, (380, 332)])
    so = S.inverter(420, 332, "x")
    S.text(420, 368, "4001 NOR as NOT", "middle", "s-sub")
    S.wire("so", [so, (580, 332), (580, 290), (620, 290)])
    S.text(560, 282, "SO", "middle", "s-io", "so")
    # DOR feedback into the AND
    S.wire("dor", [(740, 160), (800, 160), (800, 430), (56, 430), (56, 310), (74, 310)])
    S.text(440, 424, "DOR (data-out ready) = not empty", "middle", "s-sub", "dor")
    # the FIFO
    S.box(620, 56, 120, 270, "40105", "FIFO, 16 × 4",
          [("l", 24, "D0–D2"), ("l", 134, "SI"), ("l", 234, "SO"), ("r", 24, "Q0–Q3"), ("r", 104, "DOR"),
           ("r", 184, "DIR"), ("b", 60, "MR")])
    S.stub(680, 326, "rst", "rst", "b", 10)
    S.text(700, 100, "D3 = 0", "start", "s-sub2")
    # LEDs
    S.wire("q", [(740, 80), (880, 80), (880, 66)], bus="4")
    S.led(880, 66)
    S.text(895, 40, "read_data", "start", "s-sub", "q")
    S.dot(800, 160, "dor")
    S.wire("dor", [(800, 160), (920, 160), (920, 146)])
    S.led(920, 146)
    S.text(935, 120, "not empty", "start", "s-sub", "dor")
    S.wire("dir", [(740, 240), (920, 240), (920, 226)])
    S.led(920, 226, "#ffd43b")
    S.text(935, 200, "not full", "start", "s-sub", "dir")
    return S.done()


def svg_p3():
    S = Sch(1060, 740, "P3 with synchronous FIFOs: logic diagram")
    S.add('<rect class="s-cloud3" x="96" y="14" width="200" height="430" rx="14"/>')
    S.text(106, 30, "SAMPLED AT ↑", cls="s-cap")
    S.add('<rect class="s-cloud" x="304" y="14" width="740" height="430" rx="16"/>')
    S.text(316, 30, "DATAPATH", cls="s-cap")
    S.add('<rect class="s-cloud2" x="96" y="452" width="860" height="282" rx="14"/>')
    S.text(108, 470, "CONTROL: SAMPLED AT ↑, PULSES IN THE LOW HALF ↓", cls="s-cap")
    # data register
    S.text(14, 52, "data switches", cls="s-io")
    S.wire("d", [(14, 60), (200, 60)], bus="3")
    S.box(200, 40, 84, 46, "40174", "", [("l", 20, "D"), ("r", 20, "Q")])
    S.stub(242, 86, "clk", "clk", "b", 10)
    S.wire("r", [(284, 60), (350, 60), (350, 100), (390, 100)], bus="3")
    S.wire("r", [(350, 100), (350, 290), (390, 290)])
    S.dot(350, 100, "r")
    # push A and push B
    for y0, name, net, chip in ((120, "push A", "pushA", "4013 #1 · FF1"), (310, "push B", "pushB", "4013 #2 · FF1")):
        S.text(14, y0 + 10, name, cls="s-io")
        S.wire(net, [(14, y0 + 18), (110, y0 + 18)])
        S.ff(110, y0, chip)
        out, i1, i2 = S.nor(240, y0 + 33)
        S.wire(net, [(174, y0 + 42), i2])
        S.stub(i1[0], i1[1], "clk", "clk", "l", 14)
        S.text(240, y0 + 66, "4001 #1", "middle", "s-sub")
        S.wire("si", [out, (390, y0 + 33)])
        S.text(330, y0 + 25, "SI", "middle", "s-io", "si")
    # FIFO A and B
    pins = [("l", 20, "D"), ("l", 73, "SI"), ("r", 20, "Q"), ("r", 80, "DOR"), ("b", 90, "SO"), ("b", 30, "MR")]
    S.box(390, 80, 120, 130, "FIFO A", "40105", pins)
    S.box(390, 270, 120, 130, "FIFO B", "40105", pins)
    for y in (210, 400):
        S.stub(420, y, "rst", "rst", "b", 10)
    # A, B -> adder; LEDs
    S.wire("q", [(510, 100), (620, 100)], bus="3")
    S.wire("qb", [(510, 290), (620, 290)], bus="3")
    S.text(590, 92, "a", "middle", "s-io", "q")
    S.text(590, 282, "b", "middle", "s-io", "qb")
    S.stub(510, 160, "dor", "rA", "r", 22)
    S.stub(510, 350, "dor", "rB", "r", 22)
    S.box(620, 80, 84, 320, "4008", "adder", [("l", 20, "A"), ("l", 210, "B"), ("r", 160, "S")])
    S.wire("s", [(704, 240), (780, 240)], bus="4")
    # FIFO C
    S.box(780, 200, 120, 150, "FIFO C", "40105",
          [("l", 40, "D"), ("l", 90, "SI"), ("r", 16, "Q"), ("r", 56, "DOR"), ("r", 100, "DIR"), ("b", 92, "SO"),
           ("b", 30, "MR")])
    S.stub(810, 350, "rst", "rst", "b", 10)
    S.wire("q", [(900, 216), (990, 216), (990, 196)], bus="4")
    S.led(990, 196)
    S.text(990, 156, "sum", "middle", "s-sub")
    S.wire("dor", [(900, 256), (1020, 256), (1020, 236)])
    S.led(1020, 236)
    S.dot(950, 256, "dor")
    S.wire("dor", [(950, 256), (950, 274)])
    S.text(950, 286, "vC", "middle", "s-sub", "dor")
    S.wire("dir", [(900, 300), (1020, 300), (1020, 284)])
    S.led(1020, 284, "#ffd43b")
    S.dot(950, 300, "dir")
    S.wire("dir", [(950, 300), (950, 318)])
    S.text(950, 330, "fC", "middle", "s-sub", "dir")
    # go: AND3 -> FF -> NOR (SI of C) -> NOR as NOT (SO of A and B)
    s_, gout = gate_shape("AND", 330, 520, w=50, h=56)
    S.add(s_)
    for dy, nm in ((-16, "rA"), (0, "rB"), (16, "fC")):
        S.stub(305, 520 + dy, "dir" if nm == "fC" else "dor", nm, "l", 22)
    S.text(330, 562, "4082 AND", "middle", "s-sub")
    S.wire("go", [gout, (400, 520)])
    S.text(380, 512, "go", "middle", "s-io", "go")
    S.ff(400, 502, "4013 #2 · FF2", "go sampled")
    out, i1, i2 = S.nor(540, 535)
    S.wire("go", [(464, 544), (i2[0], 544)])
    S.stub(i1[0], i1[1], "clk", "clk", "l", 14)
    S.wire("sic", [out, (720, 535), (720, 290), (780, 290)])
    S.text(700, 527, "SI of C", "end", "s-io", "sic")
    S.dot(600, 535, "sic")
    S.wire("sic", [(600, 535), (600, 600), (620, 600)])
    so_ab = S.inverter(660, 600, "sic")
    S.text(560, 572, "4001 #1", "middle", "s-sub")
    S.text(660, 636, "NOR as NOT", "middle", "s-sub")
    S.wire("so", [so_ab, (760, 600), (760, 430), (560, 430), (560, 230), (480, 230), (480, 210)])
    S.wire("so", [(560, 420), (480, 420), (480, 400)])
    S.dot(560, 420, "so")
    S.text(580, 422, "SO of A and B", "start", "s-io", "so")
    # pop C: popC AND DOR C -> FF -> NOR -> NOR as NOT -> SO of C
    S.text(14, 648, "pop C", cls="s-io")
    S.wire("popC", [(14, 656), (110, 656)])
    s_, pout = gate_shape("AND", 130, 666, w=40, h=36)
    S.add(s_)
    S.stub(110, 676, "dor", "vC", "l", 22)
    S.text(130, 700, "4082 AND", "middle", "s-sub")
    S.wire("popC", [pout, (200, 666)])
    S.ff(200, 648, "4013 #1 · FF2", "pop C AND vC sampled")
    out, j1, j2 = S.nor(330, 681)
    S.wire("popC", [(264, 690), (j2[0], 690)])
    S.stub(j1[0], j1[1], "clk", "clk", "l", 14)
    S.wire("x", [out, (400, 681)])
    so_c = S.inverter(440, 681, "x")
    S.text(385, 716, "4001 #2", "middle", "s-sub")
    S.wire("so", [so_c, (872, 681), (872, 350)])
    S.text(880, 670, "SO of C", "start", "s-io", "so")
    return S.done()


# ----------------------------------------------------------------------------
# Kit prices with the proposed parts
# ----------------------------------------------------------------------------

def kit_prices():
    """FIFO kit A builds the current circuit, FIFO kit B this proposal (its `variants` in lssk_data.py)."""
    return [(k["name"], generate.compute_kit(k)["pricing"])
            for k in KITS if k["id"] in ("kit3_fifo", "kit3b_fifo_sync")]


# ----------------------------------------------------------------------------
# The page
# ----------------------------------------------------------------------------

EXTRA_CSS = """
.s-sub2{fill:var(--muted);font-size:8.5px}
.s-cloud3{fill:var(--accent-bg);stroke:#5c7cfa;stroke-width:1.2;stroke-dasharray:6 5;opacity:.85}
svg.wave{min-width:980px}
.wv-lab{fill:var(--fg);font-size:11.5px;font-weight:600}
.wv-row{fill:var(--th);opacity:.55}
.wv-clk{fill:none;stroke:var(--muted);stroke-width:1.4}
.wv-bit{fill:none;stroke:var(--fg);stroke-width:1.6}
.wv-hi{fill:none;stroke:var(--accent);stroke-width:2.2}
.wv-bus{fill:var(--accent-bg);stroke:var(--accent);stroke-width:1.2}
.wv-none{stroke:var(--muted);stroke-width:1;stroke-dasharray:2 3}
.wv-val{fill:var(--fg);font-size:11px;font-weight:700}
.wv-edge{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 4;opacity:.7}
.wv-num{fill:var(--accent);font-size:13px;font-weight:700}
.wv-band{fill:var(--warn-bg);opacity:.7}
.wv-held{fill:var(--warn);font-size:11px;font-weight:700}
.ok{color:var(--accent);font-weight:600}.bad{color:#d64541;font-weight:600}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px 22px}
.cols>div{min-width:0}
p code,li code{overflow-wrap:anywhere}
"""


def table(head, rows, num=()):
    th = "".join(f'<th{" class=n" if i in num else ""}>{h}</th>' for i, h in enumerate(head))
    tr = "".join("<tr>" + "".join(f'<td{" class=n" if i in num else ""}>{c}</td>' for i, c in enumerate(r))
                 + "</tr>" for r in rows)
    return f'<div class="tbl"><table><tr>{th}</tr>{tr}</table></div>'


def build(checks, waves):
    base = checks[0]
    assert base["ok"] and base["violations"] == 0, base["out"][-3000:]
    for c in checks[1:]:
        assert c["ok"], f"fault {c['fault']} not detected"
    rep = base["reports"]
    get = lambda pat: next(r for r in rep if re.search(pat, r))
    n3 = re.search(r"holds (\d+) words, the RTL (\d+)", get("push held for 3 clock periods"))
    pop555 = get("^bb8: popped").split("popped")[1].strip()
    pop123 = get("data 1, 2, 3").split("popped")[1].strip()
    p3_moved = re.search(r"(\d+) pairs moved", get("push A and push B held"))[1]
    p3_pop = re.search(r"popped ([\d ]+),", get("pop C held"))[1].strip()
    edges = sum(c["bb8_edges"] + c["p3_edges"] for c in base["corners"])
    moves = sum(c["moves"] for c in base["corners"])
    bb8_wave, p3_wave = waves_html(waves)
    prices = kit_prices()
    cat = lambda k: generate.money(CATALOG[k][3])

    corner_rows = [(escape(c["name"]), f'{c["bb8_edges"]:,}', c["bb8_err"], f'{c["p3_edges"]:,}', c["p3_err"],
                    f'{c["moves"]:,}') for c in base["corners"]]
    timing = [("typical", "125", "150", "200", "400", "40 / 25"), ("fast", "60", "60", "80", "150", "15 / 6"),
              ("slow", "250", "300", "400", "800", "63 / 40"), ("slow glue, fast FIFO", "250", "300", "400", "800", "15 / 6"),
              ("fast glue, slow FIFO", "60", "60", "80", "150", "63 / 40")]
    timing_tbl = table(["Corner", "4001, 4082", "4013", "40174", "4008", "40105 flags / ripple per word"],
                       timing, num=(1, 2, 3, 4, 5))
    cov = base["cover"]
    cb = [cov[("bb8", c["name"])] for c in base["corners"]]
    cp = [cov[("p3", c["name"])] for c in base["corners"]]
    cov_rows = [
        ("BB8: FIFO full at a rising edge", sum(x[0] for x in cb)),
        ("BB8: FIFO empty at a rising edge", sum(x[1] for x in cb)),
        ("BB8: push into a full FIFO on the same edge as a pop", sum(x[2] for x in cb)),
        ("BB8: push into a full FIFO without a pop (ignored)", sum(x[3] for x in cb)),
        ("BB8: push and pop on an empty FIFO on the same edge", sum(x[4] for x in cb)),
        ("P3: A full / B full / C full", f"{sum(x[0] for x in cp)} / {sum(x[1] for x in cp)} / {sum(x[2] for x in cp)}"),
        ("P3: pairs moved on consecutive clocks", sum(x[3] for x in cp)),
        ("P3: push into a full A while a pair leaves A", sum(x[4] for x in cp)),
        ("P3: pop C on an empty C while a pair arrives", sum(x[5] for x in cp)),
    ]
    fault_rows = []
    for c in checks[1:]:
        where = [x["name"] for x in c["corners"] if x["bb8_err"] + x["p3_err"]]
        tests = sorted({t for x in c["corners"] for t, e in (("BB8", x["bb8_err"]), ("P3", x["p3_err"])) if e})
        fault_rows.append((str(c["fault"]), escape(FAULTS[c["fault"]]),
                           '<span class="ok">caught</span> in ' + " and ".join(tests) + ", "
                           + ("all five corners" if len(where) == 5 else escape(", ".join(where)))))
    price_rows = [(escape(n), generate.money(p["parts"]), generate.money(p["landed"]), generate.money(p["classroom"]),
                   generate.money(p["retail"])) for n, p in prices]

    run = (f"BGM={BGM}\nRTL=$BGM/labs/4_microarchitecture/4_2_fifo/4_2_5_optimized_ff_fifo_view_2_data_layout\n"
           "iverilog -g2012 -s tb_sync_proposal -I $BGM/labs/common -I $BGM/peripherals \\\n"
           "    -o sync_tb fifo_breadboard.sv fifo_sync_proposal.sv \\\n"
           f"    $RTL/{RTL_NAME}.sv\nvvp -n sync_tb")

    body = f"""
<h1>Proposal: breadboard FIFOs that behave like the RTL FIFO</h1>
<p class="lead">In the FPGA lab, <code>{RTL_NAME}</code> samples <code>push</code> and <code>pop</code> at every
rising clock edge, so holding push for three clock cycles pushes three words. The breadboard FIFO in the current
build guide pushes one word per press, however long you hold the button. This proposal changes the glue logic
around the 40105 so that exercises BB8 and P3 become functional equivalents of the RTL FIFO (depth 16, width 4).
The build guides are unchanged until you decide; <a href="kit3b_fifo_sync.html">FIFO kit B</a> lists the parts
for this circuit.</p>

<div class="grid">
<div class="stat"><b>{n3[1]} words</b><span>after push is held for three clock periods (the RTL: {n3[2]})</span></div>
<div class="stat"><b>0 of {edges:,}</b><span>rising edges where the circuit differs from the RTL, in five timing corners</span></div>
<div class="stat"><b>{len(checks) - 1} of {len(checks) - 1}</b><span>deliberate wiring faults caught by the same check</span></div>
<div class="stat"><b>+3 chips</b><span>in P3 (two 4001, one 40174): +{generate.money(2 * CATALOG["4001"][3] + CATALOG["40174"][3])} of parts per kit</span></div>
</div>

<h2>1. What differs today</h2>
<div class="cols">
<div><h3>The RTL FIFO</h3>
<p>At every rising edge of <code>clk</code>: if <code>push</code> is 1, <code>write_data</code> goes in; if
<code>pop</code> is 1, the head goes out. <code>read_data</code>, <code>empty</code> and <code>full</code> show the
state. Holding push for <i>n</i> clock cycles pushes <i>n</i> words. The lab's <code>lab_top</code> uses
<code>push = ~full &amp; key[1]</code> and <code>pop = ~empty &amp; key[0]</code> on a slow clock.</p></div>
<div><h3>The breadboard now</h3>
<p>A 4013 flip-flop samples the push button at the rising edge and drives SI. The 40105 loads a word on a rising
edge of SI, and SI must go low before the next word. While the button is held, SI stays high, so a press gives one
word: holding it for three clock periods still pushes one. Pop works the same way on SO. In P3, the transfer
flip-flop moves a pair at most every second clock.</p></div>
</div>

<h2>2. The idea: sample at the rising edge, act in the low half</h2>
<p>The 40105 is an asynchronous FIFO. It reacts to edges on SI and SO, not to a clock. To make it synchronous,
every input of the RTL is sampled at the rising edge into a flip-flop, as the <code>always_ff</code> blocks do.
Every sampled 1 then becomes exactly one pulse on SI or SO during the low half of that clock period:</p>
<code class="eq">SI = NOR (clk, Q̄<sub>push</sub>)&nbsp;&nbsp;&nbsp;&nbsp;high from the falling edge to the next rising edge, if push was 1 at the rising edge<br>
SO = NOT NOR (clk, Q̄<sub>pop</sub>)&nbsp;&nbsp;falls at the falling edge (the 40105 drops a word on a falling SO), if pop was 1</code>
<p>The 40105 has finished long before the next rising edge: the datasheet gives at most 0.5&nbsp;µs to ripple a
word through all 16 places (4.5&nbsp;V), and at 2&nbsp;Hz the low half lasts 250&nbsp;ms. So at every rising edge,
Q0–Q3, DOR and DIR of the 40105 equal <code>read_data</code>, <code>~empty</code> and <code>~full</code> of the RTL
for the same inputs. The one visible difference is that the breadboard's LEDs change at the falling edge, half a
period after the RTL's outputs.</p>
<div class="note"><b>Why a NOR with the clock itself, not an AND with an inverted clock.</b> When the clock rises,
the clock input alone forces the NOR output low, before Q̄ can change (Q̄ changes about 150&nbsp;ns later, through
the flip-flop). When the clock falls, Q̄ has been stable for half a period. So SI cannot glitch, whatever the
delays of the chips. With <code>(NOT clk) AND Q</code>, a glitch on SI would depend on the inverter being faster
than the flip-flop. In the models it always is, which is why I could not show that fault failing, but the NOR form
does not rely on it.</div>

<h3>BB8 as a synchronous FIFO</h3>
<div class="fig-wrap">{svg_bb8()}</div>
<p class="small muted">Figure 1. The 40174 samples the data switches at the same rising edge as push. The 4082
lets the pop flip-flop see pop only while DOR is 1 (not empty), like <code>pop = ~empty &amp; key[0]</code>.
A pop on an empty FIFO never reaches SO.</p>

<h3>Your scenario: push pressed before a rising edge and held for three clock periods</h3>
<div class="fig-wrap">{bb8_wave}</div>
<p class="small muted">Figure 2. Simulated chip by chip (typical corner, contact bounce included), next to your
RTL module driven by the same buttons. The switches show 1, 2 and 3 at the three rising edges marked ↑. The
breadboard stores 1, 2, 3 half a period after each edge. Holding pop for three periods then pops
{escape(pop123)}. With the switches left at 5, the same hold pushes and pops {escape(pop555)}.</p>

<h2>3. Details that make it exact</h2>
<div class="card"><h3>The data register (40174)</h3>
<p>The 40105 takes D0–D3 at the rising edge of SI, which now comes at the falling clock edge. The 40174 samples the
switches at the rising edge, together with push, so each word is what the switches showed at that rising edge,
as in the RTL. Without it, a held value still works ({escape(pop555)}), but switches changed 1&nbsp;→&nbsp;2&nbsp;→&nbsp;3
right after the rising edges store <b>2 3 3</b> (fault 2 below).</p></div>
<div class="card"><h3>Pop only when not empty</h3>
<p>Suppose the FIFO is empty and push and pop come on the same edge. The new word ripples to the output in a few
hundred nanoseconds. If SO falls after it arrives, the 40105 pops the word that was just pushed. Whether that
happens depends on which is faster, the gates or the FIFO. In the simulation it happens in the "slow glue, fast
FIFO" corner (fault 1). Sampling <code>pop AND DOR</code> at the rising edge rules it out. P3 uses the second gate
of its 4082 for this, so it costs P3 nothing.</p></div>
<div class="card"><h3>Push into a full FIFO</h3>
<p>No gate is needed. Without a pop on that edge, the 40105 ignores SI because DIR is low. With a pop on the same
edge, SI is still high when the place frees up, and the 40105 takes the word. The datasheet says: <i>"If during
unloading SI is HIGH (FIFO is full) data on the data input of the FIFO is entered in the first location."</i>
That is the push-with-pop behaviour that your FIFO supports and that its <code>tb.sv</code> tests with
<code>allow_push_when_full_with_pop = 1</code>. <code>lab_top</code> uses the stricter <code>push = ~full &amp;
key[1]</code>. Matching that exactly needs DIR ANDed into the push flip-flop's D: the spare 4082 gate does this in
BB8, but P3 has no spare AND.</p></div>
<div class="card"><h3>Reset</h3>
<p>The push, pop and go flip-flops are reset together with the FIFOs, so SI is low while MR is high. That matters
because the datasheet says: <i>"If the shift-in flag (SI) is HIGH during the master reset pulse, data present at
the input (D0 to D3) are immediately moved into the first location upon completion of the reset process."</i>
With the go flip-flop not reset, a reset during a transfer leaves a stray word in C (fault 6).</p></div>

<h2>4. P3: one pair per clock, as in the RTL</h2>
<p>With synchronous FIFOs the transfer logic is the RTL expression itself:
<code>go = ~empty_A &amp; ~empty_B &amp; ~full_C</code>, that is DOR<sub>A</sub>·DOR<sub>B</sub>·DIR<sub>C</sub> on
the 4082. The go flip-flop samples it at the rising edge. In the low half that follows, SI of C rises, and one gate
delay later SO of A and B fall (SO<sub>A,B</sub> = NOT SI<sub>C</sub>). So C takes the sum before A and B let go of
the pair, and C's 25&nbsp;ns data hold time is met by construction. While A and B have data and C has room, a pair
moves on every clock. This replaces the transfer flip-flop t, whose two-clock handshake (go = rA·rB·fC·t̄) let at
most one pair through every second clock.</p>
<div class="fig-wrap">{svg_p3()}</div>
<p class="small muted">Figure 3. The four 4013 flip-flops sample push A, push B, pop C AND DOR<sub>C</sub>, and go.
4001 #1 makes the SI pulses of A, B and C and, as an inverter, SO of A and B. 4001 #2 makes SO of C. rA, rB, vC and
fC are the DOR and DIR outputs of the FIFOs.</p>
<div class="fig-wrap">{p3_wave}</div>
<p class="small muted">Figure 4. Push A held for three clocks (1, 2, 3), then push B held for three clocks
(4, 5, 6): B's first word arrives, and from the next clock {p3_moved} pairs move on {p3_moved} consecutive clocks.
Pop C held for three clocks then pops {escape(p3_pop)}. "RTL: words in C" is three of your FIFOs wired the same
way, changing half a period earlier.</p>

<h2>5. How it was checked</h2>
<p>The file <code>fifo_sync_proposal.sv</code> holds chip-level netlists of both circuits. It uses the chip models of
<code>fifo_breadboard.sv</code> (40105, 4013, 4082, 4008, button bounce) plus new models of the 4001 and the 40174,
with transport delays, setup and hold checks, the 40105 data hold check and the floating-input check. The reference
is your file, compiled unchanged from <code>basics-graphics-music</code>. Just before every rising edge, the
testbench compares the number of words, every word in order, DOR&nbsp;=&nbsp;~empty, DIR&nbsp;=&nbsp;~full and
Q&nbsp;=&nbsp;read_data, for each FIFO. The stimulus:</p>
<ol class="steps">
<li>your scenario, with the data held and with the data changed during the hold;</li>
<li>the tests of the lab's <code>tb.sv</code>: fill and empty, half full then back-to-back, full with push and pop
together, and an extra push into a full FIFO and pop from an empty one;</li>
<li>1,800 (BB8) and 2,400 (P3) clocks of random synchronous inputs, in phases that fill, drain and hover;</li>
<li>400 (BB8) and 500 (P3) random button changes with contact bounce at any moment, including resets in the
middle of a transfer.</li>
</ol>
{timing_tbl}
<p class="small muted">Delays in ns. The two mixed corners pair slow gates and flip-flops with fast FIFOs and the
other way round, which is where races between the glue logic and the 40105 would show.</p>
{table(["Corner", "BB8 edges", "BB8 mismatches", "P3 edges", "P3 mismatches", "P3 pairs moved"], corner_rows, num=(1, 2, 3, 4, 5))}
<p>No setup, hold or floating-input violations, and {moves:,} pairs moved in P3. Each case below was hit many
times, summed over the corners:</p>
{table(["Case", "Rising edges"], cov_rows, num=(1,))}
<p>To show that the check has teeth, the same testbench runs on the circuit with deliberate faults:</p>
{table(["Fault", "What is wrong", "Result"], fault_rows)}
<pre class="code">{escape(run)}</pre>
<p class="small muted">Add <code>-P tb_sync_proposal.fault=N</code> for fault N. A run takes about 20&nbsp;s.
<code>python3 tools/fifo_sync_proposal.py</code> reruns everything and rewrites this page.</p>
<div class="note"><b>Limits.</b> The netlists are written by hand from this proposal; there is no breadboard
layout yet. The 40105 model follows my reading of the TI datasheet text, and nothing here has been built on real
hardware.</div>

<h2>6. What it costs and what would change</h2>
{table(["Exercise", "Now", "Proposed"], [
        ("BB8", "40105, 4013 · 2 chips · 19 jumpers", "40105, 4013, 4001, 4082, 40174 · 5 chips · about 50 jumpers"),
        ("P3", "3 × 40105, 2 × 4013, 4082, 4008 · 7 chips · 74 jumpers",
         "3 × 40105, 2 × 4013, 2 × 4001, 4082, 40174, 4008 · 10 chips · about 113 jumpers")])}
<p>The extra chips fit on the same two boards: the bottom board has columns 45–63 free and the top board 50–63.
The jumper counts are my estimate until the router has laid the wires out. The kit's wire set (350 pieces) covers
them, so only the chips change the kit prices: 4001 {cat("4001")}, 40174 {cat("40174")}.</p>
{table(["Kit", "Parts", "Landed cost", "Classroom", "Retail"], price_rows, num=(1, 2, 3, 4))}
<p class="small muted">FIFO kit A has the parts of the current circuit, <a href="kit3b_fifo_sync.html">FIFO kit B</a>
those of this proposal. The comprehensive kit already has the extra chips.</p>
<p>If you approve, I would:</p>
<ol class="steps">
<li>re-route both stages on the breadboard and regenerate the wiring checklist and the three diagrams;</li>
<li>rewrite the "Buttons in step with the clock", transfer and test sections of both guides (EN and RU);</li>
<li>regenerate <code>fifo_breadboard.sv</code> from the new wires, with this lockstep check against your RTL as its
testbench;</li>
<li>replace the estimated wire counts of FIFO kit B with the counted ones.</li>
</ol>
<p>Nothing would be published until you have checked it. One layout caveat stays: the LED module plugged over C has
an LED on pin 15 (SO), now driven by a 4001. The new layout should keep LEDs off 4000-series outputs.</p>

<h2>7. Alternatives considered</h2>
<div class="card"><h3>Act at the rising edge, sample at the falling edge</h3>
<p>Clock the flip-flops with an inverted clock and use <code>SI = clk AND Q</code> and <code>SO = NAND (clk, Q)</code>.
The 40105 then takes the switches at the rising edge itself, so it needs no 40174, and the LEDs change at the
rising edge as on the FPGA. But push and pop are read half a period before the edge they act on: a press shortly
before a rising edge lands one clock later. A synchronous data source would also have to hold its data for the SI
gate delay after the edge, which acts as clock skew. It saves the 40174 and about 13 jumpers.</p></div>
<div class="card"><h3>SI = clock AND push, without a flip-flop</h3>
<p>This is the pulse in the Habr article. Contact bounce and a press in the middle of a clock-high phase make extra or
shortened pulses (fault 3: caught everywhere).</p></div>
<div class="card"><h3>Keep the current circuit</h3>
<p>One word per press is simpler to wire, but it is not the RTL's behaviour, and P3 then needs the two-clock
transfer handshake.</p></div>

<h2>8. Decisions for you</h2>
<ol class="steps">
<li><b>The 40174 data register:</b> keep it for exact equivalence (recommended), or drop it to save a chip and about
13 jumpers. Without it, the switches must not change in the first half period after a rising edge while push is held.</li>
<li><b>Push into a full FIFO on the same edge as a pop:</b> accept it as your FIFO allows (no extra gate,
recommended), or reject it like <code>lab_top</code> (one AND per FIFO: free in BB8, an extra chip in P3).</li>
<li><b>Go ahead:</b> re-route and regenerate the guides, the SV model and the kits as listed in section 6.</li>
</ol>
"""
    html = generate.page("Synchronous FIFO proposal", OUT, body, extra_css=arbiter.CSS + EXTRA_CSS)
    old = "generated from <code>tools/lssk_data.py</code>\nwith prices from"
    assert old in html
    html = html.replace(old, "generated by <code>tools/fifo_sync_proposal.py</code>\nwith prices from")
    with open(os.path.join(ROOT, OUT), "w") as f:
        f.write(html)
    return base


def main():
    cache = os.environ.get("LSSK_SYNC_CACHE")
    if cache and os.path.exists(cache):
        import pickle
        with open(cache, "rb") as f:
            checks, waves = pickle.load(f)
    else:
        checks, waves = simulate()
        if cache:
            import pickle
            with open(cache, "wb") as f:
                pickle.dump((checks, waves), f)
    base = build(checks, waves)
    print(f"wrote {OUT}")
    for r in base["reports"]:
        print("  " + r)
    for c in base["corners"]:
        print(f"  {c['name']}: bb8 {c['bb8_err']} / {c['bb8_edges']}, p3 {c['p3_err']} / {c['p3_edges']}")
    for c in checks[1:]:
        print(f"  fault {c['fault']}: {'caught' if c['ok'] else 'NOT CAUGHT'}")


if __name__ == "__main__":
    sys.exit(main())
