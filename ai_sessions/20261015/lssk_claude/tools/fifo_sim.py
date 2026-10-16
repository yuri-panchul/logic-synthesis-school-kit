"""Event-driven simulation of the FIFO adder (exercise P3) at the pin level.

The chips are behavioural models with propagation delays, so the simulation
shows races and glitches: a clock-gated pulse that feeds back through the
FIFO status flags, a button that bounces while the clock is high, a sum that
is captured before the 4008 has settled.

CD40105B / CD74HC40105 model, from the TI datasheets (SCHS096, SCHS222C):
  * a word is loaded by a low-to-high transition on SI while DIR is high; SI
    must go low before the next word is accepted.  If SI rises while the FIFO
    is full, the word is entered when a location becomes free and SI is
    still high ("if during unloading SI is HIGH ... data is entered").
  * DIR goes low after a load until the word has moved to the second location.
  * a word is removed by a high-to-low transition on SO while DOR is high;
    DOR goes low while the next word moves to the output.  Commands to an
    empty FIFO are ignored.
  * MR clears the control markers: DIR high, DOR low.
"""

import heapq
from collections import defaultdict

NS = 1
US = 1000
MS = 1000 * US


class Sim:
    def __init__(self):
        self.t = 0
        self.q = []
        self.seq = 0
        self.val = defaultdict(int)
        self.changed = defaultdict(lambda: -10 ** 12)
        self.watch = defaultdict(list)
        self.log = []
        self.problems = []

    def at(self, t, fn):
        heapq.heappush(self.q, (t, self.seq, fn))
        self.seq += 1

    def set(self, node, v):
        if node is None or self.val[node] == v:
            return
        self.val[node] = v
        self.changed[node] = self.t
        for cb in list(self.watch[node]):
            cb(node)

    def drive(self, node, v, delay):
        self.at(self.t + delay, lambda: self.set(node, v))

    def on(self, nodes, cb):
        for n in nodes:
            if n is not None and n not in ("VDD", "GND"):
                self.watch[n].append(cb)

    def v(self, node):
        if node == "VDD":
            return 1
        if node == "GND" or node is None:
            return 0
        return self.val[node]

    def run_until(self, t_end):
        while self.q and self.q[0][0] <= t_end:
            t, _, fn = heapq.heappop(self.q)
            self.t = t
            fn()
        self.t = t_end


class Gate:
    def __init__(self, sim, ins, out, fn, delay):
        self.sim, self.ins, self.out, self.fn, self.delay = sim, ins, out, fn, delay
        sim.on(ins, self.eval)
        sim.at(0, lambda: self.eval(None))

    def eval(self, _):
        self.sim.drive(self.out, self.fn([self.sim.v(n) for n in self.ins]), self.delay)


class DFF:
    """One flip-flop of a CD4013: rising-edge D, asynchronous active-high R and S."""
    SETUP, HOLD = 40, 5

    def __init__(self, sim, name, d, clk, r, s, q, qb, delay):
        self.sim, self.name = sim, name
        self.d, self.clk, self.r, self.s, self.q, self.qb, self.delay = d, clk, r, s, q, qb, delay
        self.state = 0
        self.last_clk = 0
        self.last_edge = -10 ** 12
        sim.on([clk, r, s], self.eval)
        sim.on([d], self.d_changed)
        sim.at(0, self.out)

    def out(self):
        self.sim.drive(self.q, self.state, self.delay)
        self.sim.drive(self.qb, 1 - self.state, self.delay)

    def d_changed(self, _):
        if 0 <= self.sim.t - self.last_edge < self.HOLD:
            self.sim.problems.append(f"{self.name}: D changed {self.sim.t - self.last_edge} ns after the clock edge")

    def eval(self, _):
        sim = self.sim
        clk = sim.v(self.clk)
        if sim.v(self.r):
            self.state = 0
        elif sim.v(self.s):
            self.state = 1
        elif clk and not self.last_clk:
            if sim.t - sim.changed[self.d] < self.SETUP and sim.changed[self.d] > 0:
                sim.problems.append(f"{self.name}: D changed {sim.t - sim.changed[self.d]} ns before the clock edge")
            self.state = sim.v(self.d)
            self.last_edge = sim.t
        self.last_clk = clk
        self.out()


class Adder4008:
    def __init__(self, sim, a, b, cin, s, cout, delay):
        self.sim, self.a, self.b, self.cin, self.s, self.cout, self.delay = sim, a, b, cin, s, cout, delay
        sim.on(a + b + [cin], self.eval)
        sim.at(0, lambda: self.eval(None))

    def eval(self, _):
        v = self.sim.v
        x = sum(v(n) << i for i, n in enumerate(self.a))
        y = sum(v(n) << i for i, n in enumerate(self.b))
        z = x + y + v(self.cin)
        for i, n in enumerate(self.s):
            self.sim.drive(n, (z >> i) & 1, self.delay)
        self.sim.drive(self.cout, (z >> 4) & 1, self.delay)


class Fifo40105:
    T_FLAG = 40   # SI to DIR, SO to DOR
    T_STEP = 25   # one location of the ripple-through
    HOLD = 25     # data hold time after SI

    def __init__(self, sim, name, pins):
        """pins: dict with SI, SO, MR, OE, D (4 nodes), DIR, DOR, Q (4 nodes)."""
        self.sim, self.name, self.p = sim, name, pins
        self.slot = [None] * 17
        self.armed_in = True
        self.armed_out = False
        self.moving = False
        self.loads = []
        self.load_time = -10 ** 12
        sim.on([pins["SI"]], self.si)
        sim.on([pins["SO"]], self.so)
        sim.on([pins["MR"]], self.mr)
        sim.on(pins["D"], self.d_changed)
        sim.at(0, self.flags)

    def mr_on(self):
        return self.sim.v(self.p["MR"])

    def mr(self, _):
        if self.mr_on():
            self.slot = [None] * 17
            self.armed_in = True
            self.armed_out = bool(self.sim.v(self.p["SO"]))
        else:
            self.try_load()
        self.flags()

    def si(self, _):
        if self.sim.v(self.p["SI"]):
            self.try_load()
        else:
            self.armed_in = True

    def so(self, _):
        if self.sim.v(self.p["SO"]):
            self.armed_out = True
        else:
            self.try_unload()

    def d_changed(self, _):
        if 0 <= self.sim.t - self.load_time < self.HOLD:
            self.sim.problems.append(f"FIFO {self.name}: data changed {self.sim.t - self.load_time} ns after the load")

    def try_load(self):
        sim = self.sim
        if self.mr_on() or not sim.v(self.p["SI"]) or not self.armed_in or self.slot[1] is not None:
            return
        word = sum(sim.v(n) << i for i, n in enumerate(self.p["D"]))
        self.slot[1] = word
        self.armed_in = False
        self.load_time = sim.t
        self.loads.append((sim.t, word))
        self.flags()
        self.ripple()

    def try_unload(self):
        if self.mr_on() or self.sim.v(self.p["SO"]) or not self.armed_out:
            return
        self.armed_out = False
        if self.slot[16] is not None:
            self.slot[16] = None
            self.flags()
            self.ripple()

    def ripple(self):
        if not self.moving:
            self.moving = True
            self.sim.at(self.sim.t + self.T_STEP, self.step)

    def step(self):
        self.moving = False
        old = self.slot[:]
        moved = False
        for k in range(1, 16):
            if old[k] is not None and old[k + 1] is None:
                self.slot[k + 1], self.slot[k] = old[k], None
                moved = True
        if moved:
            self.flags()
            self.ripple()
            self.try_load()

    def flags(self):
        sim, p = self.sim, self.p
        mr = self.mr_on()
        sim.drive(p["DIR"], 1 if mr or self.slot[1] is None else 0, self.T_FLAG)
        sim.drive(p["DOR"], 0 if mr or self.slot[16] is None else 1, self.T_FLAG)
        if self.slot[16] is not None and not mr:
            for i, n in enumerate(p["Q"]):
                sim.drive(n, (self.slot[16] >> i) & 1, self.T_FLAG)

    def count(self):
        return sum(1 for x in self.slot[1:] if x is not None)

    def words(self):
        return [x for x in reversed(self.slot[1:]) if x is not None]


# ----------------------------------------------------------------------------
# Building the circuit from a pin map
# ----------------------------------------------------------------------------

def build(sim, chips, pinmap, delays):
    """chips: {id: type}; pinmap: {(chip, pin): node}.  Returns {id: model}."""
    m = {}

    def n(chip, pin):
        return pinmap.get((chip, pin))

    for cid, typ in chips.items():
        if typ == "40105":
            p = dict(OE=n(cid, 1), DIR=n(cid, 2), SI=n(cid, 3), D=[n(cid, k) for k in (4, 5, 6, 7)],
                     MR=n(cid, 9), Q=[n(cid, k) for k in (13, 12, 11, 10)], DOR=n(cid, 14), SO=n(cid, 15))
            m[cid] = Fifo40105(sim, cid, p)
        elif typ == "4008":
            m[cid] = Adder4008(sim, [n(cid, k) for k in (7, 5, 3, 1)], [n(cid, k) for k in (6, 4, 2, 15)],
                               n(cid, 9), [n(cid, k) for k in (10, 11, 12, 13)], n(cid, 14), delays["4008"])
        elif typ == "4013":
            m[cid] = [DFF(sim, f"{cid}/FF1", n(cid, 5), n(cid, 3), n(cid, 4), n(cid, 6), n(cid, 1), n(cid, 2),
                          delays["4013"]),
                      DFF(sim, f"{cid}/FF2", n(cid, 9), n(cid, 11), n(cid, 10), n(cid, 8), n(cid, 13), n(cid, 12),
                          delays["4013"])]
        elif typ == "4082":
            def and4(xs):
                return int(all(xs))
            m[cid] = [Gate(sim, [n(cid, k) for k in (2, 3, 4, 5)], n(cid, 1), and4, delays["gate"]),
                      Gate(sim, [n(cid, k) for k in (9, 10, 11, 12)], n(cid, 13), and4, delays["gate"])]
        elif typ == "4081":
            def and2(xs):
                return xs[0] & xs[1]
            m[cid] = [Gate(sim, [n(cid, a), n(cid, b)], n(cid, o), and2, delays["gate"])
                      for a, b, o in ((1, 2, 3), (5, 6, 4), (8, 9, 10), (12, 13, 11))]
        else:
            raise ValueError(typ)
    return m


DELAYS = [  # typical, fast and slow corners (ns)
    dict(gate=125, **{"4013": 150, "4008": 400}),
    dict(gate=60, **{"4013": 60, "4008": 150}),
    dict(gate=250, **{"4013": 300, "4008": 800}),
]


class Bench:
    """Buttons with contact bounce, a 555 clock and the LEDs, around a built circuit."""

    def __init__(self, chips, pinmap, inputs, delays, period=500 * MS, bounce=True):
        self.sim = Sim()
        self.inputs = inputs          # {"clk": node, "rst": node, "pushA": node, ...}
        self.period = period
        self.bounce = bounce
        self.m = build(self.sim, chips, pinmap, delays)
        self.t = 0
        self.edges = 0
        self._clock(0)
        self.wait(37.3)  # people do not press buttons in step with the clock

    def _clock(self, v):
        self.sim.set(self.inputs["clk"], v)
        if v:
            self.edges += 1
        self.sim.at(self.sim.t + self.period // 2, lambda: self._clock(1 - v))

    def _press(self, node, v):
        sim = self.sim
        if self.bounce:
            t0 = sim.t
            for k, dt in enumerate((0, 300 * US, 700 * US, 1500 * US, 2600 * US)):
                sim.at(t0 + dt, (lambda x: lambda: sim.set(node, x))(v if k % 2 == 0 else 1 - v))
        else:
            sim.set(node, v)

    def wait(self, ms):
        self.t += int(ms * MS)
        self.sim.run_until(self.t)

    def press(self, name, hold_ms=700, after_ms=600, data=None):
        """Hold the data buttons, press and release one button, release the data buttons."""
        for i, b in enumerate(data or []):
            if b:
                self._press(self.inputs[f"d{i}"], 1)
        self.wait(150)
        self._press(self.inputs[name], 1)
        self.wait(hold_ms)
        self._press(self.inputs[name], 0)
        self.wait(150)
        for i, b in enumerate(data or []):
            if b:
                self._press(self.inputs[f"d{i}"], 0)
        self.wait(after_ms)

    def v(self, node):
        return self.sim.v(node)
