"""Sequence-recognizer FSM tasks for the LSSK FSM kit.

For every bit sequence this module builds a Moore FSM (KMP-style prefix
automaton), encodes the states in binary, minimizes the next-state and output
logic (Quine-McCluskey with don't-cares) and maps the result onto CMOS 4000
gate chips.  The result is used to size the FSM kit and to print task cards.
"""

from itertools import product
from math import ceil, log2

MODES = {
    "detector": "Detector: output is 1 for one clock after the last bit of the sequence (overlapping matches allowed)",
    "lock":     "Code lock: once the sequence is entered the output stays 1 until Reset",
}

# Gate chips: name -> (chip, gates per chip, inputs per gate)
GATE_CHIPS = {
    "AND2": ("4081", 4, 2), "AND3": ("4073", 3, 3), "AND4": ("4082", 2, 4),
    "OR2":  ("4071", 4, 2), "OR3":  ("4075", 3, 3), "OR4":  ("4072", 2, 4),
    "NOT":  ("4069", 6, 1),
}


def transitions(seq, mode):
    """Next-state table: state k means the last k inputs equal seq[:k]."""
    n = len(seq)
    def delta(k, x):
        if mode == "lock" and k == n:
            return n
        s = seq[:k] + x
        return max(l for l in range(min(len(s), n) + 1) if s.endswith(seq[:l]))
    return [[delta(k, x) for x in "01"] for k in range(n + 1)]


def _combine(a, b):
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    if len(diff) == 1 and "-" not in (a[diff[0]], b[diff[0]]):
        return a[:diff[0]] + "-" + a[diff[0] + 1:]
    return None


def _covers(imp, m):
    return all(c == "-" or c == mb for c, mb in zip(imp, m))


def minimize(nvars, ones, dcs):
    """Return a list of implicants (strings over 0/1/-) covering `ones`."""
    if not ones:
        return []
    terms = {format(m, f"0{nvars}b") for m in ones | dcs}
    primes = set()
    while terms:
        used, nxt = set(), set()
        tl = sorted(terms)
        for i in range(len(tl)):
            for j in range(i + 1, len(tl)):
                c = _combine(tl[i], tl[j])
                if c:
                    nxt.add(c)
                    used.update((tl[i], tl[j]))
        primes |= terms - used
        terms = nxt
    ones_b = {format(m, f"0{nvars}b") for m in ones}
    cover, left = [], set(ones_b)
    # essential prime implicants
    for m in sorted(ones_b):
        cands = [p for p in primes if _covers(p, m)]
        if len(cands) == 1 and cands[0] not in cover:
            cover.append(cands[0])
    for p in cover:
        left -= {m for m in left if _covers(p, m)}
    while left:
        best = max(sorted(primes), key=lambda p: (sum(_covers(p, m) for m in left), p.count("-")))
        cover.append(best)
        left -= {m for m in left if _covers(best, m)}
    return cover


def literal_names(nbits):
    return [f"S{i}" for i in range(nbits - 1, -1, -1)] + ["A"]


def term_to_str(t, names):
    lits = [(n if c == "1" else n + "'") for c, n in zip(t, names) if c != "-"]
    return "·".join(lits) if lits else "1"


def solve(seq, mode):
    n = len(seq)
    tr = transitions(seq, mode)
    nstates = n + 1
    nb = max(1, ceil(log2(nstates)))
    nv = nb + 1
    names = literal_names(nb)
    used_codes = set(range(nstates))
    ones = {f"D{b}": set() for b in range(nb)}
    dcs = set()
    y_ones = set()
    for code in range(2 ** nb):
        for a in (0, 1):
            m = (code << 1) | a
            if code not in used_codes:
                dcs.add(m)
                continue
            nxt = tr[code][a]
            for b in range(nb):
                if (nxt >> b) & 1:
                    ones[f"D{b}"].add(m)
            if code == n:
                y_ones.add(m)
    funcs = {k: minimize(nv, v, dcs) for k, v in ones.items()}
    funcs["Y"] = minimize(nv, y_ones, dcs)

    # gate counting with shared product terms
    gates = {k: 0 for k in GATE_CHIPS}
    wires = 0
    and_terms = set()
    inverted = set()
    consts = 0
    for name, terms in funcs.items():
        for t in terms:
            lits = [(i, c) for i, c in enumerate(t) if c != "-"]
            for i, c in lits:
                if c == "0":
                    inverted.add(i)
            if len(lits) == 0:
                consts += 1
            elif len(lits) >= 2:
                and_terms.add(t)
        k = len(terms)
        if k >= 2:
            remaining = k
            while remaining > 1:
                take = min(4, remaining)
                gates[f"OR{take}"] += 1
                wires += take
                remaining -= take - 1
            wires += 1                       # OR output -> D input / LED
        elif k == 1:
            wires += 1                       # term or literal -> D input / LED
    for t in and_terms:
        lits = sum(c != "-" for c in t)
        while lits > 4:
            gates["AND4"] += 1
            wires += 4
            lits -= 3
        gates[f"AND{lits}"] += 1
        wires += lits
    gates["NOT"] += len(inverted) + 1        # +1: Reset -> active-low CLR of 40174
    wires += len(inverted) + 2 + consts

    chips = {"40174": 1}
    tie_offs = 6 - (nb + 1)                  # unused D inputs of 40174 (one FF synchronizes A)
    for g, cnt in gates.items():
        if cnt:
            chip, per, ins = GATE_CHIPS[g]
            chips[chip] = chips.get(chip, 0) + ceil(cnt / per)
            tie_offs += (ceil(cnt / per) * per - cnt) * ins
    power = 2 * sum(chips.values())
    clock_reset = 2
    leds = nb + 3                            # GND, state bits, synchronized A, clock
    total = power + wires + tie_offs + clock_reset + leds
    eqs = {k: (" + ".join(term_to_str(t, names) for t in v) if v else "0") for k, v in funcs.items()}
    return {
        "seq": seq, "mode": mode, "states": nstates, "state_bits": nb,
        "transitions": tr, "equations": eqs, "gates": {k: v for k, v in gates.items() if v},
        "chips": chips, "wires": total,
        "wire_breakdown": {"power": power, "logic": wires, "tie_offs": tie_offs,
                           "clock_reset": clock_reset, "leds": leds},
    }


def all_tasks(max_len=6, min_len=2):
    out = []
    for n in range(min_len, max_len + 1):
        for bits in product("01", repeat=n):
            for mode in MODES:
                out.append(solve("".join(bits), mode))
    return out


if __name__ == "__main__":
    import collections
    tasks = all_tasks()
    print(solve("01", "detector"))
    for n in range(2, 7):
        ts = [t for t in tasks if len(t["seq"]) == n]
        mx = collections.Counter()
        for t in ts:
            for c, q in t["chips"].items():
                mx[c] = max(mx[c], q)
        w = [t["wires"] for t in ts]
        print(n, "chips max", dict(mx), "wires min/avg/max", min(w), sum(w) // len(w), max(w))


def fits(task, inventory):
    """Check whether the task's gates fit an inventory {chip: count}.

    Wider gates may replace narrower ones (extra inputs tied to VDD/GND);
    a missing inverter may be made from a spare NAND (4011) or NOR (4001)."""
    free = {}
    for kind in ("AND", "OR"):
        for k in (2, 3, 4):
            chip, per, _ = GATE_CHIPS[f"{kind}{k}"]
            free[(kind, k)] = inventory.get(chip, 0) * per
    need = task["gates"]
    for kind in ("AND", "OR"):
        for k in (4, 3, 2):
            cnt = need.get(f"{kind}{k}", 0)
            for width in range(k, 5):
                use = min(cnt, free[(kind, width)])
                free[(kind, width)] -= use
                cnt -= use
            if cnt:
                return False
    nots = need.get("NOT", 0) - inventory.get("4069", 0) * 6
    spare = inventory.get("4011", 0) * 4 + inventory.get("4001", 0) * 4
    return nots <= spare and inventory.get("40174", 0) >= 1
