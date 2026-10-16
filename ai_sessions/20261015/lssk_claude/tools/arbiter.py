"""Round-robin arbiter with 2 requests and 2 grants (exercise P4).

One netlist drives the three diagrams of arbiter_build.html (logic, chip
connections, breadboard), the wiring checklist and a pin-level check that
simulates the breadboard wiring against the reference behaviour.

State L = 1 means that the last grant went to requester 1.
    g0 = r0 & ~(r1 & ~L)     N1 = NAND(r1, ~L) -> x    A1 = AND(x, r0) -> g0
    g1 = r1 & ~(r0 &  L)     N2 = NAND(r0,  L) -> y    A2 = AND(r1, y) -> g1
    L' = g1 | (L & ~r0)      A3 = AND(L, y) -> h       O1 = OR(g1, h)  -> D
L & y = L & (~r0 | ~L) = L & ~r0, so A3 reuses y instead of an inverter.
"""

from collections import defaultdict
from html import escape

# ----------------------------------------------------------------------------
# Netlist
# ----------------------------------------------------------------------------

QUAD = {"A": (1, 2, 3), "B": (5, 6, 4), "C": (8, 9, 10), "D": (12, 13, 11)}  # in, in, out
FF_PINS = {1: dict(Q=1, QB=2, CLK=3, R=4, D=5, S=6), 2: dict(Q=13, QB=12, CLK=11, R=10, D=9, S=8)}
PIN_4013 = {1: "Q1", 2: "~Q1", 3: "CLK1", 4: "R1", 5: "D1", 6: "S1", 7: "VSS",
            8: "S2", 9: "D2", 10: "R2", 11: "CLK2", 12: "~Q2", 13: "Q2", 14: "VDD"}
FUNC = {"4011": lambda a, b: 1 - (a & b), "4081": lambda a, b: a & b, "4071": lambda a, b: a | b}
KIND = {"4011": "NAND", "4081": "AND", "4071": "OR", "4013": "D flip-flop"}

CHIPS = [("4013", 12), ("4011", 22), ("4081", 32), ("4071", 42)]  # type, column of pin 1
COL = dict(CHIPS)

# tag, chip, gate, inputs in pin order, output
GATES = [
    ("N2", "4011", "A", ("L", "r0"), "y"),
    ("N1", "4011", "B", ("Lb", "r1"), "x"),
    ("A1", "4081", "A", ("x", "r0"), "g0"),
    ("A2", "4081", "B", ("r1", "y"), "g1"),
    ("A3", "4081", "C", ("L", "y"), "h"),
    ("O1", "4071", "A", ("g1", "h"), "D"),
]
FF_USE = dict(D="D", CLK="clk", R="rst", S="GND", Q="L", QB="Lb")  # 4013, flip-flop 1

NETS = {  # name, label ("~" = overline), colour, meaning
    "r0": ("r0", "#e8590c", "request 0"),
    "r1": ("r1", "#7950f2", "request 1"),
    "L": ("L", "#2f9e44", "last grant went to 1"),
    "Lb": ("~L", "#0c8599", "NOT L"),
    "x": ("x", "#d6336c", "NOT (r1 AND NOT L)"),
    "y": ("y", "#d08700", "NOT (r0 AND L)"),
    "g0": ("g0", "#1c7ed6", "grant 0, LED 1"),
    "g1": ("g1", "#ae3ec9", "grant 1, LED 2"),
    "h": ("h", "#a5734d", "L AND y = L AND NOT r0"),
    "D": ("D", "#5c940d", "next L"),
    "clk": ("clk", "#868e96", "clock"),
    "rst": ("rst", "#c2410c", "reset"),
}
VDD_C, GND_C = "#e03131", "#343a40"

# Words on the diagrams and in the tables, per language.
T = {
    "en": dict(
        meaning={k: v[2] for k, v in NETS.items()},
        aria1="Logic diagram of the round-robin arbiter: two NAND gates, three AND gates, one OR gate and a D flip-flop",
        aria2="Connections between the 4013, 4011, 4081 and 4071 chips, pin by pin",
        aria3="Breadboard layout of the round-robin arbiter with every wire",
        comb="COMBINATIONAL LOGIC", state="STATE", in0="r0 · request 0", in1="r1 · request 1",
        gate="gate", ff1="flip-flop 1",
        outs=[["grant 0 → LED 1"], ["grant 1 → LED 2"], ["last → LED 4"]],
        feedback="feedback: the state goes back into the gates",
        led="LED", ledmod="8-LED module", ledmod_bb="8-LED MODULE", power="POWER MODULE · 5V", cable="9V USB-DC",
        mod_bb={"clk": ["CLOCK 555 · ~1 Hz"], "rst": ["RESET"], "r0": ["REQUEST 0"], "r1": ["REQUEST 1"]},
        mod_box={"clk": "CLOCK 555", "rst": "RESET", "r0": "REQUEST 0", "r1": "REQUEST 1"},
        mod_desc={"clk": "clock 555 module", "rst": "reset module", "r0": "request 0 module", "r1": "request 1 module"},
        jumper_in="the {m} jumper is in {h}",
        pin="pin", chip_pin="{chip} pin {p}", gate_in="gate {g} input", gate_out="gate {g} output",
        rail="{side} {sign} rail, column {col}", top="top", bottom="bottom",
        led_pin="LED module {p}", led_n="LED {i}",
        groups={"Power": "Power for the chips (red to +, black to −)",
                "Tie-offs": "Unused inputs: CMOS inputs must not float",
                "Signals": "Signal wires", "LED module": "LED module ground",
                "Modules": "Button and clock modules (male-female jumpers)"},
        wires=lambda n: f"{n} wire{'s' if n != 1 else ''}",
        th_wires=("#", "Net", "From", "To"), done="wire {i} done",
        kind={"4011": "NAND", "4081": "AND", "4071": "OR"},
        AND="AND", OR="OR", NOT="NOT",
        th_pins=("Gate", "Chip", "Inputs", "Output"), chip_gate="{chip} {kind}, gate {g}",
        ff_row=("4013 D flip-flop 1", "pin 5 D = D, pin 3 CLK = clk, pin 4 R = rst, pin 6 S = GND",
                "pin 1 Q = <b>L</b>, pin 2 <span class='ol'>Q</span> = <b><span class='ol'>L</span></b>"),
        tt=dict(next="next L", none="nobody asks: L stays", only0="only requester 0: grant 0",
                only1="only requester 1: grant 1", both1="both: grant to 1, it is its turn",
                both0="both: grant to 0, it is its turn"),
        count="' + n + ' of ' + boxes.length + ' wires done",
    ),
    "ru": dict(
        meaning=dict(r0="запрос 0", r1="запрос 1", L="последний грант получил блок 1", Lb="НЕ L",
                     x="НЕ (r1 И НЕ L)", y="НЕ (r0 И L)", g0="грант 0, светодиод 1", g1="грант 1, светодиод 2",
                     h="L И y = L И НЕ r0", D="следующее L", clk="тактовый сигнал", rst="сброс"),
        aria1="Логическая схема round-robin арбитра: два элемента И-НЕ, три И, один ИЛИ и D-триггер",
        aria2="Соединения между микросхемами 4013, 4011, 4081 и 4071, ножка за ножкой",
        aria3="Монтажная схема round-robin арбитра на макетной плате со всеми проводами",
        comb="КОМБИНАЦИОННАЯ ЛОГИКА", state="СОСТОЯНИЕ", in0="r0 · запрос 0", in1="r1 · запрос 1",
        gate="элемент", ff1="триггер 1",
        outs=[["грант 0", "светодиод 1"], ["грант 1", "светодиод 2"], ["последний", "светодиод 4"]],
        feedback="обратная связь: состояние возвращается на входы элементов",
        led="СД", ledmod="линейка светодиодов", ledmod_bb="ЛИНЕЙКА 8 СВЕТОДИОДОВ", power="БЛОК ПИТАНИЯ · 5V",
        cable="USB-DC 9V",
        mod_bb={"clk": ["ГЕНЕРАТОР 555", "~1 Гц"], "rst": ["СБРОС"], "r0": ["ЗАПРОС 0"], "r1": ["ЗАПРОС 1"]},
        mod_box={"clk": "ГЕНЕРАТОР", "rst": "СБРОС", "r0": "ЗАПРОС 0", "r1": "ЗАПРОС 1"},
        mod_desc={"clk": "генератор 555", "rst": "кнопка сброса", "r0": "кнопка запроса 0", "r1": "кнопка запроса 1"},
        mod_gen={"clk": "генератора 555", "rst": "кнопки сброса", "r0": "кнопки запроса 0", "r1": "кнопки запроса 1"},
        jumper_in="провод от {m} — в {h}",
        pin="ножка", chip_pin="{chip}, ножка {p}", gate_in="вход элемента {g}", gate_out="выход элемента {g}",
        rail="{side} шина {sign}, столбик {col}", top="верхняя", bottom="нижняя",
        led_pin="линейка, {p}", led_n="светодиод {i}",
        groups={"Power": "Питание микросхем (красные к +, чёрные к −)",
                "Tie-offs": "Неиспользуемые входы: входы КМОП нельзя оставлять висящими",
                "Signals": "Сигнальные провода", "LED module": "Земля линейки светодиодов",
                "Modules": "Кнопки и генератор (перемычки папа-мама)"},
        wires=lambda n: f"{n} {ru_plural(n, 'провод', 'провода', 'проводов')}",
        th_wires=("#", "Сигнал", "Откуда", "Куда"), done="провод {i} готов",
        kind={"4011": "И-НЕ", "4081": "И", "4071": "ИЛИ"},
        AND="И", OR="ИЛИ", NOT="НЕ",
        th_pins=("Элемент", "Микросхема", "Входы", "Выход"), chip_gate="{chip} {kind}, элемент {g}",
        ff_row=("4013, D-триггер 1", "ножка 5 D = D, ножка 3 CLK = clk, ножка 4 R = rst, ножка 6 S = GND",
                "ножка 1 Q = <b>L</b>, ножка 2 <span class='ol'>Q</span> = <b><span class='ol'>L</span></b>"),
        tt=dict(next="следующее L", none="никто не просит: L не меняется", only0="только запрос 0: грант 0",
                only1="только запрос 1: грант 1", both1="оба: грант 1, его очередь",
                both0="оба: грант 0, его очередь"),
        count="готово ' + n + ' из ' + boxes.length + ' проводов",
    ),
}


def ru_plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many

LED_FIRST = 53  # LED module header in row g: GND at column 53, LED 1-8 at columns 54-61
LED_USE = {1: "g0", 2: "g1", 4: "L"}
MODULES = [  # id, label, net, centre column, rail columns for + and -
    ("clk", "CLOCK 555 · ~1 Hz", "clk", 14, 13, 15),
    ("rst", "RESET", "rst", 19, 18, 20),
    ("r0", "REQUEST 0", "r0", 23, 22, 24),
    ("r1", "REQUEST 1", "r1", 27, 26, 29),
]

# Signal wires: net, end a, end b, route (lanes and columns between the ends).
SIGNALS = [
    ("L", "12g", "22g", ["B1"]),
    ("Lb", "13h", "26h", ["B2"]),
    ("r0", "23i", "33i", ["B3"]),
    ("y", "24j", "37j", ["B4"]),
    ("x", "25g", "32g", ["B1"]),
    ("r1", "27h", "36h", ["B2"]),
    ("g1", "35g", "42g", ["B1"]),
    ("D", "44j", "16j", ["B5"]),
    ("y", "37h", "37d", ["B2", 39, "T4"]),
    ("L", "12i", "38d", ["B3", 20, "T3"]),
    ("h", "36c", "43h", ["T2", 40, "B2"]),
    ("rst", "19i", "15i", ["B4"]),
    ("g0", "34i", "54i", ["B3"]),
    ("g1", "42j", "55j", ["B4"]),
    ("L", "38b", "57h", ["T1", 50, "B2"]),
]


def pin_pos(chip, pin):
    """Column and half ('T' rows a-e, 'B' rows f-j) of a chip pin, notch on the left."""
    c = COL[chip]
    return (c + pin - 1, "B") if pin <= 7 else (c + 14 - pin, "T")


def pin_at():
    return {pin_pos(chip, p): (chip, p) for chip, _ in CHIPS for p in range(1, 15)}


def pin_name(chip, p, lang="en"):
    if chip == "4013":
        return PIN_4013[p]
    if p == 14:
        return "VDD"
    if p == 7:
        return "VSS"
    for g, pins in QUAD.items():
        if p in pins:
            return T[lang]["gate_out" if p == pins[2] else "gate_in"].format(g=g)


def used_inputs():
    """{(chip, pin): net} for every chip input that carries a signal."""
    u = {}
    for tag, chip, g, ins, out in GATES:
        for p, n in zip(QUAD[g][:2], ins):
            u[(chip, p)] = n
    for k, n in FF_USE.items():
        if k not in ("Q", "QB") and n != "GND":
            u[("4013", FF_PINS[1][k])] = n
    return u


def tie_wires():
    """Power wires and tie-offs for every unused input: nearest rail for gates, GND for flip-flop inputs."""
    used = used_inputs()
    power, ties = [], []
    for chip, c in CHIPS:
        power.append(("+5V", f"{c}a", f"T+{c}", f"{chip} pin 14 (VDD)"))
        power.append(("GND", f"{c + 6}j", f"B-{c + 6}", f"{chip} pin 7 (VSS)"))
    for chip, c in CHIPS:
        if chip == "4013":
            ins = [FF_PINS[1]["S"]] + [FF_PINS[2][k] for k in ("CLK", "R", "D", "S")]
        else:
            ins = [p for g in "ABCD" for p in QUAD[g][:2]]
        for p in sorted(ins, key=lambda p: pin_pos(chip, p)):
            if (chip, p) in used:
                continue
            col, half = pin_pos(chip, p)
            if chip == "4013":
                rail = "T-" if half == "T" else "B-"
            else:
                rail = "T+" if half == "T" else "B-"
            hole = f"{col}{'a' if half == 'T' else 'j'}"
            ties.append(("+5V" if rail == "T+" else "GND", hole, f"{rail}{col}",
                         f"{chip} pin {p} ({pin_name(chip, p)}), unused"))
    return power, ties


def all_wires():
    """Every wire: dict(id, group, net, a, b, route, kind, note)."""
    power, ties = tie_wires()
    w = []
    for net, a, b, note in power:
        w.append(dict(group="Power", net=net, a=a, b=b, route=[], kind="M-M", note=note))
    for net, a, b, note in ties:
        w.append(dict(group="Tie-offs", net=net, a=a, b=b, route=[], kind="M-M", note=note))
    for net, a, b, route in SIGNALS:
        w.append(dict(group="Signals", net=net, a=a, b=b, route=route, kind="M-M", note=""))
    w.append(dict(group="LED module", net="GND", a=f"{LED_FIRST}j", b=f"B-{LED_FIRST}", route=[], kind="M-M",
                  note="LED module GND pin"))
    for mid, label, net, cc, cp, cm in MODULES:
        w.append(dict(group="Modules", net="+5V", a=f"M:{mid}:+", b=f"B+{cp}", route=[], kind="M-F", note=label))
        w.append(dict(group="Modules", net=net, a=f"M:{mid}:OUT", b=f"{cc}j", route=[], kind="M-F", note=label))
        w.append(dict(group="Modules", net="GND", a=f"M:{mid}:-", b=f"B-{cm}", route=[], kind="M-F", note=label))
    for i, x in enumerate(w, 1):
        x["id"] = i
    return w


def parse_end(s):
    """'12g' -> ('hole', 12, 'g'); 'T+12' -> ('rail', 'T+', 12); 'M:r0:OUT' -> ('mod', 'r0', 'OUT')."""
    if s.startswith("M:"):
        _, m, p = s.split(":")
        return ("mod", m, p)
    if s[0] in "TB" and s[1] in "+-":
        return ("rail", s[:2], int(s[2:]))
    return ("hole", int(s[:-1]), s[-1])


def node_of(end):
    e = parse_end(end)
    if e[0] == "hole":
        return ("T" if e[2] in "abcde" else "B", e[1])
    if e[0] == "rail":
        return ("R", {"T+": "+5V", "B+": "+5V", "T-": "GND", "B-": "GND"}[e[1]])
    return ("M", e[1], e[2])


# ----------------------------------------------------------------------------
# Pin-level check
# ----------------------------------------------------------------------------

def check():
    """Check the breadboard wiring and simulate it. Returns a summary; raises AssertionError on a fault."""
    wires = all_wires()
    pins = pin_at()
    # every hole holds one wire end, and none sits on a chip or LED pin
    seen = {}
    for w in wires:
        for end in (w["a"], w["b"]):
            e = parse_end(end)
            key = e if e[0] != "mod" else None
            if key is None:
                continue
            assert key not in seen, f"hole {end} used twice (wires {seen.get(key)} and {w['id']})"
            seen[key] = w["id"]
            if e[0] == "hole":
                half = "T" if e[2] in "abcde" else "B"
                assert e[2] not in "ef" or (e[1], half) not in pins, f"{end} is a chip pin"
                assert not (e[2] == "g" and LED_FIRST <= e[1] <= LED_FIRST + 8), f"{end} is an LED pin"
    # lanes: horizontal runs of different wires must not overlap
    runs = defaultdict(list)
    for w in wires:
        if not w["route"]:
            continue
        cols = [parse_end(w["a"])[1]] + [t for t in w["route"] if isinstance(t, int)] + [parse_end(w["b"])[1]]
        lanes = [t for t in w["route"] if isinstance(t, str)]
        for k, lane in enumerate(lanes):
            lo, hi = sorted((cols[k], cols[k + 1]))
            for lo2, hi2, wid in runs[lane]:
                assert hi < lo2 or hi2 < lo, f"lane {lane}: wires {wid} and {w['id']} overlap"
            runs[lane].append((lo, hi, w["id"]))
    # connectivity
    parent = {}

    def find(n):
        parent.setdefault(n, n)
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def union(a, b):
        parent[find(a)] = find(b)

    for w in wires:
        union(node_of(w["a"]), node_of(w["b"]))
    pnode = {(chip, p): find((half, col)) for (col, half), (chip, p) in pins.items()}
    led = {i: find(("B", LED_FIRST + i)) for i in range(0, 9)}
    vdd, gnd = find(("R", "+5V")), find(("R", "GND"))
    assert vdd != gnd, "+5V shorted to GND"
    for mid, *_ in MODULES:
        assert find(("M", mid, "+")) == vdd and find(("M", mid, "-")) == gnd, f"module {mid} power"
    assert led[0] == gnd, "LED module GND"
    # drivers
    drivers = defaultdict(list)
    drivers[vdd].append("+5V")
    drivers[gnd].append("GND")
    for mid, label, net, *_ in MODULES:
        drivers[find(("M", mid, "OUT"))].append("in:" + net)
    for chip, _ in CHIPS:
        assert pnode[(chip, 14)] == vdd and pnode[(chip, 7)] == gnd, f"{chip} power pins"
        if chip == "4013":
            for f in (1, 2):
                drivers[pnode[(chip, FF_PINS[f]["Q"])]].append(f"ff{f}:Q")
                drivers[pnode[(chip, FF_PINS[f]["QB"])]].append(f"ff{f}:QB")
        else:
            for g, (i1, i2, o) in QUAD.items():
                drivers[pnode[(chip, o)]].append(f"{chip}:{g}")
    for n, d in drivers.items():
        assert len(d) == 1, f"net driven by {d}"
    # every chip input and LED input is driven
    inputs = [(chip, p) for chip, _ in CHIPS for p in range(1, 15)
              if p not in (7, 14) and not (chip == "4013" and p in (1, 2, 12, 13))
              and not (chip != "4013" and any(p == QUAD[g][2] for g in QUAD))]
    for ip in inputs:
        assert drivers.get(pnode[ip]), f"floating input {ip}"
    # name the nets by their drivers and compare with the intended netlist
    name = {}
    for n, (d,) in drivers.items():
        if d in ("+5V", "GND"):
            name[n] = d
        elif d.startswith("in:"):
            name[n] = d[3:]
        elif d.startswith("ff1"):
            name[n] = FF_USE["Q" if d.endswith(":Q") else "QB"]
        elif d.startswith("ff2"):
            name[n] = "ff2"
        else:
            chip, g = d.split(":")
            gate = [x for x in GATES if x[1] == chip and x[2] == g]
            name[n] = gate[0][4] if gate else f"{chip}{g}"
    for (chip, p), net in used_inputs().items():
        assert name.get(pnode[(chip, p)]) == net, f"{chip} pin {p}: expected {net}, got {name.get(pnode[(chip, p)])}"
    assert name[pnode[("4013", FF_PINS[1]["S"])]] == "GND"
    for k in ("CLK", "R", "D", "S"):
        assert name[pnode[("4013", FF_PINS[2][k])]] == "GND", "unused flip-flop inputs go to GND"
    for i, net in LED_USE.items():
        assert name.get(led[i]) == net, f"LED {i}"
    # simulate
    state = {1: 0, 2: 0}

    def evaluate(inp):
        val = {vdd: 1, gnd: 0}
        for mid, label, net, *_ in MODULES:
            val[find(("M", mid, "OUT"))] = inp[net]
        for f in (1, 2):
            val[pnode[("4013", FF_PINS[f]["Q"])]] = state[f]
            val[pnode[("4013", FF_PINS[f]["QB"])]] = 1 - state[f]
        for _ in range(10):
            for chip, _c in CHIPS:
                if chip == "4013":
                    continue
                for g, (i1, i2, o) in QUAD.items():
                    a, b = val.get(pnode[(chip, i1)]), val.get(pnode[(chip, i2)])
                    if a is not None and b is not None:
                        val[pnode[(chip, o)]] = FUNC[chip](a, b)
        return val

    def tick(inp):
        val = evaluate(inp)
        for f in (1, 2):
            p = FF_PINS[f]
            if val[pnode[("4013", p["R"])]]:
                state[f] = 0
            elif val[pnode[("4013", p["S"])]]:
                state[f] = 1
            else:
                state[f] = val[pnode[("4013", p["D"])]]

    rows = []
    for L in (0, 1):
        for r0 in (0, 1):
            for r1 in (0, 1):
                state[1] = L
                v = evaluate(dict(r0=r0, r1=r1, rst=0, clk=0))
                g0, g1, d = v[led[1]], v[led[2]], v[pnode[("4013", FF_PINS[1]["D"])]]
                eg0 = r0 & (1 - r1 | L)
                eg1 = r1 & (1 - r0 | 1 - L)
                ed = 1 if eg1 else 0 if eg0 else L
                assert (g0, g1, d) == (eg0, eg1, ed), f"r0={r0} r1={r1} L={L}"
                assert v[led[4]] == L
                rows.append((r0, r1, L, g0, g1, d))
    state[1] = 1
    tick(dict(r0=0, r1=0, rst=1, clk=0))
    assert state[1] == 0, "reset"
    seq = []
    for _ in range(6):
        v = evaluate(dict(r0=1, r1=1, rst=0, clk=0))
        seq.append((v[led[1]], v[led[2]]))
        tick(dict(r0=1, r1=1, rst=0, clk=0))
    assert seq == [(0, 1), (1, 0)] * 3, seq
    mm = sum(1 for w in wires if w["kind"] == "M-M")
    mf = sum(1 for w in wires if w["kind"] == "M-F")
    groups = defaultdict(int)
    for w in wires:
        groups[w["group"]] += 1
    return dict(rows=rows, mm=mm, mf=mf, groups=dict(groups), wires=wires)


# ----------------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------------

def rpath(pts, r=5.0):
    """Polyline through axis-aligned points with rounded corners."""
    q = [pts[0]]
    for p in pts[1:]:
        if p != q[-1]:
            q.append(p)
    pts = q
    if len(pts) < 3:
        return "M" + " L".join(f"{x:g},{y:g}" for x, y in pts)
    d = [f"M{pts[0][0]:g},{pts[0][1]:g}"]
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1 = abs(x1 - x0) + abs(y1 - y0)
        l2 = abs(x2 - x1) + abs(y2 - y1)
        rr = min(r, l1 / 2, l2 / 2)
        ax = x1 - (x1 - x0) / l1 * rr
        ay = y1 - (y1 - y0) / l1 * rr
        bx = x1 + (x2 - x1) / l2 * rr
        by = y1 + (y2 - y1) / l2 * rr
        d.append(f"L{ax:g},{ay:g} Q{x1:g},{y1:g} {bx:g},{by:g}")
    d.append(f"L{pts[-1][0]:g},{pts[-1][1]:g}")
    return " ".join(d)


def lab_html(s):
    """'~Q1' -> Q with an overline, then 1."""
    return f'<span class="ol">{escape(s[1])}</span>{escape(s[2:])}' if s.startswith("~") else escape(s)


def lab_svg(s):
    return f'<tspan text-decoration="overline">{escape(s[1])}</tspan>{escape(s[2:])}' if s.startswith("~") else escape(s)


def text_color(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return "#1d1d1d" if 0.299 * r + 0.587 * g + 0.114 * b > 0.6 else "#ffffff"


def tag(x, y, label, color, size=9):
    w = 6.2 * len(label.lstrip("~")) + 9
    return (f'<rect x="{x - w / 2:g}" y="{y - 7:g}" width="{w:g}" height="14" rx="7" fill="{color}" '
            f'stroke="#ffffff" stroke-width="1.2"/>'
            f'<text x="{x:g}" y="{y + 3.3:g}" text-anchor="middle" font-size="{size}" font-weight="700" '
            f'fill="{text_color(color)}">{lab_svg(label)}</text>')


def gate_shape(kind, x, y, w=56, h=40, cls="s-gate", direction="right", extra=""):
    """Gate symbol. (x, y) is the centre. direction 'right', 'up' or 'down'. Returns (svg, output point)."""
    bubble = kind == "NAND"
    if direction == "right":
        x0, x1, y0, y1 = x - w / 2, x + w / 2 - (6 if bubble else 0), y - h / 2, y + h / 2
        if kind in ("AND", "NAND"):
            rr = h / 2
            d = f"M{x0:g},{y0:g} L{x1 - rr:g},{y0:g} A{rr:g},{rr:g} 0 0 1 {x1 - rr:g},{y1:g} L{x0:g},{y1:g} Z"
        else:
            d = (f"M{x0:g},{y0:g} Q{x0 + (x1 - x0) * .6:g},{y0:g} {x1:g},{y:g} "
                 f"Q{x0 + (x1 - x0) * .6:g},{y1:g} {x0:g},{y1:g} Q{x0 + 10:g},{y:g} {x0:g},{y0:g} Z")
        out = (x1 + (6 if bubble else 0), y)
        bub = f'<circle class="{cls}" cx="{x1 + 3:g}" cy="{y:g}" r="3"/>' if bubble else ""
    else:
        s = -1 if direction == "up" else 1
        yb = y - s * h / 2  # base
        yt = y + s * h / 2 - s * (6 if bubble else 0)
        x0, x1 = x - w / 2, x + w / 2
        if kind in ("AND", "NAND"):
            rr = w / 2
            ys = yt - s * rr
            sweep = 1 if s < 0 else 0
            d = (f"M{x0:g},{yb:g} L{x0:g},{ys:g} A{rr:g},{rr:g} 0 0 {sweep} {x1:g},{ys:g} L{x1:g},{yb:g} Z")
        else:
            d = (f"M{x0:g},{yb:g} Q{x0:g},{yb + (yt - yb) * .6:g} {x:g},{yt:g} "
                 f"Q{x1:g},{yb + (yt - yb) * .6:g} {x1:g},{yb:g} Q{x:g},{yb + s * 6:g} {x0:g},{yb:g} Z")
        out = (x, yt + s * (6 if bubble else 0))
        bub = f'<circle class="{cls}" cx="{x:g}" cy="{yt + s * 3:g}" r="3"/>' if bubble else ""
    return f'<path class="{cls}" d="{d}"{extra}/>{bub}', out


def gnd_symbol(x, y, up=False, cls="s-pow"):
    s = -1 if up else 1
    return (f'<path class="{cls}" d="M{x:g},{y:g} v{6 * s} M{x - 6:g},{y + 6 * s:g} h12 '
            f'M{x - 4:g},{y + 9 * s:g} h8 M{x - 2:g},{y + 12 * s:g} h4"/>')


def vdd_symbol(x, y, cls="s-vdd"):
    return f'<path class="{cls}" d="M{x:g},{y:g} v-7 M{x - 6:g},{y - 7:g} h12"/>'


def junctions(segments):
    """Dots where three or more wire arms of one net meet. segments: list of ((x1,y1),(x2,y2))."""
    pts = set()
    for a, b in segments:
        pts.add(a)
        pts.add(b)
    edges = set()
    for a, b in segments:
        on = [p for p in pts if (p[0] == a[0] == b[0] and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))
              or (p[1] == a[1] == b[1] and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]))]
        on.sort()
        for p, q in zip(on, on[1:]):
            edges.add((p, q))
    deg = defaultdict(int)
    for p, q in edges:
        deg[p] += 1
        deg[q] += 1
    return [p for p, d in deg.items() if d >= 3]


def ortho(pts):
    q = [pts[0]]
    for p in pts[1:]:
        if p != q[-1]:
            q.append(p)
    return list(zip(q, q[1:]))


# ----------------------------------------------------------------------------
# 1. Logic diagram
# ----------------------------------------------------------------------------

def svg_logic(lang="en"):
    L_ = T[lang]
    C = {k: v[1] for k, v in NETS.items()}
    o = [f'<svg class="arb" viewBox="0 0 980 440" role="img" aria-label="{L_["aria1"]}">']
    o.append(f'<rect class="s-cloud" x="236" y="42" width="456" height="318" rx="18"/>'
             f'<text class="s-cap" x="250" y="62">{L_["comb"]}</text>'
             f'<rect class="s-cloud2" x="706" y="210" width="128" height="182" rx="14"/>'
             f'<text class="s-cap" x="718" y="228">{L_["state"]}</text>')
    lines = []

    def wire(net, pts, width=2.2):
        lines.append((net, pts))
        o.append(f'<path class="s-w" style="stroke:{C[net]}" stroke-width="{width}" d="{rpath(pts, 6)}"/>')

    bus = {"r0": 110, "r1": 135, "L": 165, "Lb": 190}
    # gates: tag -> (kind, centre, inputs, output)
    G = {"A1": ("AND", (480, 90)), "N1": ("NAND", (300, 120)), "N2": ("NAND", (300, 240)),
         "A2": ("AND", (480, 200)), "A3": ("AND", (480, 300)), "O1": ("OR", (640, 270))}
    outs = {}
    gates_svg = []
    for tag_, chip, g, ins, out in GATES:
        kind, (x, y) = G[tag_]
        s, op = gate_shape(kind, x, y)
        outs[tag_] = op
        gates_svg.append(s + f'<text class="s-tag" x="{x - 6:g}" y="{y + 4:g}" text-anchor="middle">{tag_}</text>'
                         f'<text class="s-sub" x="{x:g}" y="{y + 34:g}" text-anchor="middle">{chip} · {L_["gate"]} {g}</text>')
    # inputs and buses
    wire("r0", [(20, 40), (110, 40), (110, 230)])
    wire("r1", [(20, 70), (135, 70), (135, 190)])
    o.append(f'<text class="s-io" x="20" y="33">{L_["in0"]}</text><text class="s-io" x="20" y="63">{L_["in1"]}</text>')
    taps = []

    def tap(net, y, x_to):
        wire(net, [(bus[net], y), (x_to, y)])
        taps.append((bus[net], y, net))

    tap("r0", 80, 452)    # A1
    tap("r1", 110, 272)   # N1
    tap("Lb", 130, 272)   # N1
    tap("r1", 190, 452)   # A2
    tap("r0", 230, 272)   # N2
    tap("L", 250, 272)    # N2
    tap("L", 310, 452)    # A3
    xo = outs["N1"]
    wire("x", [xo, (400, xo[1]), (400, 100), (452, 100)])
    yo = outs["N2"]
    wire("y", [yo, (410, yo[1]), (410, 210), (452, 210)])
    wire("y", [(410, yo[1]), (410, 290), (452, 290)])
    taps.append((410, yo[1], "y"))
    g0 = outs["A1"]
    wire("g0", [g0, (880, g0[1])])
    g1 = outs["A2"]
    wire("g1", [g1, (880, g1[1])])
    wire("g1", [(560, g1[1]), (560, 260), (612, 260)])
    taps.append((560, g1[1], "g1"))
    h = outs["A3"]
    wire("h", [h, (575, h[1]), (575, 280), (612, 280)])
    d = outs["O1"]
    wire("D", [d, (720, 270)])
    # flip-flop
    o.append('<rect class="s-gate" x="720" y="240" width="100" height="100" rx="3"/>'
             '<text class="s-pin" x="727" y="274">D</text><text class="s-pin" x="800" y="259">Q</text>'
             '<text class="s-pin" x="800" y="329"><tspan text-decoration="overline">Q</tspan></text>'
             '<text class="s-pin" x="765" y="334">R</text>'
             '<path class="s-line" d="M720,312 L730,320 L720,328"/>'
             '<text class="s-tag" x="770" y="296" text-anchor="middle">FF</text>'
             f'<text class="s-sub" x="770" y="382" text-anchor="middle">4013 · {L_["ff1"]}</text>')
    wire("clk", [(600, 320), (720, 320)])
    o.append('<text class="s-io" x="596" y="324" text-anchor="end">clk</text>')
    wire("rst", [(770, 340), (770, 352)])
    o.append('<text class="s-io" x="770" y="366" text-anchor="middle">rst</text>')
    wire("L", [(820, 255), (880, 255)])
    wire("L", [(866, 255), (866, 415), (165, 415), (165, 250)])
    taps.append((866, 255, "L"))
    wire("Lb", [(820, 325), (848, 325), (848, 400), (190, 400), (190, 130)])
    wire("L", [(165, 250), (165, 310)])
    for x, y, net in taps:
        o.append(f'<circle cx="{x}" cy="{y}" r="3.6" style="fill:{C[net]}"/>')
    o.extend(gates_svg)
    for (y, a), sub in zip(((g0[1], "g0"), (g1[1], "g1"), (255, "L")), L_["outs"]):
        o.append(f'<text class="s-io" x="886" y="{y - 6}">{a}</text>')
        for k, line in enumerate(sub):
            o.append(f'<text class="s-sub" x="886" y="{y + 14 + 13 * k}">{escape(line)}</text>')
    for net, x in (("L", 165), ("Lb", 190)):
        o.append(f'<text class="s-io" x="{x}" y="432" text-anchor="middle" style="fill:{C[net]}">{lab_svg(NETS[net][0])}</text>')
    o.append(f'<text class="s-sub" x="520" y="432" text-anchor="middle">{L_["feedback"]}</text>')
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------------------------------
# 2. Chip connections
# ----------------------------------------------------------------------------

P2 = 22
LED_X2 = {54: 952, 55: 990, 57: 1028}


def x2(col):
    return LED_X2[col] if col in LED_X2 else 70 + (col - 12) * P2


Y2 = dict(T1=36, T2=50, T3=64, T4=80, ttip=100, top=110, mid=160, bot=210, btip=220,
          B1=250, B2=264, B3=278, B4=292, B5=306, mod=336, led=330)


def chip_svg2(chip, c):
    used = {(x[1], x[2]): x for x in GATES}
    o = []
    left, right = x2(c) - 14, x2(c + 6) + 14
    o.append(f'<rect class="s-chip" x="{left}" y="{Y2["top"]}" width="{right - left}" height="100" rx="4"/>'
             f'<path class="s-notch" d="M{left},{Y2["mid"] - 8} A8,8 0 0 1 {left},{Y2["mid"] + 8}"/>')
    for p in range(1, 15):
        col, half = pin_pos(chip, p)
        x = x2(col)
        if half == "T":
            o.append(f'<line class="s-line" x1="{x}" y1="{Y2["ttip"]}" x2="{x}" y2="{Y2["top"]}"/>'
                     f'<text class="s-pn" x="{x + 3}" y="{Y2["top"] - 2}">{p}</text>')
        else:
            o.append(f'<line class="s-line" x1="{x}" y1="{Y2["bot"]}" x2="{x}" y2="{Y2["btip"]}"/>'
                     f'<text class="s-pn" x="{x + 3}" y="{Y2["bot"] + 9}">{p}</text>')
    cx = (x2(c) + x2(c + 6)) / 2
    o.append(f'<text class="s-chipname" x="{cx}" y="{Y2["mid"] + 4}" text-anchor="middle">{chip}</text>')
    if chip == "4013":
        for f, (y0, y1) in ((1, (172, 196)), (2, (124, 148))):
            p = FF_PINS[f]
            cols = {k: pin_pos(chip, v)[0] for k, v in p.items()}
            xs = [x2(v) for v in cols.values()]
            dim = "" if f == 1 else ' opacity=".35"'
            o.append(f'<g{dim}><rect class="s-gate" x="{min(xs) - 9}" y="{y0}" width="{max(xs) - min(xs) + 18}" '
                     f'height="{y1 - y0}" rx="2"/>')
            for k, v in p.items():
                x = x2(cols[k])
                lab = lab_svg({"QB": "~Q", "CLK": "C"}.get(k, k))
                if f == 1:
                    o.append(f'<line class="s-line" x1="{x}" y1="{y1}" x2="{x}" y2="{Y2["bot"]}"/>'
                             f'<text class="s-pin2" x="{x}" y="{y1 - 6}" text-anchor="middle">{lab}</text>')
                else:
                    o.append(f'<line class="s-line" x1="{x}" y1="{Y2["top"]}" x2="{x}" y2="{y0}"/>'
                             f'<text class="s-pin2" x="{x}" y="{y0 + 14}" text-anchor="middle">{lab}</text>')
            o.append("</g>")
        return "".join(o)
    kind = KIND[chip]
    for g, (i1, i2, out) in QUAD.items():
        (c1, half), (c2, _), (co, _) = pin_pos(chip, i1), pin_pos(chip, i2), pin_pos(chip, out)
        gx = (x2(c1) + x2(c2)) / 2
        if half == "B":
            gy, direction, yb, yloop, yedge = 184, "up", 197, 168, Y2["bot"]
        else:
            gy, direction, yb, yloop, yedge = 136, "down", 123, 152, Y2["top"]
        info = used.get((chip, g))
        dim = "" if info else ' opacity=".3"'
        s, op = gate_shape(kind, gx, gy, w=30, h=26, direction=direction)
        o.append(f'<g{dim}>{s}')
        for cc in (c1, c2):
            o.append(f'<line class="s-line" x1="{x2(cc)}" y1="{yedge}" x2="{x2(cc)}" y2="{yb}"/>')
        o.append(f'<path class="s-line" d="{rpath([op, (op[0], yloop), (x2(co), yloop), (x2(co), yedge)], 4)}"/>')
        if info:
            o.append(f'<text class="s-tag2" x="{gx}" y="{gy + (6 if half == "B" else 1)}" text-anchor="middle">{info[0]}</text>')
        o.append("</g>")
    return "".join(o)


def svg_chips(lang="en"):
    L_ = T[lang]
    C = {k: v[1] for k, v in NETS.items()}
    o = [f'<svg class="arb" viewBox="0 0 1060 400" role="img" aria-label="{L_["aria2"]}">']
    for chip, c in CHIPS:
        o.append(chip_svg2(chip, c))
    # power and tie-off symbols
    power, ties = tie_wires()
    for net, hole, rail, note in power + ties:
        e = parse_end(hole)
        x = x2(e[1])
        if e[2] == "a":
            o.append(gnd_symbol(x, Y2["ttip"], up=True) if rail.startswith("T-") else vdd_symbol(x, Y2["ttip"]))
        else:
            o.append(gnd_symbol(x, Y2["btip"]))
    # signal wires
    segs = defaultdict(list)
    paths = []
    tags = []
    pins = pin_at()

    def end_xy(end, lane_y):
        e = parse_end(end)
        col, row = e[1], e[2]
        half = "T" if row in "abcde" else "B"
        if (col, half) in pins:
            return (x2(col), Y2["ttip"] if half == "T" else Y2["btip"])
        if col in LED_X2:
            return (x2(col), Y2["led"])
        return (x2(col), lane_y)

    for net, a, b, route in SIGNALS:
        lanes = [t for t in route if isinstance(t, str)]
        pa = end_xy(a, Y2[lanes[0]])
        pts = [pa]
        x, y = pa
        for t in route:
            if isinstance(t, str):
                y = Y2[t]
            else:
                x = x2(t)
            pts.append((x, y))
        pb = end_xy(b, Y2[lanes[-1]])
        pts += [(pb[0], y), pb]
        paths.append((net, pts))
        segs[net].extend(ortho(pts))
        runs = [(p, q) for p, q in ortho(pts) if p[1] == q[1]]
        p, q = max(runs, key=lambda s: abs(s[1][0] - s[0][0]))
        if abs(q[0] - p[0]) > 60:
            tags.append(((p[0] + q[0]) / 2, p[1], NETS[net][0], C[net]))
    # module wires
    for mid, label, net, cc, cp, cm in MODULES:
        x = x2(cc)
        if (cc, "B") in pins:
            pts = [(x, Y2["mod"]), (x, Y2["btip"])]
        else:
            pts = [(x, Y2["mod"]), (x, Y2["B4"])]
        paths.append((net, pts))
        segs[net].extend(ortho(pts))
        o.append(f'<rect class="s-mod" x="{x - 33}" y="{Y2["mod"]}" width="66" height="26" rx="5"/>'
                 f'<text class="s-modt" x="{x}" y="{Y2["mod"] + 11}" text-anchor="middle">{escape(L_["mod_box"][mid])}</text>'
                 f'<text class="s-modt" x="{x}" y="{Y2["mod"] + 21}" text-anchor="middle" style="fill:{C[net]}">{lab_svg(NETS[net][0])}</text>')
    for net, pts in paths:
        o.append(f'<path class="s-w" style="stroke:{C[net]}" d="{rpath(pts, 4)}"/>')
    for net, ss in segs.items():
        for x, y in junctions(ss):
            o.append(f'<circle cx="{x:g}" cy="{y:g}" r="3.4" style="fill:{C[net]}"/>')
    for x, y, lab, col in tags:
        o.append(tag(x, y, lab, col))
    # LEDs
    for i, net in LED_USE.items():
        x = x2(LED_FIRST + i)
        y = Y2["led"]
        o.append(f'<path class="s-led" d="M{x - 7},{y + 4} h14 l-7,12 z M{x - 7},{y + 16} h14 M{x},{y + 16} v8"/>'
                 f'<path class="s-line" d="M{x + 8},{y + 6} l7,-6 M{x + 10},{y + 12} l7,-6"/>'
                 + gnd_symbol(x, y + 24) +
                 f'<text class="s-modt" x="{x}" y="{y + 52}" text-anchor="middle">{L_["led"]} {i}</text>')
        o.append(f'<line class="s-w" style="stroke:{C[net]}" x1="{x}" y1="{y}" x2="{x}" y2="{y + 4}"/>')
    o.append(f'<text class="s-sub" x="{x2(LED_FIRST + 4) + 4}" y="{Y2["led"] + 66}" text-anchor="end">{L_["ledmod"]}</text>')
    # legend for symbols
    o.append(vdd_symbol(20, 30) + '<text class="s-sub" x="30" y="27">+5V</text>'
             + gnd_symbol(20, 378) + '<text class="s-sub" x="32" y="390">GND</text>')
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------------------------------
# 3. Breadboard
# ----------------------------------------------------------------------------

BB_P = 16
ROW_Y = dict(a=78, b=94, c=110, d=126, e=142, f=190, g=206, h=222, i=238, j=254)
RAIL_Y = {"T-": 30, "T+": 46, "B-": 286, "B+": 302}
LANE_Y = dict(T1=86, T2=102, T3=118, T4=134, B1=198, B2=214, B3=230, B4=246, B5=270)
MOD_Y = 380


def bx(col):
    return 70 + (col - 1) * BB_P


def end_bb(end):
    e = parse_end(end)
    if e[0] == "hole":
        return (bx(e[1]), ROW_Y[e[2]])
    if e[0] == "rail":
        return (bx(e[2]), RAIL_Y[e[1]])
    mod = {m[0]: m for m in MODULES}[e[1]]
    return (bx(mod[3]) + {"+": -16, "OUT": 0, "-": 16}[e[2]], MOD_Y)


def wire_bb(w):
    a, b = end_bb(w["a"]), end_bb(w["b"])
    if w["kind"] == "M-F":
        if a[0] == b[0]:
            return f"M{a[0]:g},{a[1]:g} L{b[0]:g},{b[1]:g}", None
        return f"M{a[0]:g},{a[1]:g} C{a[0]:g},{a[1] - 40:g} {b[0]:g},{b[1] + 40:g} {b[0]:g},{b[1]:g}", None
    pts = [a]
    x, y = a
    for t in w["route"]:
        if isinstance(t, str):
            y = LANE_Y[t]
        else:
            x = bx(t)
        pts.append((x, y))
    pts += [(b[0], y), b]
    return rpath(pts, 5), pts


def svg_breadboard(wires, lang="en"):
    L_ = T[lang]
    C = {k: v[1] for k, v in NETS.items()}
    color = dict(C, **{"+5V": VDD_C, "GND": GND_C})
    o = [f'<svg class="arb bbv" viewBox="0 0 1100 480" role="img" aria-label="{L_["aria3"]}">',
         '<defs><pattern id="bbh" width="16" height="16" patternUnits="userSpaceOnUse" x="62" y="70">'
         '<rect x="5.6" y="5.6" width="4.8" height="4.8" rx="1" fill="#a8a294"/></pattern></defs>',
         '<rect x="44" y="12" width="1046" height="308" rx="9" fill="#f4f1e8" stroke="#d6cfbd" stroke-width="1.5"/>']
    for name, y in RAIL_Y.items():
        tint = "#fbe3e3" if name.endswith("+") else "#e3ebfb"
        line = VDD_C if name.endswith("+") else "#2f6fd0"
        ly = y + (-9 if name.startswith("T") and name.endswith("-") else 9 if name.startswith("B") and name.endswith("+") else 0)
        o.append(f'<rect x="60" y="{y - 7}" width="1020" height="14" rx="3" fill="{tint}"/>')
        if ly != y:
            o.append(f'<line x1="66" x2="1074" y1="{ly}" y2="{ly}" stroke="{line}" stroke-width="1.5"/>')
        o.append(f'<rect x="62" y="{y - 8}" width="1008" height="16" fill="url(#bbh)"/>')
        sym = "+" if name.endswith("+") else "−"
        o.append(f'<text x="1082" y="{y + 4}" font-size="12" font-weight="700" fill="{line}">{sym}</text>')
    o.append('<rect x="62" y="70" width="1008" height="80" fill="url(#bbh)"/>'
             '<rect x="62" y="182" width="1008" height="80" fill="url(#bbh)"/>'
             '<rect x="56" y="158" width="1024" height="16" rx="3" fill="#e7e2d4"/>')
    for col in range(1, 64):
        bold = col % 5 == 0 or col == 1
        o.append(f'<text x="{bx(col)}" y="65" text-anchor="middle" font-size="{8 if bold else 6.5}" '
                 f'fill="{"#5b5547" if bold else "#8d8676"}" font-weight="{700 if bold else 400}">{col}</text>')
    for r, y in ROW_Y.items():
        o.append(f'<text x="54" y="{y + 3}" text-anchor="middle" font-size="9" fill="#8d8676">{r}</text>')
    # chips
    for chip, c in CHIPS:
        x0, x1 = bx(c) - 9, bx(c + 6) + 9
        o.append(f'<rect x="{x0}" y="147" width="{x1 - x0}" height="38" rx="3" fill="#2b2f33"/>'
                 f'<path d="M{x0},160 A6,6 0 0 1 {x0},172" fill="#f4f1e8"/>')
        for i in range(7):
            x = bx(c + i)
            o.append(f'<rect x="{x - 3}" y="{ROW_Y["e"] - 3}" width="6" height="8" rx="1" fill="#c9ced3"/>'
                     f'<rect x="{x - 3}" y="{ROW_Y["f"] - 5}" width="6" height="8" rx="1" fill="#c9ced3"/>')
        o.append(f'<text x="{(x0 + x1) / 2}" y="170" text-anchor="middle" font-size="12" font-weight="700" '
                 f'fill="#ffffff">{chip}</text>'
                 f'<circle cx="{x0 + 7}" cy="180" r="1.8" fill="#9aa0a6"/>')
    # LED module, lying over the board with its header in row g
    lx0, lx1 = bx(LED_FIRST) - 10, bx(LED_FIRST + 8) + 10
    o.append(f'<rect x="{lx0}" y="114" width="{lx1 - lx0}" height="86" rx="5" fill="#1d4f91"/>')
    for i in range(9):
        x = bx(LED_FIRST + i)
        o.append(f'<rect x="{x - 2.5}" y="198" width="5" height="10" fill="#c9ced3"/>'
                 f'<text x="{x}" y="194" text-anchor="middle" font-size="7.5" fill="#dbe7ff">{"G" if i == 0 else i}</text>')
        if i:
            o.append(f'<rect x="{x - 5}" y="128" width="10" height="20" rx="2" fill="#8fd3ff" stroke="#cdeeff" stroke-width="1"/>')
    for i, net in LED_USE.items():
        o.append(f'<text x="{bx(LED_FIRST + i)}" y="166" text-anchor="middle" font-size="9" font-weight="700" '
                 f'fill="#ffffff">{lab_svg(NETS[net][0])}</text>')
    o.append(f'<text x="{(lx0 + lx1) / 2}" y="124" text-anchor="middle" font-size="8.5" fill="#dbe7ff" '
             f'font-weight="600">{L_["ledmod_bb"]}</text>')
    # power module at the left end
    o.append('<rect x="26" y="6" width="112" height="320" rx="7" fill="#2f6fd0" opacity=".96"/>'
             '<rect x="18" y="128" width="30" height="34" rx="3" fill="#222"/>'
             '<rect x="22" y="176" width="24" height="28" rx="2" fill="#adb5bd"/>'
             '<rect x="100" y="56" width="22" height="12" rx="2" fill="#ffd43b"/>'
             '<rect x="100" y="264" width="22" height="12" rx="2" fill="#ffd43b"/>'
             '<text x="111" y="83" text-anchor="middle" font-size="8" font-weight="700" fill="#fff">5V</text>'
             '<text x="111" y="259" text-anchor="middle" font-size="8" font-weight="700" fill="#fff">5V</text>'
             '<text transform="translate(80,166) rotate(-90)" text-anchor="middle" font-size="11" '
             f'font-weight="700" fill="#fff">{L_["power"]}</text>'
             '<path d="M18,145 C2,150 2,190 -4,236" stroke="#555" stroke-width="6" fill="none" stroke-linecap="round"/>'
             f'<text x="4" y="350" font-size="10" fill="#6b6455">{L_["cable"]}</text>')
    # wires: ties and power first, then signals, then modules
    order = {"Power": 0, "Tie-offs": 0, "LED module": 0, "Signals": 1, "Modules": 2}
    tags = []
    for w in sorted(wires, key=lambda w: order[w["group"]]):
        d, pts = wire_bb(w)
        col = color[w["net"]]
        width = 4.6 if w["kind"] == "M-F" else 4
        o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".28" stroke-width="{width + 2.2}" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}" stroke-linecap="round" '
                 f'stroke-linejoin="round"/>')
        for end in (w["a"], w["b"]):
            e = parse_end(end)
            x, y = end_bb(end)
            if e[0] == "mod":
                o.append(f'<rect x="{x - 3.5}" y="{y - 12}" width="7" height="13" rx="1" fill="#1f1f1f"/>')
            else:
                o.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#3d3d3d" stroke="#fff" stroke-width=".8"/>')
        if pts and w["group"] == "Signals":
            runs = [(p, q) for p, q in ortho(pts) if p[1] == q[1]]
            p, q = max(runs, key=lambda s: abs(s[1][0] - s[0][0]))
            if abs(q[0] - p[0]) >= 64:
                tags.append(((p[0] + q[0]) / 2, p[1], NETS[w["net"]][0], col))
    for x, y, lab, col in tags:
        o.append(tag(x, y, lab, col, 8.5))
    # modules
    for mid, label, net, cc, cp, cm in MODULES:
        x = bx(cc)
        body = "#2f6fd0" if mid != "clk" else "#1b5fb8"
        o.append(f'<rect x="{x - 28}" y="{MOD_Y}" width="56" height="44" rx="5" fill="{body}"/>')
        for dx, t in ((-16, "+"), (0, "OUT"), (16, "−")):
            o.append(f'<text x="{x + dx}" y="{MOD_Y + 11}" text-anchor="middle" font-size="7" fill="#fff" '
                     f'font-weight="700">{t}</text>')
        if mid == "clk":
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
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------------------------------
# HTML fragments
# ----------------------------------------------------------------------------

def hole_desc(end, lang="en"):
    L_ = T[lang]
    e = parse_end(end)
    if e[0] == "mod":
        return f"{L_['mod_desc'][e[1]]}, {e[2].replace('-', '−')}"
    if e[0] == "rail":
        return L_["rail"].format(side=L_["top"] if e[1][0] == "T" else L_["bottom"],
                                 sign="+" if e[1][1] == "+" else "−", col=e[2])
    col, row = e[1], e[2]
    half = "T" if row in "abcde" else "B"
    p = pin_at().get((col, half))
    if p:
        return (f"<b>{col}{row}</b> <span class='muted'>({L_['chip_pin'].format(chip=p[0], p=p[1])}, "
                f"{lab_html(pin_name(*p, lang=lang))})</span>")
    mod = [m for m in MODULES if m[3] == col]
    if mod and half == "B" and row != "j":
        m = L_.get("mod_gen", L_["mod_desc"])[mod[0][0]]
        return f"<b>{col}{row}</b> <span class='muted'>({L_['jumper_in'].format(m=m, h=f'{col}j')})</span>"
    if LED_FIRST <= col <= LED_FIRST + 8 and half == "B":
        i = col - LED_FIRST
        return (f"<b>{col}{row}</b> <span class='muted'>"
                f"({L_['led_pin'].format(p='GND' if i == 0 else L_['led_n'].format(i=i))})</span>")
    return f"<b>{col}{row}</b>"


def wiring_table(wires, lang="en"):
    L_ = T[lang]
    groups = ["Power", "Tie-offs", "Signals", "LED module", "Modules"]
    rows = []
    for g in groups:
        ws = [w for w in wires if w["group"] == g]
        rows.append(f'<tr class="grp"><td colspan="5"><b>{L_["groups"][g]}</b> <span class="muted">· '
                    f'{L_["wires"](len(ws))}</span></td></tr>')
        for w in ws:
            net = w["net"]
            col = NETS[net][1] if net in NETS else (VDD_C if net == "+5V" else GND_C)
            label = NETS[net][0] if net in NETS else ("+5V" if net == "+5V" else "GND")
            done = L_["done"].format(i=w["id"])
            rows.append(f'<tr><td><input type="checkbox" class="wchk" data-w="{w["id"]}" aria-label="{done}"></td>'
                        f'<td class=n>{w["id"]}</td>'
                        f'<td><span class="sw" style="background:{col}"></span>{lab_html(label)}</td>'
                        f'<td>{hole_desc(w["a"], lang)}</td><td>{hole_desc(w["b"], lang)}</td></tr>')
    h = L_["th_wires"]
    return (f'<div class="tbl"><table class="wires"><tr><th></th><th class=n>{h[0]}</th><th>{h[1]}</th>'
            f'<th>{h[2]}</th><th>{h[3]}</th></tr>' + "".join(rows) + "</table></div>")


def legend(lang="en"):
    return '<div class="legend">' + "".join(
        f'<span><span class="sw" style="background:{c}"></span><b>{lab_html(lab)}</b> {escape(T[lang]["meaning"][k])}</span>'
        for k, (lab, c, m) in NETS.items()) + (
        f'<span><span class="sw" style="background:{VDD_C}"></span><b>+5V</b></span>'
        f'<span><span class="sw" style="background:{GND_C}"></span><b>GND</b></span></div>')


def pin_table(lang="en"):
    L_ = T[lang]
    AND, OR, NOT, pin = L_["AND"], L_["OR"], L_["NOT"], L_["pin"]
    rows = []
    for tag_, chip, g, ins, out in GATES:
        p1, p2, po = QUAD[g]
        a, b = NETS[ins[0]][0], NETS[ins[1]][0]
        expr = {"NAND": f"{NOT} ({a} {AND} {b})".replace("~L", f"{NOT} L"),
                "AND": f"{a} {AND} {b}", "OR": f"{a} {OR} {b}"}[KIND[chip]]
        rows.append(f"<tr><td><b>{tag_}</b></td><td>{L_['chip_gate'].format(chip=chip, kind=L_['kind'][chip], g=g)}</td>"
                    f"<td>{pin} {p1} = {lab_html(a)}, {pin} {p2} = {lab_html(b)}</td>"
                    f"<td>{pin} {po} = <b>{NETS[out][0]}</b> = {escape(expr)}</td></tr>")
    f = L_["ff_row"]
    rows.append(f"<tr><td><b>FF</b></td><td>{f[0]}</td><td>{f[1]}</td><td>{f[2]}</td></tr>")
    h = L_["th_pins"]
    return (f'<div class="tbl"><table><tr><th>{h[0]}</th><th>{h[1]}</th><th>{h[2]}</th><th>{h[3]}</th></tr>'
            + "".join(rows) + "</table></div>")


def truth_table(rows, lang="en"):
    t = T[lang]["tt"]

    def b(v):
        return f"<b>{v}</b>" if v else "0"
    body = []
    for r0, r1, L, g0, g1, d in sorted(rows, key=lambda r: (r[2], r[0], r[1])):
        what = {(0, 0): t["none"], (1, 0): t["only0"], (0, 1): t["only1"],
                (1, 1): t["both1"] if L == 0 else t["both0"]}[(r0, r1)]
        body.append(f"<tr><td class=n>{r0}</td><td class=n>{r1}</td><td class=n>{L}</td><td class=n>{b(g0)}</td>"
                    f"<td class=n>{b(g1)}</td><td class=n>{b(d)}</td><td class='muted'>{what}</td></tr>")
    return (f'<div class="tbl"><table><tr><th class=n>r0</th><th class=n>r1</th><th class=n>L</th>'
            f'<th class=n>g0</th><th class=n>g1</th><th class=n>{t["next"]}</th><th></th></tr>'
            + "".join(body) + "</table></div>")


CSS = """
.fig-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card);margin:14px 0 6px;
padding:8px}
svg.arb{display:block;width:100%;min-width:900px;height:auto}
svg.arb text{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.s-gate,.s-chip{fill:var(--card);stroke:var(--fg);stroke-width:1.6}
.s-chip{stroke-width:1.8}.s-notch{fill:var(--bg);stroke:var(--fg);stroke-width:1.4}
.s-line{stroke:var(--fg);stroke-width:1.4;fill:none}
.s-w{fill:none;stroke-width:2.4;stroke-linejoin:round;stroke-linecap:round}
.s-pow{stroke:var(--fg);stroke-width:1.5;fill:none}.s-vdd{stroke:#e03131;stroke-width:1.8;fill:none}
.s-led{fill:var(--card);stroke:var(--fg);stroke-width:1.4}
.s-cloud{fill:var(--accent-bg);stroke:var(--accent);stroke-width:1.2;stroke-dasharray:6 5;opacity:.85}
.s-cloud2{fill:var(--warn-bg);stroke:var(--warn);stroke-width:1.2;stroke-dasharray:6 5;opacity:.85}
.s-cap{fill:var(--muted);font-size:10.5px;letter-spacing:.08em;font-weight:700}
.s-tag{fill:var(--fg);font-size:12px;font-weight:700}.s-tag2{fill:var(--fg);font-size:8.5px;font-weight:700}
.s-sub{fill:var(--muted);font-size:10.5px}.s-io{fill:var(--fg);font-size:12.5px;font-weight:600}
.s-pin{fill:var(--fg);font-size:11px;font-weight:600}.s-pin2{fill:var(--fg);font-size:8px}
.s-pn{fill:var(--muted);font-size:8px}.s-chipname{fill:var(--fg);font-size:12px;font-weight:700}
.s-mod{fill:var(--th);stroke:var(--line);stroke-width:1.2}.s-modt{fill:var(--fg);font-size:8.5px;font-weight:600}
.ol{text-decoration:overline}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:13px;margin:8px 0 4px}
.legend>span{display:inline-flex;align-items:center;gap:5px}
.sw{display:inline-block;width:14px;height:6px;border-radius:3px;margin-right:6px;vertical-align:middle}
.legend .sw{margin-right:0}
table.wires td{padding:4px 10px}table.wires tr.grp td{background:var(--th)}
table.wires tr.done td{opacity:.45}
.wchk{width:16px;height:16px;margin:0;accent-color:var(--accent)}
ol.steps li{margin:6px 0}
pre.code{background:var(--code);border-radius:10px;padding:14px 16px;overflow-x:auto;font-size:13.5px;line-height:1.45}
.eq{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:14px;background:var(--code);
padding:10px 14px;border-radius:8px;display:block;line-height:1.7;overflow-x:auto}
@media print{.fig-wrap{overflow:visible}svg.arb{min-width:0}}
"""

def script(lang="en"):
    return SCRIPT.replace("COUNT_TEXT", T[lang]["count"])


SCRIPT = """<script>
(function(){
  var KEY = 'lssk-arbiter-wires';
  var done = {};
  try { done = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { done = {}; }
  var boxes = document.querySelectorAll('.wchk');
  var count = document.getElementById('wcount');
  function update() {
    var n = 0;
    boxes.forEach(function (b) { if (b.checked) n++; b.closest('tr').classList.toggle('done', b.checked); });
    if (count) count.textContent = 'COUNT_TEXT';
  }
  boxes.forEach(function (b) {
    b.checked = !!done[b.dataset.w];
    b.addEventListener('change', function () {
      done[b.dataset.w] = b.checked;
      try { localStorage.setItem(KEY, JSON.stringify(done)); } catch (e) {}
      update();
    });
  });
  var reset = document.getElementById('wreset');
  if (reset) reset.addEventListener('click', function () {
    done = {};
    try { localStorage.removeItem(KEY); } catch (e) {}
    boxes.forEach(function (b) { b.checked = false; });
    update();
  });
  update();
})();
</script>"""
