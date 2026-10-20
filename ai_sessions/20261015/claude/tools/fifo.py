"""FIFO adder with backpressure (exercise P3) on two breadboards, and the one-FIFO demo (BB8).

Three CD74HC40105 FIFOs, a CD4008 adder, a CD4082 4-input AND and two CD4013s.
Operands are 3 bits wide, so the 4-bit sum always fits into FIFO C.

    go = A has data & B has data & C has room & not t      (4082, gate 1)
    t <= go at every rising clock edge                      (4013 #2, flip-flop 2)
    rising edge of t:  SI of C goes high, C takes A + B
    falling edge of t, one clock later:  SO of A and B fall, A and B drop the pair
    push A, push B and pop C go through flip-flops (4013 #1 FF1, 4013 #2 FF1,
    4013 #1 FF2), so that every press gives one clean edge in step with the clock.

One description drives the breadboard drawing, the chip-connection drawing, the
wiring checklist and a pin-level check that rebuilds the netlist from the wires
and simulates it with fifo_sim.  Wires are placed by a negotiated-congestion
maze router (PathFinder), so they never run on top of each other.
"""

import heapq
import random
from collections import defaultdict
from functools import lru_cache
from html import escape

import fifo_sim
from arbiter import gate_shape, gnd_symbol, junctions, lab_html, lab_svg, ortho, rpath, ru_plural, tag, vdd_symbol

# ----------------------------------------------------------------------------
# Chips and pins
# ----------------------------------------------------------------------------

PINS = {
    "40105": {1: "OE", 2: "DIR", 3: "SI", 4: "D0", 5: "D1", 6: "D2", 7: "D3", 8: "GND", 9: "MR",
              10: "Q3", 11: "Q2", 12: "Q1", 13: "Q0", 14: "DOR", 15: "SO", 16: "VCC"},
    "4008": {1: "A4", 2: "B3", 3: "A3", 4: "B2", 5: "A2", 6: "B1", 7: "A1", 8: "VSS", 9: "CIN",
             10: "S1", 11: "S2", 12: "S3", 13: "S4", 14: "COUT", 15: "B4", 16: "VDD"},
    "4013": {1: "Q1", 2: "~Q1", 3: "CLK1", 4: "R1", 5: "D1", 6: "S1", 7: "VSS",
             8: "S2", 9: "D2", 10: "R2", 11: "CLK2", 12: "~Q2", 13: "Q2", 14: "VDD"},
    "4082": {1: "J", 2: "A", 3: "B", 4: "C", 5: "D", 6: "NC", 7: "VSS",
             8: "NC", 9: "E", 10: "F", 11: "G", 12: "H", 13: "K", 14: "VDD"},
}
NPINS = {"40105": 16, "4008": 16, "4013": 14, "4082": 14}
OUTPUTS = {"40105": {2, 10, 11, 12, 13, 14}, "4008": {10, 11, 12, 13, 14}, "4013": {1, 2, 12, 13},
           "4082": {1, 13}}
SUPPLY = {"40105": (16, 8), "4008": (16, 8), "4013": (14, 7), "4082": (14, 7)}  # VDD, GND pins

# id, type, board (1 = top board with the power module, 2 = bottom board), column of pin 1
CHIPS = [
    ("U1", "4013", 2, 4),
    ("U2", "4013", 2, 13),
    ("A", "40105", 2, 24),
    ("B", "40105", 2, 36),
    ("C", "40105", 1, 10),
    ("AND", "4082", 1, 21),
    ("ADD", "4008", 1, 30),
]
CHIP = {c[0]: c for c in CHIPS}
CHIP_TYPES = {c[0]: c[1] for c in CHIPS}
CHIP_LABEL = {"U1": "4013 #1", "U2": "4013 #2", "A": "40105 A", "B": "40105 B", "C": "40105 C",
              "AND": "4082", "ADD": "4008"}

# Expected net on every chip pin (None: output not used, "NC": no connection inside the chip).
NETLIST = {
    "A": {1: "GND", 2: None, 3: "sA", 4: "d0", 5: "d1", 6: "d2", 7: "GND", 9: "rst",
          10: None, 11: "a2", 12: "a1", 13: "a0", 14: "rA", 15: "t"},
    "B": {1: "GND", 2: None, 3: "sB", 4: "d0", 5: "d1", 6: "d2", 7: "GND", 9: "rst",
          10: None, 11: "b2", 12: "b1", 13: "b0", 14: "rB", 15: "t"},
    "C": {1: "GND", 2: "fC", 3: "t", 4: "s0", 5: "s1", 6: "s2", 7: "s3", 9: "rst",
          10: "c3", 11: "c2", 12: "c1", 13: "c0", 14: "vC", 15: "pC"},
    "ADD": {1: "GND", 2: "b2", 3: "a2", 4: "b1", 5: "a1", 6: "b0", 7: "a0", 9: "GND",
            10: "s0", 11: "s1", 12: "s2", 13: "s3", 14: None, 15: "GND"},
    "AND": {1: "go", 2: "tb", 3: "fC", 4: "rB", 5: "rA", 6: "NC", 8: "NC",
            9: "GND", 10: "GND", 11: "GND", 12: "GND", 13: None},
    "U1": {1: "sA", 2: None, 3: "clk", 4: "rst", 5: "pushA", 6: "GND",
           8: "GND", 9: "popC", 10: "rst", 11: "clk", 12: "pC", 13: None},
    "U2": {1: "sB", 2: None, 3: "clk", 4: "rst", 5: "pushB", 6: "GND",
           8: "GND", 9: "go", 10: "rst", 11: "clk", 12: "tb", 13: "t"},
}
for _cid, _typ, *_ in CHIPS:
    NETLIST[_cid][SUPPLY[_typ][0]] = "VDD"
    NETLIST[_cid][SUPPLY[_typ][1]] = "GND"
    assert set(NETLIST[_cid]) == set(range(1, NPINS[_typ] + 1)), _cid

# What each flip-flop of the two 4013s does
FF_ROLE = {("U1", 1): "syncA", ("U1", 2): "syncPop", ("U2", 1): "syncB", ("U2", 2): "transfer"}

# 8-LED module plugged straight into row a over the top pins of FIFO C; it lies over the top edge
# of the top board.  GND is one column left of pin 16, LED k sits over pin 17 - k.
LC_CHIP = "C"
# 8-LED module wired to A and B: header in row g of the top board, GND at column LA_G, LED k at LA_G + k.
LA_BOARD, LA_G = 1, 40
LA_USE = {1: "rA", 2: "a2", 3: "a1", 4: "a0", 5: "rB", 6: "b2", 7: "b1", 8: "b0"}
# Single 5V LEDs: net, chip, pin, colour.  Long leg in row j of the pin column, short leg in the - rail.
SINGLE_LEDS = [("fC", "C", 2, "yellow")]

MODULES = [  # id, net, kind, centre column under the bottom board, target (chip, pin) or None
    ("popC", "popC", "btn", 2, None),
    ("clk", "clk", "clk", 6, ("U1", 3)),
    ("rst", "rst", "btn", 10, ("U1", 4)),
    ("pushA", "pushA", "btn", 14, ("U1", 5)),
    ("pushB", "pushB", "btn", 18, ("U2", 5)),
    ("d0", "d0", "btn", 25, ("A", 4)),
    ("d1", "d1", "btn", 29, ("A", 5)),
    ("d2", "d2", "btn", 33, ("A", 6)),
]
MODULE = {m[0]: m for m in MODULES}
POPC_HOLE = (2, 1)  # board, column where the pop C module lands (bottom half); a wire takes it on

# Connections.  Each net is a set of terminals; the router decides which terminal each wire joins.
# Terminals: ("P", chip, pin), ("L", k) = LED k of the A/B module, ("H", board, column, half).
SIGNALS = [
    ("d0", ("P", "A", 4), ("P", "B", 4)),
    ("d1", ("P", "A", 5), ("P", "B", 5)),
    ("d2", ("P", "A", 6), ("P", "B", 6)),
    ("sA", ("P", "U1", 1), ("P", "A", 3)),
    ("sB", ("P", "U2", 1), ("P", "B", 3)),
    ("popC", ("H", 2, POPC_HOLE[1], "B"), ("P", "U1", 9)),
    ("pC", ("P", "U1", 12), ("P", "C", 15)),
    ("a0", ("P", "A", 13), ("P", "ADD", 7)),
    ("a1", ("P", "A", 12), ("P", "ADD", 5)),
    ("a2", ("P", "A", 11), ("P", "ADD", 3)),
    ("b0", ("P", "B", 13), ("P", "ADD", 6)),
    ("b1", ("P", "B", 12), ("P", "ADD", 4)),
    ("b2", ("P", "B", 11), ("P", "ADD", 2)),
    ("s0", ("P", "ADD", 10), ("P", "C", 4)),
    ("s1", ("P", "ADD", 11), ("P", "C", 5)),
    ("s2", ("P", "ADD", 12), ("P", "C", 6)),
    ("s3", ("P", "ADD", 13), ("P", "C", 7)),
    ("rA", ("P", "A", 14), ("L", 1)),
    ("a2", ("P", "A", 11), ("L", 2)),
    ("a1", ("P", "A", 12), ("L", 3)),
    ("a0", ("P", "A", 13), ("L", 4)),
    ("rB", ("P", "B", 14), ("L", 5)),
    ("b2", ("P", "B", 11), ("L", 6)),
    ("b1", ("P", "B", 12), ("L", 7)),
    ("b0", ("P", "B", 13), ("L", 8)),
    ("rA", ("P", "A", 14), ("P", "AND", 5)),
    ("rB", ("P", "B", 14), ("P", "AND", 4)),
    ("fC", ("P", "C", 2), ("P", "AND", 3)),
    ("tb", ("P", "U2", 12), ("P", "AND", 2)),
    ("go", ("P", "AND", 1), ("P", "U2", 9)),
    ("t", ("P", "U2", 13), ("P", "B", 15)),
    ("t", ("P", "B", 15), ("P", "A", 15)),
    ("t", ("P", "U2", 13), ("P", "C", 3)),
    ("clk", ("P", "U1", 3), ("P", "U1", 11)),
    ("clk", ("P", "U1", 3), ("P", "U2", 3)),
    ("clk", ("P", "U2", 3), ("P", "U2", 11)),
    ("rst", ("P", "U1", 4), ("P", "U1", 10)),
    ("rst", ("P", "U1", 4), ("P", "U2", 4)),
    ("rst", ("P", "U2", 4), ("P", "U2", 10)),
    ("rst", ("P", "U1", 10), ("P", "A", 9)),
    ("rst", ("P", "A", 9), ("P", "B", 9)),
    ("rst", ("P", "B", 9), ("P", "C", 9)),
]

# Stage 1 is the one-FIFO demo (BB8): 4013 #1, FIFO A, the A half of the LED module, and a
# temporary wire that lets the pop button drive SO of A.
STAGE1_CHIPS = {"U1", "A"}
STAGE1_MODULES = {"popC", "clk", "rst", "pushA", "d0", "d1", "d2"}
TEMP_WIRE = ("pC", ("P", "U1", 12), ("P", "A", 15))


def term_stage(t):
    if t[0] == "P":
        return 1 if t[1] in STAGE1_CHIPS else 2
    if t[0] == "L":
        return 1 if t[1] <= 4 else 2
    return 1


# ----------------------------------------------------------------------------
# Geometry (SVG units).  Two 830-point boards, the bottom board below the top one.
# ----------------------------------------------------------------------------

BOARD_Y = {1: 0, 2: 352}
ROW_Y = dict(a=78, b=94, c=110, d=126, e=142, f=190, g=206, h=222, i=238, j=254)
RAIL_Y = {"T-": 30, "T+": 46, "B-": 286, "B+": 302}
MOD_Y = BOARD_Y[2] + 372
PWR_COLS = 6       # the power module covers the left end of the top board
LEDMOD_UP = 66     # the LED module on C lies over the top edge, this far above row a
LA_TOP = 106       # top of the A/B LED module body, relative to the board


def bx(col):
    return 70 + (col - 1) * 16


def pin_pos(cid, pin):
    """(board, column, half) of a chip pin; notch on the left, pin 1 bottom left."""
    _, typ, board, c = CHIP[cid]
    n = NPINS[typ]
    if pin <= n // 2:
        return board, c + pin - 1, "B"
    return board, c + n - pin, "T"


def chip_span(cid):
    _, typ, board, c = CHIP[cid]
    return board, c, c + NPINS[typ] // 2 - 1


def lc_g():
    """Board and GND column of the LED module on C."""
    _, typ, board, c = CHIP[LC_CHIP]
    return board, c - 1


def lc_pin_net(k):
    return NETLIST[LC_CHIP][17 - k]


def chip_free(board, col):
    for cid, typ, b, c in CHIPS:
        if b == board and c <= col <= c + NPINS[typ] // 2 - 1:
            return False
    return True


def y_of(board, key):
    off = BOARD_Y[board]
    return off + (ROW_Y[key] if key in ROW_Y else RAIL_Y[key])


# ----------------------------------------------------------------------------
# Fixed wires: rail jumpers, straight power and tie-off wires, the modules, the single LEDs
# ----------------------------------------------------------------------------

RAIL_JUMPERS = [  # (board, rail, column) -> (board, rail, column)
    ((1, "B+", 63), (2, "T+", 63)),
    ((1, "B-", 62), (2, "T-", 62)),
    ((2, "T+", 61), (2, "B+", 61)),
    ((2, "T-", 60), (2, "B-", 60)),
]


def module_cols(m):
    return m[3] - 1, m[3], m[3] + 1


def chip_stage(cid):
    return 1 if cid in STAGE1_CHIPS else 2


def fixed_wires():
    w = []
    for (b0, r0, c0), (b1, r1, c1) in RAIL_JUMPERS:
        w.append(dict(group="Rails", stage=1, net="+5V" if r0.endswith("+") else "GND",
                      a=("R", b0, r0, c0), b=("R", b1, r1, c1), kind="M-M",
                      pts=[(c0, y_of(b0, r0)), (c1, y_of(b1, r1))]))
    lb, lg = lc_g()
    lc_cols = set(range(lg, lg + 9))
    for cid, typ, board, c in CHIPS:
        vdd, gnd = SUPPLY[typ]
        _, col, _ = pin_pos(cid, vdd)
        if not (board == lb and col in lc_cols):
            w.append(dict(group="Power", stage=chip_stage(cid), net="+5V", a=("H", board, col, "a"),
                          b=("R", board, "T+", col), kind="M-M", pin=(cid, vdd),
                          pts=[(col, y_of(board, "a")), (col, y_of(board, "T+"))]))
        _, col, _ = pin_pos(cid, gnd)
        w.append(dict(group="Power", stage=chip_stage(cid), net="GND", a=("H", board, col, "j"),
                      b=("R", board, "B-", col), kind="M-M", pin=(cid, gnd),
                      pts=[(col, y_of(board, "j")), (col, y_of(board, "B-"))]))
    for cid, typ, board, c in CHIPS:
        gnd = SUPPLY[typ][1]
        for p in range(1, NPINS[typ] + 1):
            if NETLIST[cid][p] != "GND" or p == gnd:
                continue
            _, col, half = pin_pos(cid, p)
            row, rail = ("j", "B-") if half == "B" else ("a", "T-")
            assert half == "B" or not (board == lb and col in lc_cols)
            w.append(dict(group="Tie-offs", stage=chip_stage(cid), net="GND", a=("H", board, col, row),
                          b=("R", board, rail, col), kind="M-M", pin=(cid, p),
                          pts=[(col, y_of(board, row)), (col, y_of(board, rail))]))
    w.append(dict(group="LED module", stage=1, net="GND", a=("H", LA_BOARD, LA_G, "j"),
                  b=("R", LA_BOARD, "B-", LA_G), kind="M-M", led="LA",
                  pts=[(LA_G, y_of(LA_BOARD, "j")), (LA_G, y_of(LA_BOARD, "B-"))]))
    for net, cid, p, colour in SINGLE_LEDS:
        board, col, half = pin_pos(cid, p)
        w.append(dict(group="LEDs", stage=chip_stage(cid), net=net, a=("H", board, col, "j"),
                      b=("R", board, "B-", col), kind="LED", colour=colour, pin=(cid, p),
                      pts=[(col, y_of(board, "j")), (col, y_of(board, "B-"))]))
    bottom = BOARD_Y[2] + 320
    for m in MODULES:
        mid, net, kind, cc, target = m
        cp, co, cm = module_cols(m)
        board, col = (pin_pos(*target)[:2] if target else POPC_HOLE)
        st = 1 if mid in STAGE1_MODULES else 2
        w.append(dict(group="Modules", stage=st, net="+5V", a=("M", mid, "+"), b=("R", 2, "B+", cp), kind="M-F",
                      pts=[(cp, y_of(2, "B+")), (cp, bottom)]))
        w.append(dict(group="Modules", stage=st, net=net, a=("M", mid, "OUT"), b=("H", board, col, "j"),
                      kind="M-F", pts=[(col, y_of(board, "j")), (col, bottom)]))
        w.append(dict(group="Modules", stage=st, net="GND", a=("M", mid, "-"), b=("R", 2, "B-", cm), kind="M-F",
                      pts=[(cm, y_of(2, "B-")), (cm, bottom)]))
    return w


def routed_power():
    """VCC of FIFO C (under its LED module) and the module's GND are routed around the module."""
    lb, lg = lc_g()
    return [dict(group="Power", stage=2, net="+5V", a=("P", LC_CHIP, 16), b=("R", lb, "T+"), pin=(LC_CHIP, 16)),
            dict(group="LED module", stage=2, net="GND", a=("H", lb, lg, "T"), b=("R", lb, "GND"), led="LC")]


# ----------------------------------------------------------------------------
# Maze: wires run vertically at a column and horizontally in the lanes between hole
# rows, in the centre groove where no chip sits, above row a and along the seam
# between the boards.  Wires may cross; they may not share a run or a corner, end
# in the same hole, run over a hole that holds another wire, cross a chip or lie
# under a module.
# ----------------------------------------------------------------------------

_REL = [(30, "T-"), (46, "T+"), (62, "T0"), (78, "a"), (86, "T1"), (94, "b"), (102, "T2"), (110, "c"),
        (118, "T3"), (126, "d"), (134, "T4"), (142, "e"), (166, "CG"), (190, "f"), (198, "B1"), (206, "g"),
        (214, "B2"), (222, "h"), (230, "B3"), (238, "i"), (246, "B4"), (254, "j"), (270, "B5"), (286, "B-"),
        (302, "B+")]
SEAM_Y = (320 + BOARD_Y[2] + 12) // 2
LEVELS = sorted([(y + BOARD_Y[b], b, n) for b in (1, 2) for y, n in _REL] + [(SEAM_Y, 0, "SEAM")])
LEVEL_INDEX = {(b, n): i for i, (y, b, n) in enumerate(LEVELS)}
# y extent of each board half; the centre groove and the seam belong to both neighbours
REGION_EXT = [(0, 166), (166, SEAM_Y), (SEAM_Y, BOARD_Y[2] + 166), (BOARD_Y[2] + 166, BOARD_Y[2] + 330)]
LEVEL_OF_Y = {y: i for i, (y, b, n) in enumerate(LEVELS)}
LANE_NAMES = {"T0", "T1", "T2", "T3", "T4", "CG", "B1", "B2", "B3", "B4", "B5", "SEAM"}
COLS = range(1, 64)


def forbidden_areas():
    f = []
    for cid, typ, board, c in CHIPS:
        off = BOARD_Y[board]
        f.append((c - 0.4, c + NPINS[typ] // 2 - 1 + 0.4, off + ROW_Y["e"] - 2, off + ROW_Y["f"] + 2))
    lb, lg = lc_g()
    off = BOARD_Y[lb]
    f.append((lg - 0.45, lg + 8.45, off + ROW_Y["a"] - LEDMOD_UP, off + ROW_Y["a"] + 3))
    off = BOARD_Y[LA_BOARD]
    f.append((LA_G - 0.45, LA_G + 8.45, off + LA_TOP - 2, off + ROW_Y["g"] + 3))
    f.append((-1, PWR_COLS + 0.5, -20, BOARD_Y[2] - 10))
    return f


class Maze:
    def __init__(self):
        n = len(LEVELS)
        self.occ_h, self.occ_v, self.occ_ve, self.occ_he = {}, {}, {}, {}
        self.forbid = forbidden_areas()
        self.vblock, self.hblock = set(), set()
        for x in COLS:
            for i in range(n - 1):
                y0, y1 = LEVELS[i][0], LEVELS[i + 1][0]
                if any(fx0 <= x <= fx1 and y0 <= fy1 and y1 >= fy0 for fx0, fx1, fy0, fy1 in self.forbid):
                    self.vblock.add((x, i))
            for i in range(n):
                y = LEVELS[i][0]
                if LEVELS[i][2] in LANE_NAMES and x < 63 and any(
                        fy0 <= y <= fy1 and x <= fx1 and x + 1 >= fx0 for fx0, fx1, fy0, fy1 in self.forbid):
                    self.hblock.add((x, i))

    def mark_vertical(self, x, ya, yb, wid):
        ya, yb = sorted((ya, yb))
        for i, (y, b, nm) in enumerate(LEVELS):
            if ya - 0.5 <= y <= yb + 0.5:
                self.occ_v[(x, i)] = wid
        for i in range(len(LEVELS) - 1):
            if LEVELS[i][0] < yb and LEVELS[i + 1][0] > ya:
                self.occ_ve[(x, i)] = wid


def end_nodes(end, maze):
    """Nodes (column, level) where a wire end may sit."""
    kind = end[0]
    if kind == "R":
        _, board, rail = end[:3]
        rails = ["T-", "B-"] if rail == "GND" else [rail]
        out = []
        for r in rails:
            i = LEVEL_INDEX[(board, r)]
            for x in COLS:
                if maze.occ_v.get((x, i)) is None and (x, i) not in maze.vblock and (x, i - 1) not in maze.vblock:
                    out.append((x, i))
        return out
    if kind == "L":
        col = LA_G + end[1]
        return [(col, LEVEL_INDEX[(LA_BOARD, r)]) for r in "hij"
                if maze.occ_v.get((col, LEVEL_INDEX[(LA_BOARD, r)])) is None]
    if kind == "P":
        board, col, half = pin_pos(end[1], end[2])
    else:
        _, board, col, half = end
    lb, lg = lc_g()
    free_col = chip_free(board, col) and not (board == LA_BOARD and LA_G <= col <= LA_G + 8)
    rows = ("abcde" if free_col else "abcd") if half == "T" else ("fghij" if free_col else "ghij")
    out = []
    for r in rows:
        if r == "a" and board == lb and lg <= col <= lg + 8:
            continue
        i = LEVEL_INDEX[(board, r)]
        if maze.occ_v.get((col, i)) is None:
            out.append((col, i))
    return out


class Negotiator:
    """PathFinder costs: every resource gets more expensive while it is overused."""
    BEND = 26

    def __init__(self, maze):
        self.m = maze
        self.use = defaultdict(int)
        self.hist = defaultdict(float)
        self.pf = 0.5

    @staticmethod
    def res_of(nodes):
        r = []
        n = len(nodes)
        for k, (x, i) in enumerate(nodes):
            if k == 0 or k == n - 1:
                r.append(("v", x, i))
                continue
            din = "v" if nodes[k - 1][0] == x else "h"
            dout = "v" if nodes[k + 1][0] == x else "h"
            r += [("v", x, i), ("h", x, i)] if din != dout else [(din, x, i)]
        for (x0, i0), (x1, i1) in zip(nodes, nodes[1:]):
            r.append(("ve", x0, min(i0, i1)) if x0 == x1 else ("he", min(x0, x1), i0))
        return r

    def cost(self, key):
        return (1 + self.hist[key]) * (1 + self.pf * self.use[key])

    def add(self, nodes, k=1):
        for r in self.res_of(nodes):
            self.use[r] += k

    def overuse(self):
        return {r: u for r, u in self.use.items() if u > 1}

    def astar(self, starts, goals, band=True):
        """band: keep the wire within the board halves of its two ends."""
        m = self.m
        goalset = set(goals)
        if band and starts and goals:
            ys = [LEVELS[n[1]][0] for n in list(starts) + list(goals)]
            ylo = min(lo for lo, hi in REGION_EXT if any(lo <= y <= hi for y in ys) and lo <= min(ys))
            yhi = max(hi for lo, hi in REGION_EXT if any(lo <= y <= hi for y in ys) and hi >= max(ys))
        else:
            ylo, yhi = -1e9, 1e9
        gpts = [(g[0], LEVELS[g[1]][0]) for g in goals]
        if not gpts:
            return None

        def h(x, i):
            y = LEVELS[i][0]
            return min(abs(x - a) * 16 + abs(y - b) for a, b in gpts)

        pq, best, prev, done = [], {}, {}, set()
        for s in starts:
            st = (s[0], s[1], "v")
            c0 = 16 * self.cost(("v", s[0], s[1]))
            best[st] = c0
            heapq.heappush(pq, (c0 + h(*s), c0, st, None))
        while pq:
            f, g, st, par = heapq.heappop(pq)
            if st in done:
                continue
            done.add(st)
            prev[st] = par
            x, i, d = st
            if (x, i) in goalset and par is not None:
                path = [(x, i)]
                p = par
                while p is not None:
                    if (p[0], p[1]) != path[-1]:
                        path.append((p[0], p[1]))
                    p = prev[p]
                return path[::-1]
            lane_here = LEVELS[i][2] in LANE_NAMES
            for dx, di in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nd = "v" if dx == 0 else "h"
                nx, ni = x + dx, i + di
                if nx < 1 or nx > 63 or ni < 0 or ni >= len(LEVELS) or not ylo <= LEVELS[ni][0] <= yhi:
                    continue
                if nd == "h" and (not lane_here or par is None):
                    continue
                if nd == "v":
                    e = (x, min(i, ni))
                    if e in m.vblock or e in m.occ_ve or (nx, ni) in m.occ_v:
                        continue
                    step = abs(LEVELS[ni][0] - LEVELS[i][0]) * self.cost(("ve",) + e) + 4 * self.cost(("v", nx, ni))
                else:
                    e = (min(x, nx), i)
                    if e in m.hblock or e in m.occ_he or (nx, ni) in m.occ_h:
                        continue
                    step = 16 * self.cost(("he",) + e) + 4 * self.cost(("h", nx, ni))
                if par is not None and nd != d:
                    if (x, i) in m.occ_h or (x, i) in m.occ_v:
                        continue
                    step += self.BEND * self.cost(("h", x, i)) * self.cost(("v", x, i))
                ns = (nx, ni, nd)
                ng = g + step
                if ng < best.get(ns, 1e18):
                    best[ns] = ng
                    heapq.heappush(pq, (ng + h(nx, ni), ng, ns, st))
        return None


def net_terminals():
    """{net: [terminals]}: stage-1 terminals first, so that stage 1 is connected by its own wires."""
    nets = {}
    for net, a, b in SIGNALS:
        for e in (a, b):
            nets.setdefault(net, [])
            if e not in nets[net]:
                nets[net].append(e)
    return {n: sorted(ts, key=term_stage) for n, ts in nets.items()}


def path_len(nodes):
    pts = nodes_to_pts(nodes)
    return sum(abs(p[0] - q[0]) * 16 + abs(p[1] - q[1]) for p, q in zip(pts, pts[1:])) + 26 * (len(pts) - 2)


def nodes_to_pts(nodes):
    pts = [(x, LEVELS[i][0]) for x, i in nodes]
    r = [pts[0]]
    for k in range(1, len(pts) - 1):
        a, b, c = r[-1], pts[k], pts[k + 1]
        if (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
            continue
        r.append(b)
    r.append(pts[-1])
    return r


def negotiate(seed=0, iterations=120, growth=1.3, hist_inc=0.6):
    rnd = random.Random(seed)
    maze = Maze()
    fixed = fixed_wires()
    for k, w in enumerate(fixed):
        (x0, y0), (x1, y1) = w["pts"]
        maze.mark_vertical(x0, y0, y1, ("fixed", k))
    neg = Negotiator(maze)
    power = routed_power()
    nets = net_terminals()
    nodes_of = {}

    def tn(t):
        if t not in nodes_of:
            nodes_of[t] = end_nodes(t, maze)
        return nodes_of[t]

    temp = dict(group="Temporary", stage=1, net=TEMP_WIRE[0], a=TEMP_WIRE[1], b=TEMP_WIRE[2])
    jobs = [("pw", k) for k in range(len(power))] + [("net", n) for n in nets] + [("tmp", 0)]
    routes = {}

    def route_job(job):
        if job[0] in ("pw", "tmp"):
            w = power[job[1]] if job[0] == "pw" else temp
            path = neg.astar(tn(w["a"]), tn(w["b"])) or neg.astar(tn(w["a"]), tn(w["b"]), band=False)
            return [(w, path)] if path else None
        net = job[1]
        terms = nets[net]
        pending, connected, out = list(terms[1:]), [terms[0]], []
        while pending:
            goals = [n for t in connected for n in tn(t)]

            def dist(t):
                return min((abs(a[0] - b[0]) * 16 + abs(LEVELS[a[1]][0] - LEVELS[b[1]][0])
                            for a in tn(t) for b in goals), default=1e9)

            pending.sort(key=lambda t: (term_stage(t), dist(t)))
            t = pending.pop(0)
            if term_stage(t) == 1:
                goals = [n for c in connected if term_stage(c) == 1 for n in tn(c)]
            path = neg.astar(tn(t), goals) or neg.astar(tn(t), goals, band=False)
            if not path:
                for _, p in out:
                    neg.add(p, -1)
                return None
            neg.add(path)
            to = next(c for c in connected if path[-1] in tn(c))
            out.append((dict(group="Signals", net=net, a=t, b=to), path))
            connected.append(t)
        for _, p in out:
            neg.add(p, -1)
        return out

    for it in range(iterations):
        order = jobs[:]
        if it:
            rnd.shuffle(order)
        for job in order:
            for _, p in routes.get(job) or []:
                neg.add(p, -1)
            routes[job] = route_job(job)
            for _, p in routes[job] or []:
                neg.add(p)
        over = neg.overuse()
        if not over and all(routes.values()):
            break
        for r in over:
            neg.hist[r] += hist_inc
        neg.pf *= growth
    ok = not neg.overuse() and all(routes.values())
    if ok:
        cleanup(neg, maze, routes, nets, tn)
    return ok, fixed, routes, maze


def cleanup(neg, maze, routes, nets, tn, rounds=5):
    """Re-route each wire alone, longest first, along the shortest legal path.  A wire may move to
    any pair of terminals that keeps its net (and the stage-1 part of it) connected."""
    neg.hist.clear()
    neg.pf = 1e6
    items = [(job, k) for job, r in routes.items() for k in range(len(r))]
    for _ in range(rounds):
        improved = False
        items.sort(key=lambda jk: -path_len(routes[jk[0]][jk[1]][1]))
        for job, k in items:
            w, path = routes[job][k]
            neg.add(path, -1)
            if job[0] == "net":
                edges = [(x["a"], x["b"]) for j, (x, _) in enumerate(routes[job]) if j != k]
                side, grow = {w["a"]}, True
                while grow:
                    grow = False
                    for u, v in edges:
                        if (u in side) != (v in side):
                            side |= {u, v}
                            grow = True
                left = [t for t in nets[job[1]] if t in side]
                right = [t for t in nets[job[1]] if t not in side]
                if term_stage(w["a"]) == 1 and term_stage(w["b"]) == 1:
                    left = [t for t in left if term_stage(t) == 1]
                    right = [t for t in right if term_stage(t) == 1]
            else:
                left, right = [w["a"]], [w["b"]]
            new = neg.astar([n for t in left for n in tn(t)], [n for t in right for n in tn(t)])
            if new and path_len(new) < path_len(path) - 1 and all(neg.use[r] == 0 for r in neg.res_of(new)):
                a_t = next(t for t in left if new[0] in tn(t))
                b_t = next(t for t in right if new[-1] in tn(t))
                routes[job][k] = (dict(w, a=a_t, b=b_t), new)
                path = new
                improved = True
            neg.add(path)
        if not improved:
            break


def hole_end(node):
    """('H', board, column, row) or ('R', board, rail, column) of a router node."""
    x, i = node
    y, board, name = LEVELS[i]
    if name in RAIL_Y:
        return ("R", board, name, x)
    return ("H", board, x, name)


ROUTE_SEEDS = (1,)  # chosen from seeds 0-7 by the score below; re-check when the placement changes


@lru_cache(maxsize=None)
def routing():
    """Route with a few seeds and keep the shortest result.  Returns (wires, temporary wire)."""
    best = None
    for seed in ROUTE_SEEDS:
        ok, fixed, routes, maze = negotiate(seed=seed)
        if not ok:
            continue
        lens = [path_len(p) for r in routes.values() for _, p in r]
        score = sum(lens) + 4 * max(lens)  # short wires overall, and no single long detour
        if best is None or score < best[0]:
            best = (score, fixed, routes, maze, seed)
    assert best, "no legal routing"
    total, fixed, routes, maze, seed = best
    wires = list(fixed)
    temp = None
    for job, r in routes.items():
        for w, path in r:
            w = dict(w, ta=w["a"], tb=w["b"], pts=nodes_to_pts(path), kind="M-M",
                     a=hole_end(path[0]), b=hole_end(path[-1]))
            if w["group"] == "Signals":
                w["stage"] = max(term_stage(w["ta"]), term_stage(w["tb"]))
            if job[0] == "tmp":
                temp = w
            else:
                wires.append(w)
    return tuple(wires), temp, seed


# ----------------------------------------------------------------------------
# Wire list in checklist order
# ----------------------------------------------------------------------------

GROUP_ORDER = ["Rails", "Power", "Tie-offs", "LED module", "LEDs", "Signals", "Temporary", "Modules"]


def end_sort_key(e):
    if e[0] == "H":
        return (e[1], e[2])
    if e[0] == "R":
        return (e[1], e[3])
    m = MODULE[e[1]]
    return (3, m[3])


@lru_cache(maxsize=None)
def all_wires():
    """Every wire with an id, in the order of the checklist: stage, group, board, column."""
    wires, temp, seed = routing()
    ws = [dict(w) for w in wires] + [dict(temp)]
    ws.sort(key=lambda w: (w["stage"], GROUP_ORDER.index(w["group"]),
                           min(end_sort_key(w["a"]), end_sort_key(w["b"]))))
    for i, w in enumerate(ws, 1):
        w["id"] = i
        # wire ends: put the chip end first
        if w["kind"] != "LED" and w["b"][0] == "H" and w["a"][0] in "R":
            w["a"], w["b"] = w["b"], w["a"]
    return tuple(ws)


# ----------------------------------------------------------------------------
# Pin-level check: rebuild the netlist from the wires and simulate it
# ----------------------------------------------------------------------------

def strip(board, col, row):
    return ("S", board, "T" if row in "abcde" else "B", col)


def node_of(end):
    if end[0] == "H":
        return strip(end[1], end[2], end[3])
    if end[0] == "R":
        return ("R", end[1], end[2])
    return ("M", end[1], end[2])


def occupied_holes():
    """Holes taken by chip legs and LED module headers."""
    occ = {}
    for cid, typ, board, c in CHIPS:
        for p in range(1, NPINS[typ] + 1):
            b, col, half = pin_pos(cid, p)
            occ[(b, col, "e" if half == "T" else "f")] = f"{cid} pin {p}"
    for k in range(9):
        occ[(LA_BOARD, LA_G + k, "g")] = f"A/B LED module pin {k}"
    lb, lg = lc_g()
    for k in range(9):
        occ[(lb, lg + k, "a")] = f"C LED module pin {k}"
    return occ


def build_netlist(wires):
    parent = {}

    def find(n):
        parent.setdefault(n, n)
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def union(a, b):
        parent[find(a)] = find(b)

    union(("R", 1, "T+"), ("R", 1, "B+"))  # the power module feeds both rail pairs of the top board
    union(("R", 1, "T-"), ("R", 1, "B-"))
    for w in wires:
        if w["kind"] == "LED":
            continue
        union(node_of(w["a"]), node_of(w["b"]))
    return find


def check_wiring(wires, chips, override=None):
    """Structural checks.  override: {(chip, pin): net} for stage 1.  Returns (find, name, pinmap, problems)."""
    probs = []
    occ = occupied_holes()
    seen = {}
    for w in wires:
        for e in (w["a"], w["b"]):
            if e[0] != "H":
                continue
            key = e[1:]
            if key in seen:
                probs.append(f"hole {e} used by wires {seen[key]} and {w['id']}")
            seen[key] = w["id"]
            if key in occ:
                probs.append(f"wire {w['id']} ends in {e}, which holds {occ[key]}")
    find = build_netlist(wires)
    vdd, gnd = find(("R", 1, "T+")), find(("R", 1, "T-"))
    if vdd == gnd:
        probs.append("+5V shorted to GND")
    drivers = defaultdict(list)
    drivers[vdd].append(("VDD",))
    drivers[gnd].append(("GND",))
    mods = {w["a"][1] for w in wires if w["a"][0] == "M"}
    for mid in mods:
        m = MODULE[mid]
        if find(("M", mid, "+")) != vdd or find(("M", mid, "-")) != gnd:
            probs.append(f"module {mid}: power")
        drivers[find(("M", mid, "OUT"))].append(("in", m[1]))

    def pnode(cid, p):
        b, col, half = pin_pos(cid, p)
        return find(("S", b, half, col))

    for cid in chips:
        typ = CHIP_TYPES[cid]
        for p in OUTPUTS[typ]:
            drivers[pnode(cid, p)].append(("out", cid, p))
    name = {}
    for n, d in drivers.items():
        if len(d) > 1:
            probs.append(f"net driven by {d}")
        d = d[0]
        if d[0] in ("VDD", "GND"):
            name[n] = d[0]
        elif d[0] == "in":
            name[n] = d[1]
        else:
            name[n] = NETLIST[d[1]][d[2]] or f"{d[1]}.{d[2]}"
    pinmap = {}
    for cid in chips:
        typ = CHIP_TYPES[cid]
        for p in range(1, NPINS[typ] + 1):
            n = pnode(cid, p)
            want = (override or {}).get((cid, p), NETLIST[cid][p])
            got = name.get(n)
            pinmap[(cid, p)] = got
            if want == "NC":
                if got is not None:
                    probs.append(f"{cid} pin {p} is not connected inside the chip but carries {got}")
                continue
            if want is None:
                want = f"{cid}.{p}"
            if got != want:
                probs.append(f"{cid} pin {p} ({PINS[typ][p]}): expected {want}, got {got}")
    return find, name, pinmap, probs


def led_nodes(find, name, stage):
    """{label: net name} for every LED that is in the circuit at this stage."""
    out = {}
    for k, net in LA_USE.items():
        if stage == 2 or k <= 4:
            out[f"LA{k}"] = name.get(find(strip(LA_BOARD, LA_G + k, "h")))
    out["LA0"] = name.get(find(strip(LA_BOARD, LA_G, "h")))
    if stage == 2:
        lb, lg = lc_g()
        for k in range(9):
            out[f"LC{k}"] = name.get(find(strip(lb, lg + k, "b")))
    return out


def sim_full(pinmap, inputs, delays, bounce=True):
    """The FIFO adder scenario.  Returns the list of sums popped from C, read on the LEDs."""
    chips = {c: CHIP_TYPES[c] for c in CHIP_TYPES}
    b = fifo_sim.Bench(chips, pinmap, inputs, delays, bounce=bounce)

    def bits(x):
        return [(x >> i) & 1 for i in range(3)]

    def c_head():
        return sum(b.v(lc_pin_net(4 + k)) << k for k in range(4))

    popped, notes = [], []

    def pop():
        if b.v("vC"):
            popped.append(c_head())
        b.press("popC")

    b.press("rst", hold_ms=300)
    assert b.v("fC") == 1 and b.v("vC") == 0 and b.v("rA") == 0, "after reset"
    b.press("pushA", data=bits(3))
    assert b.v("rA") == 1 and [b.v(n) for n in ("a2", "a1", "a0")] == [0, 1, 1], "A shows 3"
    b.press("pushB", data=bits(2))
    b.wait(1500)
    assert b.v("vC") == 1 and c_head() == 5 and b.v("rA") == 0 and b.v("rB") == 0, "3 + 2 in C"
    for x in (1, 4, 7):
        b.press("pushA", data=bits(x))
    b.wait(1500)
    assert b.m["C"].count() == 1 and b.v("rA") == 1, "A waits for B"
    for y in (2, 3, 0):
        b.press("pushB", data=bits(y))
    b.wait(2000)
    assert b.m["C"].count() == 4, "three more sums"
    for _ in range(5):
        pop()
    for k in range(18):
        b.press("pushA", data=bits(k % 8), after_ms=50)
        b.press("pushB", data=bits(1), after_ms=50)
    b.wait(3000)
    assert b.m["C"].count() == 16 and b.v("fC") == 0, "C full"
    assert b.m["A"].count() == 2 and b.m["B"].count() == 2, "backpressure: A and B keep two pairs"
    pop()
    b.wait(2000)
    assert b.m["C"].count() == 16 and b.m["A"].count() == 1, "one pair moves after one pop"
    for _ in range(18):
        pop()
    want = [5, 3, 7, 7] + [(k % 8) + 1 for k in range(18)]
    assert popped == want, f"popped {popped}"
    return popped, b.sim.problems


def sim_stage1(pinmap, inputs, delays):
    """The one-FIFO demo: push three numbers into A, pop them in the same order."""
    b = fifo_sim.Bench({"U1": "4013", "A": "40105"}, pinmap, inputs, delays)

    def bits(x):
        return [(x >> i) & 1 for i in range(3)]

    def head():
        return sum(b.v(n) << k for k, n in enumerate(("a0", "a1", "a2")))

    b.press("rst", hold_ms=300)
    assert b.v("rA") == 0
    for x in (2, 5, 7):
        b.press("pushA", data=bits(x))
    seen = []
    while b.v("rA"):
        seen.append(head())
        b.press("popC")
    assert seen == [2, 5, 7], seen
    return seen, b.sim.problems


def transfer_ticks(pinmap, inputs):
    """Tick-by-tick record of one transfer, for the table on the page."""
    b = fifo_sim.Bench({c: CHIP_TYPES[c] for c in CHIP_TYPES}, pinmap, inputs, fifo_sim.DELAYS[0], bounce=False)
    rows = []

    def snap(what):
        rows.append(dict(what=what, A=b.m["A"].words(), B=b.m["B"].words(), C=b.m["C"].words(),
                         go=b.v("go"), t=b.v("t")))

    def bits(x):
        return [(x >> i) & 1 for i in range(3)]

    b.press("rst", hold_ms=300)
    for i, b_ in enumerate(bits(3)):
        if b_:
            b.sim.set(inputs[f"d{i}"], 1)
    b.sim.set(inputs["pushA"], 1)
    edge = b.edges
    while b.edges == edge:
        b.wait(10)
    b.wait(50)
    b.sim.set(inputs["pushA"], 0)
    for i in range(3):
        b.sim.set(inputs[f"d{i}"], 0)
    snap("pushA3")
    for i, b_ in enumerate(bits(2)):
        if b_:
            b.sim.set(inputs[f"d{i}"], 1)
    b.sim.set(inputs["pushB"], 1)
    edge = b.edges
    while b.edges == edge:
        b.wait(10)
    b.wait(50)
    b.sim.set(inputs["pushB"], 0)
    for i in range(3):
        b.sim.set(inputs[f"d{i}"], 0)
    snap("pushB2")
    for k in range(3):
        edge = b.edges
        while b.edges == edge:
            b.wait(10)
        b.wait(50)
        snap("tick")
    return rows


@lru_cache(maxsize=None)
def check():
    """Check the wiring and simulate it.  Returns a summary; raises AssertionError on a fault."""
    wires = all_wires()
    final = [w for w in wires if w["group"] != "Temporary"]
    find, name, pinmap, probs = check_wiring(final, list(CHIP_TYPES))
    assert not probs, probs
    leds = led_nodes(find, name, 2)
    for k, net in LA_USE.items():
        assert leds[f"LA{k}"] == net, f"A/B LED {k}"
    assert leds["LA0"] == "GND" and leds["LC0"] == "GND", "LED module GND"
    for k in range(1, 9):
        assert leds[f"LC{k}"] == (lc_pin_net(k) if lc_pin_net(k) != "VDD" else "VDD"), f"C LED {k}"
    for w in final:
        if w["kind"] == "LED":
            assert name.get(find(node_of(w["a"]))) == w["net"], f"LED {w['net']}"
            assert find(node_of(w["b"])) == find(("R", 1, "T-")), f"LED {w['net']} cathode"
    inputs = {m[0]: m[1] for m in MODULES}
    sims = []
    for d in fifo_sim.DELAYS:
        popped, sp = sim_full(pinmap, inputs, d)
        assert not sp, sp
        sims.append(popped)
    # stage 1: only the stage-1 wires and the temporary wire
    s1 = [w for w in wires if w["stage"] == 1]
    find1, name1, pinmap1, probs1 = check_wiring(s1, ["U1", "A"], override={("A", 15): TEMP_WIRE[0]})
    assert not probs1, probs1
    for k in range(1, 5):
        assert led_nodes(find1, name1, 1)[f"LA{k}"] == LA_USE[k]
    seen, sp1 = sim_stage1(pinmap1, inputs, fifo_sim.DELAYS[0])
    assert not sp1, sp1
    groups = defaultdict(int)
    for w in final:
        groups[(w["stage"], w["group"])] += 1
    mm = sum(1 for w in final if w["kind"] == "M-M")
    mf = sum(1 for w in final if w["kind"] == "M-F")
    ticks = transfer_ticks(pinmap, inputs)
    return dict(wires=wires, mm=mm, mf=mf, groups=dict(groups), popped=sims[0], stage1=seen, ticks=ticks,
                n1=sum(1 for w in wires if w["stage"] == 1 and w["kind"] == "M-M"),
                n1mf=sum(1 for w in wires if w["stage"] == 1 and w["kind"] == "M-F"))


# ----------------------------------------------------------------------------
# Nets: label ("~" = overline) and colour.  Meanings are in T.
# ----------------------------------------------------------------------------

NETS = {
    "d0": ("d0", "#e8590c"), "d1": ("d1", "#f08c00"), "d2": ("d2", "#e0a800"),
    "pushA": ("push A", "#4263eb"), "pushB": ("push B", "#7048e8"), "popC": ("pop C", "#ae3ec9"),
    "clk": ("clk", "#868e96"), "rst": ("rst", "#c2410c"),
    "sA": ("sA", "#3b5bdb"), "sB": ("sB", "#6741d9"), "pC": ("~pC", "#9c36b5"),
    "a0": ("a0", "#2b8a3e"), "a1": ("a1", "#37b24d"), "a2": ("a2", "#74b816"),
    "b0": ("b0", "#1864ab"), "b1": ("b1", "#1c7ed6"), "b2": ("b2", "#4dabf7"),
    "s0": ("s0", "#a61e4d"), "s1": ("s1", "#d6336c"), "s2": ("s2", "#e64980"), "s3": ("s3", "#f783ac"),
    "c0": ("c0", "#5f3dc4"), "c1": ("c1", "#5f3dc4"), "c2": ("c2", "#5f3dc4"), "c3": ("c3", "#5f3dc4"),
    "rA": ("rA", "#0c8599"), "rB": ("rB", "#15aabf"), "fC": ("fC", "#a5734d"), "vC": ("vC", "#5c940d"),
    "t": ("t", "#c92a2a"), "tb": ("~t", "#ff8787"), "go": ("go", "#66a80f"),
}
VDD_C, GND_C = "#e03131", "#343a40"
WIRE_NETS = ["d0", "d1", "d2", "sA", "sB", "popC", "pC", "a0", "a1", "a2", "b0", "b1", "b2",
             "s0", "s1", "s2", "s3", "rA", "rB", "fC", "tb", "go", "t", "clk", "rst"]


def net_color(net):
    return {"+5V": VDD_C, "GND": GND_C}.get(net) or NETS[net][1]


def net_label(net):
    return {"+5V": "+5V", "GND": "GND"}.get(net) or NETS[net][0]


# ----------------------------------------------------------------------------
# Words on the diagrams and in the tables
# ----------------------------------------------------------------------------

T = {
    "en": dict(
        meaning=dict(
            d0="data button d0, bit 0", d1="data button d1, bit 1", d2="data button d2, bit 2",
            pushA="push A button", pushB="push B button", popC="pop C button", clk="clock", rst="reset",
            sA="push A in step with the clock: SI of A", sB="push B in step with the clock: SI of B",
            pC="pop C in step with the clock, inverted: SO of C",
            a0="head of A, bit 0", a1="head of A, bit 1", a2="head of A, bit 2",
            b0="head of B, bit 0", b1="head of B, bit 1", b2="head of B, bit 2",
            s0="sum, bit 0", s1="sum, bit 1", s2="sum, bit 2", s3="sum, bit 3",
            c0="head of C, bit 0", c1="head of C, bit 1", c2="head of C, bit 2", c3="head of C, bit 3",
            rA="A has data: DOR of A", rB="B has data: DOR of B", fC="C has room: DIR of C",
            vC="C has data: DOR of C", t="transfer", tb="NOT transfer", go="transfer at the next clock edge"),
        aria1="Logic diagram of the FIFO adder: three FIFOs, an adder, a 4-input AND gate and four D flip-flops",
        aria2="Connections between the seven chips of the FIFO adder, pin by pin",
        aria3="Breadboard layout of the FIFO adder on two breadboards with every wire",
        board={1: "top board", 2: "bottom board"}, board_short={1: "top", 2: "bottom"},
        power="POWER MODULE · 5V", cable="9V USB-DC",
        mod_bb={"popC": ["POP C"], "clk": ["CLOCK 555", "~2 Hz"], "rst": ["RESET"], "pushA": ["PUSH A"],
                "pushB": ["PUSH B"], "d0": ["DATA", "d0"], "d1": ["DATA", "d1"], "d2": ["DATA", "d2"]},
        mod_box={"popC": "POP C", "clk": "CLOCK 555", "rst": "RESET", "pushA": "PUSH A", "pushB": "PUSH B",
                 "d0": "DATA d0", "d1": "DATA d1", "d2": "DATA d2"},
        mod_desc={"popC": "pop C module", "clk": "clock 555 module", "rst": "reset module",
                  "pushA": "push A module", "pushB": "push B module", "d0": "data d0 module",
                  "d1": "data d1 module", "d2": "data d2 module"},
        ledmod_ab="A/B LED MODULE", ledmod_c="LED MODULE ON C",
        ledmod_ab_s2="A/B LED module", ledmod_c_s2="LED module on C",
        logic=dict(sync="IN STEP | WITH THE CLOCK", data="DATAPATH", ctrl="FLOW CONTROL",
                   data_in="data d2 d1 d0", push_a="push A", push_b="push B", pop_c="pop C",
                   fifo="FIFO", adder="adder", and4="4-input AND", ff="flip-flop", leds="LEDs",
                   led_ab="LED module A/B", led_c="LED module on C", room="C has room", transfer="transfer",
                   sum_note="s = a + b"),
        ff_short={"syncA": "bottom: FF1, push A", "syncPop": "top: FF2, pop C",
                  "syncB": "bottom: FF1, push B", "transfer": "top: FF2, transfer t"},
        led_single={"fC": "C has room", "t": "transfer"}, led_colour={"yellow": "yellow", "green": "green"},
        chip_pin="{chip} pin {p}", hole="{board} {h}",
        rail="{board}, {side} {sign} rail, column {col}", top="top", bottom="bottom",
        la_pin="A/B LED module, LED {k}", la_gnd="A/B LED module, GND",
        lc_gnd="under the GND pin of the LED module on C",
        jumper_in="the {m} jumper is in {h}",
        groups={"Rails": "Power for the bottom board: rail to rail",
                "Power": "Power for the chips (red to +, black to −)",
                "Tie-offs": "Unused inputs: CMOS inputs must not float",
                "LED module": "LED module ground", "LEDs": "Single 5V LEDs (no wire: the LED itself)",
                "Signals": "Signal wires", "Modules": "Button and clock modules (male-female jumpers)",
                "Temporary": "Temporary wire for the one-FIFO demo"},
        stage={1: "Stage 1: one FIFO", 2: "Stage 2: the FIFO adder"},
        led_long="long leg in {h}, short leg in the {board} − rail",
        temp_note="remove it in stage 2",
        wires=lambda n: f"{n} wire{'s' if n != 1 else ''}",
        th_wires=("#", "Net", "From", "To"), done="wire {i} done",
        count="' + n + ' of ' + boxes.length + ' wires done",
        th_pins=("Chip", "What it does", "Pins"),
        ff_roles={"syncA": "flip-flop 1: push A in step with the clock",
                  "syncPop": "flip-flop 2: pop C in step with the clock",
                  "syncB": "flip-flop 1: push B in step with the clock",
                  "transfer": "flip-flop 2: transfer t"},
        chip_roles={"A": "FIFO A, operand a", "B": "FIFO B, operand b", "C": "FIFO C, the sums",
                    "AND": "4-input AND, gate 1: go", "ADD": "4-bit adder: s = a + b"},
        unused="not used", nc="not connected inside",
        pin="pin",
    ),
    "ru": dict(
        meaning=dict(
            d0="кнопка данных d0, бит 0", d1="кнопка данных d1, бит 1", d2="кнопка данных d2, бит 2",
            pushA="кнопка «записать в A»", pushB="кнопка «записать в B»", popC="кнопка «взять из C»",
            clk="тактовый сигнал", rst="сброс",
            sA="запись в A по такту: SI очереди A", sB="запись в B по такту: SI очереди B",
            pC="чтение из C по такту, инвертированное: SO очереди C",
            a0="голова A, бит 0", a1="голова A, бит 1", a2="голова A, бит 2",
            b0="голова B, бит 0", b1="голова B, бит 1", b2="голова B, бит 2",
            s0="сумма, бит 0", s1="сумма, бит 1", s2="сумма, бит 2", s3="сумма, бит 3",
            c0="голова C, бит 0", c1="голова C, бит 1", c2="голова C, бит 2", c3="голова C, бит 3",
            rA="в A есть данные: DOR очереди A", rB="в B есть данные: DOR очереди B",
            fC="в C есть место: DIR очереди C", vC="в C есть данные: DOR очереди C",
            t="пересылка", tb="НЕ пересылка", go="пересылка на следующем фронте такта"),
        aria1="Логическая схема сумматора на очередях: три FIFO, сумматор, элемент 4И и четыре D-триггера",
        aria2="Соединения между семью микросхемами сумматора на очередях, ножка за ножкой",
        aria3="Монтажная схема сумматора на очередях на двух макетных платах со всеми проводами",
        board={1: "верхняя плата", 2: "нижняя плата"}, board_short={1: "верх.", 2: "нижн."},
        power="БЛОК ПИТАНИЯ · 5V", cable="USB-DC 9V",
        mod_bb={"popC": ["ВЗЯТЬ", "ИЗ C"], "clk": ["ГЕНЕРАТОР", "555 · ~2 Гц"], "rst": ["СБРОС"],
                "pushA": ["ЗАПИСАТЬ", "В A"], "pushB": ["ЗАПИСАТЬ", "В B"], "d0": ["ДАННЫЕ", "d0"],
                "d1": ["ДАННЫЕ", "d1"], "d2": ["ДАННЫЕ", "d2"]},
        mod_box={"popC": "ИЗ C", "clk": "ГЕНЕРАТОР", "rst": "СБРОС", "pushA": "В A", "pushB": "В B",
                 "d0": "ДАННЫЕ d0", "d1": "ДАННЫЕ d1", "d2": "ДАННЫЕ d2"},
        mod_desc={"popC": "кнопка «взять из C»", "clk": "генератор 555", "rst": "кнопка сброса",
                  "pushA": "кнопка «записать в A»", "pushB": "кнопка «записать в B»",
                  "d0": "кнопка данных d0", "d1": "кнопка данных d1", "d2": "кнопка данных d2"},
        mod_gen={"popC": "кнопки «взять из C»", "clk": "генератора 555", "rst": "кнопки сброса",
                 "pushA": "кнопки «записать в A»", "pushB": "кнопки «записать в B»",
                 "d0": "кнопки данных d0", "d1": "кнопки данных d1", "d2": "кнопки данных d2"},
        ledmod_ab="СВЕТОДИОДЫ A И B", ledmod_c="ЛИНЕЙКА НА C",
        ledmod_ab_s2="Линейка для A и B", ledmod_c_s2="Линейка на C",
        logic=dict(sync="СИНХРОНИЗАЦИЯ | С ТАКТОМ", data="ТРАКТ ДАННЫХ", ctrl="УПРАВЛЕНИЕ ПОТОКОМ",
                   data_in="данные d2 d1 d0", push_a="записать в A", push_b="записать в B", pop_c="взять из C",
                   fifo="FIFO", adder="сумматор", and4="элемент 4И", ff="триггер", leds="светодиоды",
                   led_ab="линейка для A и B", led_c="линейка на C", room="в C есть место", transfer="пересылка",
                   sum_note="s = a + b"),
        ff_short={"syncA": "внизу: FF1, запись в A", "syncPop": "вверху: FF2, чтение C",
                  "syncB": "внизу: FF1, запись в B", "transfer": "вверху: FF2, пересылка t"},
        led_single={"fC": "в C есть место", "t": "пересылка"}, led_colour={"yellow": "жёлтый", "green": "зелёный"},
        chip_pin="{chip}, ножка {p}", hole="{board} {h}",
        rail="{board}, {side} шина {sign}, столбик {col}", top="верхняя", bottom="нижняя",
        la_pin="линейка A и B, светодиод {k}", la_gnd="линейка A и B, GND",
        lc_gnd="под выводом GND линейки на C",
        jumper_in="провод от {m} — в {h}",
        groups={"Rails": "Питание нижней платы: от шины к шине",
                "Power": "Питание микросхем (красные к +, чёрные к −)",
                "Tie-offs": "Неиспользуемые входы: входы КМОП нельзя оставлять висящими",
                "LED module": "Земля линейки светодиодов", "LEDs": "Одиночные светодиоды на 5 В (вместо провода — сам светодиод)",
                "Signals": "Сигнальные провода", "Modules": "Кнопки и генератор (перемычки папа-мама)",
                "Temporary": "Временный провод для опыта с одной очередью"},
        stage={1: "Этап 1: одна очередь", 2: "Этап 2: сумматор на очередях"},
        led_long="длинная ножка в {h}, короткая — в шину − ({board})",
        temp_note="на этапе 2 его нужно вынуть",
        wires=lambda n: f"{n} {ru_plural(n, 'провод', 'провода', 'проводов')}",
        th_wires=("#", "Сигнал", "Откуда", "Куда"), done="провод {i} готов",
        count="готово ' + n + ' из ' + boxes.length + ' проводов",
        th_pins=("Микросхема", "Что делает", "Ножки"),
        ff_roles={"syncA": "триггер 1: запись в A по такту",
                  "syncPop": "триггер 2: чтение из C по такту",
                  "syncB": "триггер 1: запись в B по такту",
                  "transfer": "триггер 2: пересылка t"},
        chip_roles={"A": "очередь A, слагаемое a", "B": "очередь B, слагаемое b", "C": "очередь C, суммы",
                    "AND": "элемент 4И, элемент 1: go", "ADD": "4-битный сумматор: s = a + b"},
        unused="не используется", nc="внутри не подключена",
        pin="ножка",
    ),
}


# ----------------------------------------------------------------------------
# 3. Breadboard
# ----------------------------------------------------------------------------

SVG_W, SVG_H = 1100, MOD_Y + 92


def place_tags(cands, blocked):
    """cands: [(segments, label, colour)]; picks a spot on the longest free segment for each tag."""
    out = []
    taken = list(blocked)
    for segs, lab, col in cands:
        w = 6.2 * len(lab.lstrip("~")) + 9
        done = False
        for p, q in sorted(segs, key=lambda s: -(abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))):
            if abs(q[0] - p[0]) + abs(q[1] - p[1]) < 60:
                break
            for f in (0.5, 0.35, 0.65, 0.22, 0.78):
                x, y = p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
                r = (x - w / 2 - 2, y - 9, x + w / 2 + 2, y + 9)
                if any(r[0] < b[2] and r[2] > b[0] and r[1] < b[3] and r[3] > b[1] for b in taken):
                    continue
                out.append((x, y, lab, col))
                taken.append(r)
                done = True
                break
            if done:
                break
    return out


def end_xy(e):
    if e[0] == "H":
        return bx(e[2]), y_of(e[1], e[3])
    if e[0] == "R":
        return bx(e[3]), y_of(e[1], e[2])
    m = MODULE[e[1]]
    return bx(m[3]) + {"+": -16, "OUT": 0, "-": 16}[e[2]], MOD_Y


def wire_path(w):
    """SVG path of a wire and the points of its polyline (None for module wires)."""
    if w["kind"] == "M-F":
        (ax, ay), (bx_, by) = end_xy(w["a"]), end_xy(w["b"])
        if ax == bx_:
            return f"M{ax:g},{ay:g} L{bx_:g},{by:g}", None
        return f"M{ax:g},{ay:g} C{ax:g},{ay - 46:g} {bx_:g},{by + 60:g} {bx_:g},{by:g}", None
    pts = [(bx(x), y) for x, y in w["pts"]]
    return rpath(pts, 5), pts


def board_svg(b, L_):
    off = BOARD_Y[b]
    o = [f'<rect x="44" y="{off + 12}" width="1046" height="308" rx="9" fill="#f4f1e8" stroke="#d6cfbd" '
         f'stroke-width="1.5"/>']
    for name, y in RAIL_Y.items():
        y += off
        tint = "#fbe3e3" if name.endswith("+") else "#e3ebfb"
        line = VDD_C if name.endswith("+") else "#2f6fd0"
        ly = y + (-9 if name == "T-" else 9 if name == "B+" else 0)
        o.append(f'<rect x="60" y="{y - 7}" width="1020" height="14" rx="3" fill="{tint}"/>')
        if ly != y:
            o.append(f'<line x1="66" x2="1074" y1="{ly}" y2="{ly}" stroke="{line}" stroke-width="1.5"/>')
        o.append(f'<rect x="62" y="{y - 8}" width="1008" height="16" fill="url(#bbh)"/>')
        o.append(f'<text x="1082" y="{y + 4}" font-size="12" font-weight="700" fill="{line}">'
                 f'{"+" if name.endswith("+") else "−"}</text>')
    o.append(f'<rect x="62" y="{off + 70}" width="1008" height="80" fill="url(#bbh)"/>'
             f'<rect x="62" y="{off + 182}" width="1008" height="80" fill="url(#bbh)"/>'
             f'<rect x="56" y="{off + 158}" width="1024" height="16" rx="3" fill="#e7e2d4"/>')
    for col in range(1, 64):
        if b == 1 and col <= PWR_COLS:
            continue
        bold = col % 5 == 0 or col == 1
        o.append(f'<text x="{bx(col)}" y="{off + 21}" text-anchor="middle" font-size="{8 if bold else 6.5}" '
                 f'fill="{"#5b5547" if bold else "#8d8676"}" font-weight="{700 if bold else 400}">{col}</text>')
    for r, y in ROW_Y.items():
        if b == 2:
            o.append(f'<text x="54" y="{off + y + 3}" text-anchor="middle" font-size="9" fill="#8d8676">{r}</text>')
        o.append(f'<text x="1068" y="{off + y + 3}" text-anchor="middle" font-size="9" fill="#8d8676">{r}</text>')
    o.append(f'<text x="1086" y="{off + 166}" text-anchor="end" font-size="9" font-weight="700" fill="#8d8676" '
             f'transform="rotate(-90 1086 {off + 166})" dx="34">{escape(L_["board"][b].upper())}</text>')
    return "".join(o)


def chip_svg(cid):
    _, typ, board, c = CHIP[cid]
    off = BOARD_Y[board]
    n = NPINS[typ] // 2
    x0, x1 = bx(c) - 9, bx(c + n - 1) + 9
    o = [f'<rect x="{x0}" y="{off + 147}" width="{x1 - x0}" height="38" rx="3" fill="#2b2f33"/>'
         f'<path d="M{x0},{off + 160} A6,6 0 0 1 {x0},{off + 172}" fill="#f4f1e8"/>']
    for i in range(n):
        x = bx(c + i)
        o.append(f'<rect x="{x - 3}" y="{off + ROW_Y["e"] - 3}" width="6" height="8" rx="1" fill="#c9ced3"/>'
                 f'<rect x="{x - 3}" y="{off + ROW_Y["f"] - 5}" width="6" height="8" rx="1" fill="#c9ced3"/>')
    o.append(f'<text x="{(x0 + x1) / 2}" y="{off + 170}" text-anchor="middle" font-size="12" font-weight="700" '
             f'fill="#ffffff">{CHIP_LABEL[cid]}</text><circle cx="{x0 + 7}" cy="{off + 180}" r="1.8" fill="#9aa0a6"/>')
    return "".join(o)


def ledmod_ab_svg(L_):
    off = BOARD_Y[LA_BOARD]
    lx0, lx1 = bx(LA_G) - 10, bx(LA_G + 8) + 10
    o = [f'<rect x="{lx0}" y="{off + LA_TOP + 2}" width="{lx1 - lx0}" height="{200 - LA_TOP - 2}" rx="5" fill="#1d4f91"/>']
    for k in range(9):
        x = bx(LA_G + k)
        o.append(f'<rect x="{x - 2.5}" y="{off + 198}" width="5" height="10" fill="#c9ced3"/>'
                 f'<text x="{x}" y="{off + 194}" text-anchor="middle" font-size="7.5" fill="#dbe7ff">{"G" if k == 0 else k}</text>')
        if k:
            o.append(f'<rect x="{x - 5}" y="{off + 128}" width="10" height="20" rx="2" fill="#8fd3ff" stroke="#cdeeff"/>'
                     f'<text x="{x}" y="{off + 166}" text-anchor="middle" font-size="8.5" font-weight="700" '
                     f'fill="#ffffff">{lab_svg(net_label(LA_USE[k]))}</text>')
    o.append(f'<text x="{(lx0 + lx1) / 2}" y="{off + 121}" text-anchor="middle" font-size="8.5" fill="#dbe7ff" '
             f'font-weight="600">{L_["ledmod_ab"]}</text>')
    return "".join(o)


def ledmod_c_svg(L_):
    lb, lg = lc_g()
    off = BOARD_Y[lb]
    lx0, lx1 = bx(lg) - 10, bx(lg + 8) + 10
    top = off + ROW_Y["a"] - LEDMOD_UP
    o = [f'<rect x="{lx0}" y="{top}" width="{lx1 - lx0}" height="{LEDMOD_UP + 4}" rx="5" fill="#1d4f91"/>']
    for k in range(9):
        x = bx(lg + k)
        o.append(f'<rect x="{x - 2.5}" y="{off + ROW_Y["a"] - 4}" width="5" height="9" fill="#c9ced3"/>')
        if k:
            pin = 17 - k
            o.append(f'<rect x="{x - 5}" y="{top + 16}" width="10" height="18" rx="2" fill="#ffb3b3" stroke="#ffe0e0"/>'
                     f'<text x="{x}" y="{top + 45}" text-anchor="middle" font-size="7" font-weight="700" '
                     f'fill="#ffffff">{PINS["40105"][pin]}</text>'
                     f'<text x="{x}" y="{top + 57}" text-anchor="middle" font-size="7.5" fill="#dbe7ff">{k}</text>')
        else:
            o.append(f'<text x="{x}" y="{top + 57}" text-anchor="middle" font-size="7.5" fill="#dbe7ff">G</text>')
    o.append(f'<text x="{(lx0 + lx1) / 2}" y="{top + 10}" text-anchor="middle" font-size="7.5" fill="#dbe7ff" '
             f'font-weight="600">{L_["ledmod_c"]}</text>')
    return "".join(o)


def single_led_svg(w):
    (x, y0), (_, y1) = end_xy(w["a"]), end_xy(w["b"])
    fill = {"yellow": "#ffd43b", "green": "#51cf66"}[w["colour"]]
    ym = (y0 + y1) / 2
    return (f'<path d="M{x},{y0} V{ym - 4} M{x},{y1} V{ym + 4}" stroke="#868e96" stroke-width="1.6"/>'
            f'<circle cx="{x}" cy="{ym}" r="7.5" fill="{fill}" stroke="#7a6a00" stroke-opacity=".5" stroke-width="1.2"/>'
            f'<circle cx="{x - 2.4}" cy="{ym - 2.4}" r="2" fill="#ffffff" opacity=".8"/>'
            f'<circle cx="{x}" cy="{y0}" r="2.6" fill="#3d3d3d" stroke="#fff" stroke-width=".8"/>'
            f'<circle cx="{x}" cy="{y1}" r="2.6" fill="#3d3d3d" stroke="#fff" stroke-width=".8"/>')


def power_module_svg(L_):
    return ('<rect x="26" y="6" width="112" height="320" rx="7" fill="#2f6fd0" opacity=".96"/>'
            '<rect x="18" y="128" width="30" height="34" rx="3" fill="#222"/>'
            '<rect x="22" y="176" width="24" height="28" rx="2" fill="#adb5bd"/>'
            '<rect x="100" y="56" width="22" height="12" rx="2" fill="#ffd43b"/>'
            '<rect x="100" y="264" width="22" height="12" rx="2" fill="#ffd43b"/>'
            '<text x="111" y="83" text-anchor="middle" font-size="8" font-weight="700" fill="#fff">5V</text>'
            '<text x="111" y="259" text-anchor="middle" font-size="8" font-weight="700" fill="#fff">5V</text>'
            '<text transform="translate(80,166) rotate(-90)" text-anchor="middle" font-size="11" '
            f'font-weight="700" fill="#fff">{L_["power"]}</text>'
            '<path d="M18,145 C2,150 2,190 -4,236" stroke="#555" stroke-width="6" fill="none" stroke-linecap="round"/>'
            f'<text x="2" y="342" font-size="10" fill="#6b6455">{L_["cable"]}</text>')


def module_svg(m, L_):
    mid, net, kind, cc, target = m
    x = bx(cc)
    body = "#1b5fb8" if kind == "clk" else "#2f6fd0"
    o = [f'<rect x="{x - 28}" y="{MOD_Y}" width="56" height="44" rx="5" fill="{body}"/>']
    for dx, t in ((-16, "+"), (0, "OUT"), (16, "−")):
        o.append(f'<text x="{x + dx}" y="{MOD_Y + 11}" text-anchor="middle" font-size="7" fill="#fff" '
                 f'font-weight="700">{t}</text>')
    if kind == "clk":
        o.append(f'<rect x="{x - 14}" y="{MOD_Y + 17}" width="18" height="13" rx="1" fill="#222"/>'
                 f'<text x="{x - 5}" y="{MOD_Y + 26}" text-anchor="middle" font-size="6" fill="#ddd">555</text>'
                 f'<circle cx="{x + 14}" cy="{MOD_Y + 26}" r="6" fill="#4dabf7" stroke="#d0ebff"/>'
                 f'<path d="M{x + 10},{MOD_Y + 26} h8" stroke="#1d4f91" stroke-width="2"/>')
    else:
        o.append(f'<rect x="{x - 10}" y="{MOD_Y + 16}" width="20" height="20" rx="2" fill="#495057"/>'
                 f'<circle cx="{x}" cy="{MOD_Y + 26}" r="7" fill="#e2453c" stroke="#a82d27" stroke-width="1.5"/>')
    for k, line in enumerate(L_["mod_bb"][mid]):
        o.append(f'<text x="{x}" y="{MOD_Y + 60 + 12 * k}" text-anchor="middle" font-size="9.5" '
                 f'font-weight="{700 if k == 0 else 400}" fill="#4a4538">{escape(line)}</text>')
    return "".join(o)


def blocked_boxes(view):
    """Rectangles that tags must not cover: chips and LED modules (view 1: breadboard, 2: schematic 2)."""
    ymap = (lambda y: y) if view == 1 else s2y
    out = []
    for cid, typ, board, c in CHIPS:
        off = BOARD_Y[board]
        n = NPINS[typ] // 2
        out.append((bx(c) - 12, ymap(off + ROW_Y["e"] + 2), bx(c + n - 1) + 12, ymap(off + ROW_Y["f"] - 2)))
    lb, lg = lc_g()
    out.append((bx(lg) - 10, BOARD_Y[lb] + ROW_Y["a"] - LEDMOD_UP, bx(lg + 8) + 10, ymap(BOARD_Y[lb] + ROW_Y["a"] + 6)))
    off = BOARD_Y[LA_BOARD]
    out.append((bx(LA_G) - 10, ymap(off + LA_TOP), bx(LA_G + 8) + 10, ymap(off + ROW_Y["g"] + 6)))
    return out


def svg_breadboard(lang="en"):
    L_ = T[lang]
    wires = [w for w in all_wires() if w["group"] != "Temporary"]
    o = [f'<svg class="arb bbv" viewBox="0 0 {SVG_W} {SVG_H}" role="img" aria-label="{L_["aria3"]}">',
         '<defs><pattern id="bbh" width="16" height="16" patternUnits="userSpaceOnUse" x="62" y="70">'
         '<rect x="5.6" y="5.6" width="4.8" height="4.8" rx="1" fill="#a8a294"/></pattern></defs>']
    o += [board_svg(1, L_), board_svg(2, L_)]
    o += [chip_svg(cid) for cid in CHIP]
    o.append(ledmod_ab_svg(L_))
    o.append(power_module_svg(L_))
    order = {"Rails": 0, "Power": 0, "Tie-offs": 0, "LED module": 0, "LEDs": 3, "Signals": 1, "Modules": 2}
    tags = []
    for w in sorted(wires, key=lambda w: order[w["group"]]):
        if w["kind"] == "LED":
            o.append(single_led_svg(w))
            continue
        d, pts = wire_path(w)
        col = net_color(w["net"])
        width = 4.6 if w["kind"] == "M-F" else 4
        o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".28" stroke-width="{width + 2.2}" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}" stroke-linecap="round" '
                 f'stroke-linejoin="round"/>')
        for e in (w["a"], w["b"]):
            x, y = end_xy(e)
            if e[0] == "M":
                o.append(f'<rect x="{x - 3.5}" y="{y - 12}" width="7" height="13" rx="1" fill="#1f1f1f"/>')
            else:
                o.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#3d3d3d" stroke="#fff" stroke-width=".8"/>')
        if pts and w["group"] == "Signals":
            tags.append((ortho(pts), net_label(w["net"]), col))
    o.append(ledmod_c_svg(L_))
    for x, y, lab, col in place_tags(tags, blocked_boxes(1)):
        o.append(tag(x, y, lab, col, 8.5))
    for m in MODULES:
        o.append(module_svg(m, L_))
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------------------------------
# 2. Chip connections: the same wires without the board.  The chips are drawn
# taller (S2_EXPAND) so that pin names fit, the column a wire plugs into becomes a
# short stub, and power, tie-offs and LEDs become symbols.
# ----------------------------------------------------------------------------

S2_EXPAND = 46


def s2y(y):
    shift = 0
    for b in (1, 2):
        e, f = BOARD_Y[b] + ROW_Y["e"], BOARD_Y[b] + ROW_Y["f"]
        if y <= e:
            return y + shift
        if y < f:
            return e + shift + (y - e) * (f - e + S2_EXPAND) / (f - e)
        shift += S2_EXPAND
    return y + shift


S2_H = s2y(MOD_Y) + 40


def led_symbol(x, y, up=False, color="var(--fg)"):
    """LED from (x, y) to GND, pointing down (or up)."""
    s = -1 if up else 1
    return (f'<path class="s-led" d="M{x - 6},{y + 4 * s} h12 l-6,{10 * s} z M{x - 6},{y + 14 * s} h12 M{x},{y} v{4 * s} '
            f'M{x},{y + 14 * s} v{6 * s}"/>'
            f'<path class="s-line" d="M{x + 7},{y + 7 * s} l6,{-5 * s} M{x + 8},{y + 12 * s} l6,{-5 * s}"/>'
            + gnd_symbol(x, y + 20 * s, up=up))


def chip_box_s2(cid, L_):
    _, typ, board, c = CHIP[cid]
    n = NPINS[typ] // 2
    off = BOARD_Y[board]
    x0, x1 = bx(c) - 10, bx(c + n - 1) + 10
    y0, y1 = s2y(off + ROW_Y["e"] + 4), s2y(off + ROW_Y["f"] - 4)
    o = [f'<rect class="s-chip" x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="4"/>'
         f'<path class="s-notch" d="M{x0},{(y0 + y1) / 2 - 8} A8,8 0 0 1 {x0},{(y0 + y1) / 2 + 8}"/>']
    for p in range(1, NPINS[typ] + 1):
        b, col, half = pin_pos(cid, p)
        x = bx(col)
        nm = PINS[typ][p]
        faded = NETLIST[cid][p] in (None, "NC")
        op = ' opacity=".45"' if faded else ""
        if half == "T":
            o.append(f'<line class="s-line" x1="{x}" y1="{s2y(off + ROW_Y["e"])}" x2="{x}" y2="{y0}"/>'
                     f'<text class="s-pn" x="{x + 2}" y="{y0 - 2}">{p}</text>'
                     f'<text class="s-pin2" x="{x}" y="{y0 + 10}" text-anchor="middle"{op}>{lab_svg(nm)}</text>')
        else:
            o.append(f'<line class="s-line" x1="{x}" y1="{y1}" x2="{x}" y2="{s2y(off + ROW_Y["f"])}"/>'
                     f'<text class="s-pn" x="{x + 2}" y="{y1 + 9}">{p}</text>'
                     f'<text class="s-pin2" x="{x}" y="{y1 - 4}" text-anchor="middle"{op}>{lab_svg(nm)}</text>')
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if typ == "4013":
        r1, r2 = L_["ff_short"][FF_ROLE[(cid, 1)]], L_["ff_short"][FF_ROLE[(cid, 2)]]
        o.append(f'<text class="s-chipname" x="{cx}" y="{cy - 7}" text-anchor="middle">{CHIP_LABEL[cid]}</text>'
                 f'<text class="s-sub2" x="{cx}" y="{cy + 5}" text-anchor="middle">{escape(r2)}</text>'
                 f'<text class="s-sub2" x="{cx}" y="{cy + 15}" text-anchor="middle">{escape(r1)}</text>')
    else:
        o.append(f'<text class="s-chipname" x="{cx}" y="{cy - 2}" text-anchor="middle">{CHIP_LABEL[cid]}</text>'
                 f'<text class="s-sub2" x="{cx}" y="{cy + 11}" text-anchor="middle">{escape(L_["chip_roles"][cid])}</text>')
    return "".join(o)


def svg_chips(lang="en"):
    L_ = T[lang]
    wires = [w for w in all_wires() if w["group"] != "Temporary"]
    o = [f'<svg class="arb" viewBox="0 0 {SVG_W} {S2_H:g}" role="img" aria-label="{L_["aria2"]}">']
    for b in (1, 2):
        off = BOARD_Y[b]
        o.append(f'<text class="s-cap" x="1086" y="{s2y(off + 166) + 4}" text-anchor="end" '
                 f'transform="rotate(-90 1086 {s2y(off + 166)})" dx="44">{escape(L_["board"][b].upper())}</text>')
    o += [chip_box_s2(cid, L_) for cid in CHIP]
    # strips: the column a wire plugs into, drawn as a stub from the pin to the farthest wire end
    ends = defaultdict(list)    # strip -> [(y, net)]
    for w in wires:
        if w["group"] in ("Signals",) or (w["group"] == "Modules" and w["a"][2] == "OUT"):
            for e in (w["a"], w["b"]):
                if e[0] == "H":
                    ends[strip(e[1], e[2], e[3])].append((y_of(e[1], e[3]), w["net"]))
    pin_at = {}
    for cid, typ, board, c in CHIPS:
        for p in range(1, NPINS[typ] + 1):
            b, col, half = pin_pos(cid, p)
            pin_at[("S", b, half, col)] = (cid, p)
    paths = []
    segs = defaultdict(list)
    for s_, lst in ends.items():
        _, b, half, col = s_
        ys = [y for y, _ in lst]
        net = lst[0][1]
        if s_ in pin_at:
            ys.append(BOARD_Y[b] + (ROW_Y["e"] if half == "T" else ROW_Y["f"]))
        if b == LA_BOARD and half == "B" and LA_G <= col <= LA_G + 8:
            ys.append(BOARD_Y[b] + ROW_Y["g"])
        pts = [(bx(col), s2y(min(ys))), (bx(col), s2y(max(ys)))]
        if pts[0] != pts[1]:
            paths.append((net, pts))
            segs[net].extend(ortho(pts))
    tags = []
    for w in wires:
        if w["group"] == "Signals":
            pts = [(bx(x), s2y(y)) for x, y in w["pts"]]
            paths.append((w["net"], pts))
            segs[w["net"]].extend(ortho(pts))
            tags.append((ortho(pts), net_label(w["net"]), net_color(w["net"])))
        elif w["group"] == "Modules" and w["a"][2] == "OUT":
            (ax, ay), (hx, hy) = end_xy(w["a"]), end_xy(w["b"])
            ay2, hy2 = s2y(MOD_Y), s2y(hy)
            d = f"M{ax},{ay2} C{ax},{ay2 - 40} {hx},{hy2 + 50} {hx},{hy2}" if ax != hx else f"M{ax},{ay2} L{hx},{hy2}"
            o.append(f'<path class="s-w" style="stroke:{net_color(w["net"])}" d="{d}"/>')
    for net, pts in paths:
        o.append(f'<path class="s-w" style="stroke:{net_color(net)}" d="{rpath(pts, 4)}"/>')
    from arbiter import junctions
    for net, ss in segs.items():
        for x, y in junctions(ss):
            o.append(f'<circle cx="{x:g}" cy="{y:g}" r="3.2" style="fill:{net_color(net)}"/>')
    # power and tie-offs as symbols at the pin
    for w in wires:
        if w["group"] in ("Power", "Tie-offs") and "pin" in w:
            cid, p = w["pin"]
            b, col, half = pin_pos(cid, p)
            x = bx(col)
            off = BOARD_Y[b]
            if half == "T":
                y = s2y(off + ROW_Y["c"])
                o.append(f'<line class="s-line" x1="{x}" y1="{y}" x2="{x}" y2="{s2y(off + ROW_Y["e"])}"/>')
                o.append(vdd_symbol(x, y) if w["net"] == "+5V" else gnd_symbol(x, y, up=True))
            else:
                y = s2y(off + ROW_Y["h"])
                o.append(f'<line class="s-line" x1="{x}" y1="{s2y(off + ROW_Y["f"])}" x2="{x}" y2="{y}"/>')
                o.append(gnd_symbol(x, y))
    # LEDs
    off = BOARD_Y[LA_BOARD]
    for k, net in LA_USE.items():
        x = bx(LA_G + k)
        y = s2y(off + ROW_Y["g"])
        o.append(led_symbol(x, y - 34) + f'<line class="s-w" style="stroke:{net_color(net)}" x1="{x}" y1="{y - 34}" '
                 f'x2="{x}" y2="{y}"/><text class="s-pin2" x="{x}" y="{y - 40}" text-anchor="middle">{k}</text>')
    lx0, lx1 = bx(LA_G + 1) - 12, bx(LA_G + 8) + 12
    o.append(f'<rect x="{lx0}" y="{s2y(off + ROW_Y["g"]) - 48}" width="{lx1 - lx0}" height="44" rx="5" '
             f'fill="none" stroke="var(--muted)" stroke-dasharray="4 3"/>'
             f'<text class="s-sub" x="{lx0}" y="{s2y(off + ROW_Y["g"]) - 52}">{escape(L_["ledmod_ab_s2"])}</text>')
    lb, lg = lc_g()
    off = BOARD_Y[lb]
    for k in range(1, 9):
        x = bx(lg + k)
        y = s2y(off + ROW_Y["e"])
        o.append(f'<line class="s-line" x1="{x}" y1="{y}" x2="{x}" y2="{y - 30}"/>' + led_symbol(x, y - 30, up=True))
    lx0, lx1 = bx(lg + 1) - 12, bx(lg + 8) + 12
    o.append(f'<rect x="{lx0}" y="{s2y(off + ROW_Y["e"]) - 64}" width="{lx1 - lx0}" height="40" rx="5" fill="none" '
             f'stroke="var(--muted)" stroke-dasharray="4 3"/>'
             f'<text class="s-sub" x="{lx1 + 6}" y="{s2y(off + ROW_Y["e"]) - 50}">{escape(L_["ledmod_c_s2"])}</text>')
    for net, cid, p, colour in SINGLE_LEDS:
        b, col, half = pin_pos(cid, p)
        x = bx(col)
        y = s2y(BOARD_Y[b] + ROW_Y["f"])
        o.append(f'<line class="s-line" x1="{x}" y1="{y}" x2="{x}" y2="{y + 30}"/>' + led_symbol(x, y + 30))
    # modules
    for m in MODULES:
        mid, net, kind, cc, target = m
        x = bx(cc)
        y = s2y(MOD_Y)
        o.append(f'<rect class="s-mod" x="{x - 30}" y="{y}" width="60" height="26" rx="5"/>'
                 f'<text class="s-modt" x="{x}" y="{y + 11}" text-anchor="middle">{escape(L_["mod_box"][mid])}</text>'
                 f'<text class="s-modt" x="{x}" y="{y + 21}" text-anchor="middle" style="fill:{net_color(net)}">'
                 f'{lab_svg(net_label(net))}</text>')
    for x, y, lab, col in place_tags(tags, blocked_boxes(2)):
        o.append(tag(x, y, lab, col))
    o.append(vdd_symbol(20, 30) + '<text class="s-sub" x="30" y="27">+5V</text>'
             + gnd_symbol(20, 54) + '<text class="s-sub" x="32" y="66">GND</text>')
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------------------------------
# 1. Logic diagram
# ----------------------------------------------------------------------------

def svg_logic(lang="en"):
    L_ = T[lang]
    G = L_["logic"]
    C = net_color
    o = [f'<svg class="arb" viewBox="0 0 1000 620" role="img" aria-label="{L_["aria1"]}">']
    sync = G["sync"].split(" | ")
    o.append('<rect class="s-cloud3" x="120" y="92" width="128" height="472" rx="14"/>'
             + "".join(f'<text class="s-cap" x="130" y="{110 + 13 * k}">{t}</text>' for k, t in enumerate(sync))
             + '<rect class="s-cloud" x="268" y="30" width="586" height="378" rx="16"/>'
             f'<text class="s-cap" x="280" y="48">{G["data"]}</text>'
             '<rect class="s-cloud2" x="492" y="420" width="300" height="150" rx="14"/>'
             f'<text class="s-cap" x="504" y="438">{G["ctrl"]}</text>')

    def wire(net, pts, bus=None, name=None):
        o.append(f'<path class="s-w" style="stroke:{C(net)}" stroke-width="{4 if bus else 2.2}" d="{rpath(pts, 6)}"/>')
        (x0, y0), (x1, y1) = pts[0], pts[1]
        if bus:
            mx, my = x0 + (x1 - x0) * 0.3, y0 + (y1 - y0) * 0.3
            o.append(f'<path class="s-line" d="M{mx - 4},{my + 6} l8,-12"/>'
                     f'<text class="s-pin2" x="{mx + 5}" y="{my + 12}">{bus}</text>')
        if name:
            mx, my = x0 + (x1 - x0) * 0.42, y0 + (y1 - y0) * 0.42
            o.append(f'<text class="s-io" x="{mx}" y="{my - 6}" text-anchor="middle" style="fill:{C(net)}">'
                     f'{lab_svg(name)}</text>')

    def dot(x, y, net):
        o.append(f'<circle cx="{x}" cy="{y}" r="3.6" style="fill:{C(net)}"/>')

    def text(x, y, t, anchor="start", cls="s-io", net=None):
        st = f' style="fill:{C(net)}"' if net else ""
        o.append(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"{st}>{t}</text>')

    def box(x, y, w, h, title, sub, pins):
        o.append(f'<rect class="s-gate" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/>'
                 f'<text class="s-tag" x="{x + w / 2}" y="{y + h / 2 - 2}" text-anchor="middle">{title}</text>'
                 f'<text class="s-sub" x="{x + w / 2}" y="{y + h / 2 + 13}" text-anchor="middle">{sub}</text>')
        for side, d, nm in pins:
            if side == "l":
                o.append(f'<text class="s-pin" x="{x + 5}" y="{y + d + 4}">{lab_svg(nm)}</text>')
            elif side == "r":
                o.append(f'<text class="s-pin" x="{x + w - 5}" y="{y + d + 4}" text-anchor="end">{lab_svg(nm)}</text>')
            else:
                o.append(f'<text class="s-pin" x="{x + d}" y="{y + h - 6}" text-anchor="middle">{lab_svg(nm)}</text>')

    def ff(x, y, title, qb=False):
        o.append(f'<rect class="s-gate" x="{x}" y="{y}" width="64" height="60" rx="3"/>'
                 f'<text class="s-pin" x="{x + 5}" y="{y + 22}">D</text>'
                 f'<path class="s-line" d="M{x},{y + 36} l9,6 l-9,6"/>'
                 f'<text class="s-pin" x="{x + 32}" y="{y + 56}" text-anchor="middle">R</text>'
                 f'<text class="s-pin" x="{x + 59}" y="{y + 22}" text-anchor="end">Q</text>'
                 + (f'<text class="s-pin" x="{x + 59}" y="{y + 46}" text-anchor="end">'
                    f'<tspan text-decoration="overline">Q</tspan></text>' if qb else "")
                 + f'<text class="s-sub" x="{x + 32}" y="{y - 6}" text-anchor="middle">{title}</text>'
                 f'<path class="s-w" style="stroke:{C("clk")}" d="M{x - 16},{y + 42} H{x}"/>'
                 f'<text class="s-sub" x="{x - 18}" y="{y + 46}" text-anchor="end">clk</text>'
                 f'<path class="s-w" style="stroke:{C("rst")}" d="M{x + 32},{y + 60} V{y + 72}"/>'
                 f'<text class="s-sub" x="{x + 32}" y="{y + 84}" text-anchor="middle">rst</text>')

    def led_up(x, y, colour=None):
        """LED from the point (x, y) up to GND."""
        o.append(f'<path class="s-led" d="M{x},{y} v-6 M{x - 6},{y - 6} h12 l-6,-10 z M{x - 6},{y - 16} h12 '
                 f'M{x},{y - 16} v-6"/><path class="s-line" d="M{x + 7},{y - 12} l6,-5 M{x + 8},{y - 7} l6,-5"/>'
                 + gnd_symbol(x, y - 22, up=True))
        if colour:
            o.append(f'<circle cx="{x}" cy="{y - 10}" r="2.4" fill="{colour}"/>')

    # inputs and the flip-flops that put them in step with the clock
    text(20, 92, G["data_in"])
    wire("d0", [(20, 100), (300, 100)], bus="3")
    wire("d0", [(272, 100), (272, 290), (300, 290)])
    dot(272, 100, "d0")
    for y, key, net in ((170, "push_a", "pushA"), (360, "push_b", "pushB"), (510, "pop_c", "popC")):
        text(20, y - 8, G[key])
        wire(net, [(20, y), (150, y)])
    ff(150, 152, "4013 #1 · FF1")
    ff(150, 342, "4013 #2 · FF1")
    ff(150, 492, "4013 #1 · FF2", qb=True)
    wire("sA", [(214, 170), (300, 170)], name="sA")
    wire("sB", [(214, 360), (300, 360)], name="sB")
    wire("pC", [(214, 534), (246, 534), (246, 600), (880, 600), (880, 320), (790, 320), (790, 304)])
    text(420, 594, lab_svg("~pC"), "middle", "s-io", "pC")
    # datapath
    pins_ab = [("l", 26, "D"), ("l", 96, "SI"), ("r", 26, "Q"), ("r", 76, "DOR"), ("r", 104, "SO"), ("b", 34, "MR")]
    box(300, 74, 130, 130, "FIFO A", "40105", pins_ab)
    box(300, 264, 130, 130, "FIFO B", "40105", pins_ab)
    box(536, 74, 92, 300, "4008", G["adder"], [("l", 26, "A"), ("l", 216, "B"), ("r", 126, "S")])
    o.append(f'<text class="s-sub" x="582" y="250" text-anchor="middle">{G["sum_note"]}</text>')
    box(690, 170, 120, 134, "FIFO C", "40105", [("l", 30, "D"), ("l", 100, "SI"), ("r", 16, "Q"), ("r", 48, "DOR"),
                                                ("r", 80, "DIR"), ("b", 100, "SO"), ("b", 34, "MR")])
    for x, y in ((334, 204), (334, 394), (724, 304)):
        o.append(f'<path class="s-w" style="stroke:{C("rst")}" d="M{x},{y} V{y + 10}"/>'
                 f'<text class="s-sub" x="{x}" y="{y + 22}" text-anchor="middle">rst</text>')
    wire("a0", [(430, 100), (536, 100)], bus="3", name="a")
    wire("b0", [(430, 290), (536, 290)], bus="3", name="b")
    wire("s0", [(628, 200), (690, 200)], bus="4", name="s")
    # LEDs for A and B
    for x, y, net in ((448, 100, "a0"), (448, 150, "rA"), (448, 290, "b0"), (448, 340, "rB")):
        dot(x, y, net)
        led_up(x, y)
    text(470, 64, G["led_ab"], "start", "s-sub")
    wire("rA", [(430, 150), (478, 150), (478, 468), (536, 468)], name=None)
    wire("rB", [(430, 340), (490, 340), (490, 482), (536, 482)])
    text(484, 214, "rA", "start", "s-io", "rA")
    text(496, 404, "rB", "start", "s-io", "rB")
    # C outputs
    wire("c0", [(810, 186), (900, 186), (900, 170)], bus="4", name="c")
    led_up(900, 170)
    wire("vC", [(810, 218), (930, 218), (930, 170)], name="vC")
    led_up(930, 170)
    text(915, 128, G["led_c"], "middle", "s-sub")
    wire("fC", [(810, 250), (850, 250), (850, 586), (512, 586), (512, 496), (536, 496)])
    wire("fC", [(850, 250), (960, 250), (960, 236)])
    dot(850, 250, "fC")
    led_up(960, 236, "#ffd43b")
    text(960, 196, G["room"], "middle", "s-sub")
    text(866, 244, "fC", "start", "s-io", "fC")
    # flow control
    s_, op = gate_shape("AND", 566, 482, w=56, h=64)
    o.append(s_ + f'<text class="s-sub" x="574" y="532" text-anchor="middle">4082 · {G["and4"]}</text>')
    wire("go", [op, (660, 482)], name="go")
    ff(660, 460, "4013 #2 · FF2", qb=True)
    wire("t", [(724, 478), (770, 478), (770, 420), (460, 420), (460, 178), (430, 178)])
    wire("t", [(460, 368), (430, 368)])
    wire("t", [(668, 420), (668, 270), (690, 270)])
    for x, y in ((460, 368), (668, 420)):
        dot(x, y, "t")
    text(612, 414, "t", "middle", "s-io", "t")
    wire("tb", [(724, 506), (746, 506), (746, 560), (504, 560), (504, 510), (536, 510)])
    text(626, 554, lab_svg("~t"), "middle", "s-io", "tb")
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------------------------------
# HTML fragments
# ----------------------------------------------------------------------------

def hole_name(e):
    return f"{e[2]}{e[3]}"


def end_desc(e, lang="en"):
    L_ = T[lang]
    if e[0] == "M":
        return f"{L_['mod_desc'][e[1]]}, {e[2].replace('-', '−')}"
    if e[0] == "R":
        _, b, rail, col = e
        return L_["rail"].format(board=L_["board"][b], side=L_["top"] if rail[0] == "T" else L_["bottom"],
                                 sign="+" if rail[1] == "+" else "−", col=col).capitalize()
    _, b, col, row = e
    half = "T" if row in "abcde" else "B"
    where = L_["board"][b]
    for cid, typ, board, c in CHIPS:
        for p in range(1, NPINS[typ] + 1):
            if pin_pos(cid, p) == (b, col, half):
                return (f"<b>{col}{row}</b> <span class='muted'>{where} · "
                        f"{L_['chip_pin'].format(chip=CHIP_LABEL[cid], p=p)}, {lab_html(PINS[typ][p])}</span>")
    if b == LA_BOARD and half == "B" and LA_G <= col <= LA_G + 8:
        k = col - LA_G
        lab = L_["la_gnd"] if k == 0 else L_["la_pin"].format(k=k)
        return f"<b>{col}{row}</b> <span class='muted'>{where} · {lab}</span>"
    lb, lg = lc_g()
    if b == lb and col == lg and half == "T":
        return f"<b>{col}{row}</b> <span class='muted'>{where} · {L_['lc_gnd']}</span>"
    for m in MODULES:
        board, mcol = (pin_pos(*m[4])[:2] if m[4] else POPC_HOLE)
        if (board, mcol) == (b, col) and half == "B" and not m[4]:
            mm = L_.get("mod_gen", L_["mod_desc"])[m[0]]
            return (f"<b>{col}{row}</b> <span class='muted'>{where} · "
                    f"{L_['jumper_in'].format(m=mm, h=f'{col}j')}</span>")
    return f"<b>{col}{row}</b> <span class='muted'>{where}</span>"


def wiring_table(lang="en"):
    L_ = T[lang]
    wires = all_wires()
    rows = []
    for st in (1, 2):
        ws_st = [w for w in wires if w["stage"] == st]
        n_st = sum(1 for w in ws_st if w["kind"] in ("M-M", "M-F"))
        rows.append(f'<tr class="stage"><td colspan="5"><b>{L_["stage"][st]}</b> <span class="muted">· '
                    f'{L_["wires"](n_st)}</span></td></tr>')
        for g in GROUP_ORDER:
            ws = [w for w in ws_st if w["group"] == g]
            if not ws:
                continue
            rows.append(f'<tr class="grp"><td colspan="5"><b>{L_["groups"][g]}</b></td></tr>')
            for w in ws:
                net = w["net"]
                col = net_color(net)
                done = L_["done"].format(i=w["id"])
                a, b = end_desc(w["a"], lang), end_desc(w["b"], lang)
                if w["kind"] == "LED":
                    b = (f'{L_["led_colour"][w["colour"]]} LED · ' if lang == "en" else
                         f'{L_["led_colour"][w["colour"]]} светодиод · ') + escape(L_["led_single"][net])
                    a = L_["led_long"].format(h=f"<b>{hole_name(w['a'])}</b>", board=L_["board"][w["a"][1]])
                if w["group"] == "Temporary":
                    b += f' <span class="tag warn">{L_["temp_note"]}</span>'
                rows.append(f'<tr data-stage="{st}"><td><input type="checkbox" class="wchk" data-w="{w["id"]}" '
                            f'aria-label="{done}"></td><td class=n>{w["id"]}</td>'
                            f'<td><span class="sw" style="background:{col}"></span>{lab_html(net_label(net))}</td>'
                            f'<td>{a}</td><td>{b}</td></tr>')
    h = L_["th_wires"]
    return (f'<div class="tbl"><table class="wires"><tr><th></th><th class=n>{h[0]}</th><th>{h[1]}</th>'
            f'<th>{h[2]}</th><th>{h[3]}</th></tr>' + "".join(rows) + "</table></div>")


def legend(lang="en"):
    L_ = T[lang]
    items = [n for n in NETS if n in L_["meaning"]]
    return '<div class="legend">' + "".join(
        f'<span><span class="sw" style="background:{net_color(n)}"></span><b>{lab_html(net_label(n))}</b> '
        f'{escape(L_["meaning"][n])}</span>' for n in items if n not in ("c1", "c2", "c3")) + (
        f'<span><span class="sw" style="background:{VDD_C}"></span><b>+5V</b></span>'
        f'<span><span class="sw" style="background:{GND_C}"></span><b>GND</b></span></div>')


def pin_table(lang="en"):
    L_ = T[lang]
    rows = []
    for cid, typ, board, c in CHIPS:
        if typ == "4013":
            role = "<br>".join(escape(L_["ff_roles"][FF_ROLE[(cid, f)]]) for f in (1, 2))
        else:
            role = escape(L_["chip_roles"][cid])
        parts = []
        vdd, gnd = SUPPLY[typ]
        for p in range(1, NPINS[typ] + 1):
            net = NETLIST[cid][p]
            if p in (vdd, gnd) or net == "NC":
                continue
            nm = lab_html(PINS[typ][p])
            if net is None:
                parts.append(f'<span class="muted">{p} {nm} {L_["unused"]}</span>')
            elif net == "GND":
                parts.append(f"{p} {nm} = GND")
            else:
                parts.append(f'{p} {nm} = <b style="color:{net_color(net)}">{lab_html(net_label(net))}</b>')
        rows.append(f"<tr><td><b>{CHIP_LABEL[cid]}</b><div class='small muted'>{L_['board'][board]}</div></td>"
                    f"<td>{role}</td><td class='small'>{', '.join(parts)}</td></tr>")
    h = L_["th_pins"]
    return (f'<div class="tbl"><table><tr><th>{h[0]}</th><th>{h[1]}</th><th>{h[2]}</th></tr>'
            + "".join(rows) + "</table></div>")


TICKS = {
    "en": dict(th=("Clock tick", "A", "B", "go", "t", "C", "What happens"),
               rows=["Hold d1 and d0 (3) and press push A", "Hold d1 (2) and press push B", "Next tick",
                     "Next tick", "Next tick"],
               why=["3 goes into A. B is empty, so go = 0.",
                    "2 goes into B. Now A has data, B has data, C has room and t = 0: go = 1.",
                    "t rises: SI of C rises and C takes the sum 3 + 2 = 5. A and B still hold 3 and 2.",
                    "t falls: SO of A and B fall and both drop their word. go was 0, because t was 1.",
                    "Nothing to do: A and B are empty."],
               empty="empty"),
    "ru": dict(th=("Такт", "A", "B", "go", "t", "C", "Что происходит"),
               rows=["Держите d1 и d0 (3), нажмите «записать в A»", "Держите d1 (2), нажмите «записать в B»",
                     "Следующий такт", "Следующий такт", "Следующий такт"],
               why=["3 записывается в A. B пуста, поэтому go = 0.",
                    "2 записывается в B. Теперь в A и B есть данные, в C есть место и t = 0: go = 1.",
                    "t растёт: SI очереди C растёт, и C забирает сумму 3 + 2 = 5. В A и B всё ещё 3 и 2.",
                    "t падает: SO очередей A и B падают, и обе отдают своё слово. go было 0, потому что t было 1.",
                    "Делать нечего: A и B пусты."],
               empty="пусто"),
}


def ticks_table(ticks, lang="en"):
    t = TICKS[lang]

    def q(ws):
        return " ".join(str(x) for x in ws) if ws else f'<span class="muted">{t["empty"]}</span>'

    body = []
    for k, (r, what, why) in enumerate(zip(ticks, t["rows"], t["why"]), 1):
        body.append(f"<tr><td>{k}. {escape(what)}</td><td class=n>{q(r['A'])}</td><td class=n>{q(r['B'])}</td>"
                    f"<td class=n>{'<b>1</b>' if r['go'] else 0}</td><td class=n>{'<b>1</b>' if r['t'] else 0}</td>"
                    f"<td class=n>{q(r['C'])}</td><td class='small muted'>{escape(why)}</td></tr>")
    h = t["th"]
    return (f'<div class="tbl"><table><tr><th>{h[0]}</th><th class=n>{h[1]}</th><th class=n>{h[2]}</th>'
            f'<th class=n>{h[3]}</th><th class=n>{h[4]}</th><th class=n>{h[5]}</th><th>{h[6]}</th></tr>'
            + "".join(body) + "</table></div>")


CSS = """
.s-sub2{fill:var(--muted);font-size:8.5px}
.s-cloud3{fill:var(--accent-bg);stroke:#5c7cfa;stroke-width:1.2;stroke-dasharray:6 5;opacity:.85}
table.wires tr.stage td{background:var(--accent-bg);color:var(--fg);font-size:15px;padding:8px 10px}
"""


def script(lang="en"):
    from arbiter import SCRIPT
    return SCRIPT.replace("lssk-arbiter-wires", "lssk-fifo-wires").replace("COUNT_TEXT", T[lang]["count"])


def place_words():
    """Columns and holes for the text of the build steps."""
    out = {}
    for cid, typ, board, c in CHIPS:
        b, lo, hi = chip_span(cid)
        out[f"cols_{cid}"] = f"{lo}–{hi}"
        out[f"p1_{cid}"] = f"{lo}f"
    out["la_cols"] = f"{LA_G}–{LA_G + 8}"
    out["la_g"] = str(LA_G)
    lb, lg = lc_g()
    out["lc_cols"] = f"{lg}–{lg + 8}"
    out["lc_g"] = str(lg)
    for net, cid, p, colour in SINGLE_LEDS:
        b, col, half = pin_pos(cid, p)
        out[f"led_{colour}"] = f"{col}j"
    for w in all_wires():
        if w["group"] == "Modules" and w["a"][2] == "OUT":
            out[f"mod_{w['a'][1]}"] = hole_name(w["b"])
    for (b0, r0, c0), (b1, r1, c1) in RAIL_JUMPERS:
        out.setdefault("rail_cols", [])
        out["rail_cols"].append(str(c0))
    out["rail_cols"] = ", ".join(out["rail_cols"])
    return out
