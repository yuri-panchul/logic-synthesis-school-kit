"""Generate exercises.html and the kit CSV/HTML files from lssk_data.py.

Usage:  python3 tools/generate.py        (writes into the repository root)
"""

import csv
import json
import os
from collections import defaultdict
from html import escape
from math import ceil

import diagrams
from fsm_tasks import MODES, all_tasks, fits
from lssk_data import (CATALOG, DOC_URL, EXERCISES, HABR_URL, JULY23_URL, JULY31_URL, KITS, PRICING,
                       SECTIONS, SHEET_URL)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = {e["id"]: e for e in EXERCISES}

GENERIC = {"btn", "ledmod", "disp", "res", "clk", "bb", "traffic", "led_r", "led_g", "led_y"}
RARE_CHIPS = {"40108", "40181"}

# ----------------------------------------------------------------------------
# Kit computation
# ----------------------------------------------------------------------------

def wire_plan(w, mm):
    """Return {part: packs} for on-board wires w and board-to-board wires mm."""
    demand = ceil(w * 1.25) + mm
    if demand <= 80:
        return {"mm40": ceil(demand / 40)}
    plan = {"wire350": 1}
    if mm:
        plan["mm40"] = 1
    return plan


def expand_generic(key, q):
    """Map a generic requirement to catalog parts."""
    if key == "btn":
        return {"btn5a": 1} if q <= 5 else {"btn5a": 1, "btn5b": ceil((q - 5) / 5)}
    if key == "ledmod":
        return {"ledmod_b": 1} if q <= 1 else {"ledmod_b": 1, "ledmod_r": q - 1}
    if key == "disp":
        return {"disp_g": min(q, 2), **({"disp_r": q - 2} if q > 2 else {})}
    if key == "res":
        return {"res": ceil(q * 1.1 / 5) * 5}
    if key == "bb":
        return {"bb": q} if q <= 2 else {"bb_set": 1, **({"bb": q - 2} if q > 2 else {})}
    return {key: q}


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def compute_kit(kit):
    exs = [EX[i] for i in kit["exercises"]]
    need = defaultdict(int)
    origin = defaultdict(list)
    for e in exs:
        for k, q in e["parts"].items():
            if e.get("rare") and k in RARE_CHIPS:
                continue
            need[k] = max(need[k], q)
            for part in (expand_generic(k, q) if k in GENERIC else {k: q}):
                origin[part].append(e["id"])
        for part in e.get("alt_parts", []):
            origin[part].append(e["id"] + " (alt.)")
    qty = defaultdict(int)
    for k, q in need.items():
        for part, pq in (expand_generic(k, q) if k in GENERIC else {k: q}).items():
            qty[part] = max(qty[part], pq)
    wmax = max(e["w"] for e in exs)
    mmax = max(e["mm"] for e in exs)
    mfmax = max(e["mf"] for e in exs)
    for part, q in wire_plan(wmax, mmax).items():
        qty[part] = max(qty[part], q)
    qty["mf40"] = max(qty["mf40"], ceil(mfmax * 1.1 / 40))
    for part in ("psu", "usbdc9", "ic_extractor"):
        qty[part] = max(qty[part], 1)
    optional_keys = {k for k, _, _ in kit["optional"]}
    if kit.get("use_sheet_qty"):
        for k, c in CATALOG.items():
            if c[5] > 0 and k not in optional_keys:
                qty[k] = max(qty[k], c[5])
    origin["mf40"] = [e["id"] for e in exs if e["mf"]]
    if "wire350" in qty:
        origin["wire350"] = [e["id"] for e in exs if e["w"]]
        origin["mm40"] = [e["id"] for e in exs if e["mm"]]
    else:
        origin["mm40"] = [e["id"] for e in exs if e["w"] or e["mm"]]
    for part in ("psu", "usbdc9", "ic_extractor", "pin_straightener", "bb", "bb_set"):
        origin[part] = ["all"]

    def at_max(k):
        return ", ".join(e["id"] for e in exs if e["parts"].get(k, 0) == need[k] and not (e.get("rare") and k in RARE_CHIPS))

    why = {}
    for part in qty:
        if part in ("btn5a", "btn5b"):
            why[part] = f"up to {plural(need['btn'], 'button')} at once ({at_max('btn')})"
        elif part in ("ledmod_b", "ledmod_r"):
            why[part] = f"up to {plural(need['ledmod'], 'LED array')} at once ({at_max('ledmod')})"
        elif part in ("disp_g", "disp_r"):
            why[part] = f"up to {plural(need['disp'], 'display')} at once ({at_max('disp')})"
        elif part == "res":
            why[part] = f"up to {need['res']} at once ({at_max('res')}) + spares"
        elif part in ("bb", "bb_set"):
            why[part] = f"up to {plural(need['bb'], 'large board')} at once ({at_max('bb')})"
        elif part == "wire350" or (part == "mm40" and "wire350" not in qty):
            why[part] = f"largest build ≈{wmax} wires on the board" + (f" + {mmax} between boards" if mmax else "") + " + 25% spare"
        elif part == "mm40":
            why[part] = f"{mmax} jumpers for the power rails between boards, plus long runs"
        elif part == "mf40":
            why[part] = f"largest build {mfmax} M-F (3 per button or clock module)"
        elif part in need and need[part] > 1:
            why[part] = f"{need[part]} at once in {at_max(part)}"
        elif part == "pin_straightener":
            why[part] = "teacher tool, as in the sheet"
        elif (kit.get("use_sheet_qty") and CATALOG[part][0] in ("IC", "Display", "LED", "Input")
              and qty[part] > need.get(part, 0)):
            why[part] = "sheet quantity: spare for a damaged chip or a second group" if need.get(part) else "sheet quantity"
    lines = []
    for part in sorted(qty, key=order_key):
        if qty[part] <= 0:
            continue
        c = CATALOG[part]
        lines.append(dict(key=part, cat=c[0], name=c[1], desc=c[2], qty=qty[part], price=c[3],
                          total=round(qty[part] * c[3], 2), supplier=c[4],
                          used=", ".join(dict.fromkeys(origin.get(part, []))),
                          why=why.get(part, "")))
    opt = []
    for part, q, note in sorted(kit["optional"], key=lambda o: order_key(o[0])):
        c = CATALOG[part]
        opt.append(dict(key=part, cat=c[0], name=c[1], desc=c[2], qty=q, price=c[3],
                        total=round(q * c[3], 2), supplier=c[4], used="", why=note))
    covered = [e["id"] for e in exs]
    also = [e["id"] for e in EXERCISES if e["id"] not in covered and possible_with(e, qty)]
    return dict(lines=lines, optional=opt, wmax=wmax, mfmax=mfmax, mmax=mmax, also=also,
                pricing=price_summary(kit, lines, opt))


CAT_ORDER = ["IC", "Display", "LED", "Input", "Clock", "Power", "Breadboard", "Wires", "Tool"]


def order_key(part):
    c = CATALOG[part]
    keys = list(CATALOG)
    return (CAT_ORDER.index(c[0]), keys.index(part))


def possible_with(e, qty):
    if e.get("rare"):
        return False
    have = dict(qty)
    btns = 5 * have.get("btn5a", 0) + 5 * have.get("btn5b", 0)
    mods = have.get("ledmod_b", 0) + have.get("ledmod_r", 0)
    disps = have.get("disp_g", 0) + have.get("disp_r", 0)
    boards = have.get("bb", 0) + 2 * have.get("bb_set", 0)
    for k, q in e["parts"].items():
        if k == "btn" and btns < q: return False
        elif k == "ledmod" and mods < q: return False
        elif k == "disp" and disps < q: return False
        elif k == "bb" and boards < q: return False
        elif k in ("led_r", "led_g", "led_y") and have.get(k, 0) < q and mods == 0: return False
        elif k not in GENERIC and have.get(k, 0) < q: return False
        elif k in ("res", "clk", "traffic") and have.get(k, 0) < q: return False
    cap = 250 * have.get("wire350", 0) + 40 * have.get("mm40", 0)
    return e["w"] + e["mm"] <= cap and e["mf"] <= 40 * have.get("mf40", 0)


def price_round(x):
    return ceil(x) - 0.01


def price_summary(kit, lines, opt):
    p = PRICING
    parts = round(sum(l["total"] for l in lines), 2)
    opt_total = round(sum(l["total"] for l in opt), 2)
    spares = parts * p["spares_pct"] / 100
    inbound = parts * p["inbound_pct"] / 100
    labor = p["labor_base"] + p["labor_per_line"] * len(lines)
    landed = parts + spares + inbound + kit["packaging"] + kit["docs"] + labor
    classroom = price_round(landed * p["classroom_mult"])
    retail = price_round(landed * p["retail_mult"])
    return dict(parts=parts, optional=opt_total, spares=round(spares, 2), inbound=round(inbound, 2),
                packaging=kit["packaging"], docs=kit["docs"], labor=round(labor, 2), lines=len(lines),
                landed=round(landed, 2), classroom=classroom, retail=retail,
                classroom_margin=round(100 * (classroom - landed) / classroom),
                retail_margin=round(100 * (retail - landed) / retail))


# ----------------------------------------------------------------------------
# HTML helpers
# ----------------------------------------------------------------------------

CSS = """
:root{--bg:#f7f6f2;--fg:#1c2329;--muted:#5d6872;--card:#ffffff;--line:#dfe3e6;--accent:#0b6e4f;
--accent-bg:#e5f2ec;--warn:#9a4d00;--warn-bg:#fdf1e3;--code:#eef1f3;--th:#f0f2f1;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#13171b;--fg:#e5e9ec;--muted:#9aa6b0;
--card:#1b2126;--line:#2d363d;--accent:#55c79a;--accent-bg:#1b3027;--warn:#f0b06a;--warn-bg:#33261a;--code:#232b31;--th:#20282e;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#13171b;--fg:#e5e9ec;--muted:#9aa6b0;--card:#1b2126;--line:#2d363d;--accent:#55c79a;
--accent-bg:#1b3027;--warn:#f0b06a;--warn-bg:#33261a;--code:#232b31;--th:#20282e;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1120px;margin:0 auto;padding:24px 16px 64px}
nav.top{background:var(--card);border-bottom:1px solid var(--line);font-size:14px}
nav.top div{max-width:1120px;margin:0 auto;padding:10px 16px;display:flex;flex-wrap:wrap;gap:6px 16px}
nav.top a{color:var(--muted);text-decoration:none}nav.top a:hover,nav.top a.cur{color:var(--accent)}
h1{font-size:30px;line-height:1.2;margin:8px 0 6px}h2{font-size:22px;margin:36px 0 10px}
h3{font-size:18px;margin:0 0 6px}
p.lead{font-size:18px;color:var(--muted);margin:0 0 18px;max-width:820px}
a{color:var(--accent)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:16px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.stat b{display:block;font-size:24px;line-height:1.2}.stat span{color:var(--muted);font-size:13px}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--th);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:0}td.n,th.n{text-align:right;white-space:nowrap}
tr.sum td{font-weight:600;background:var(--th)}
.tag{display:inline-block;font-size:12px;padding:1px 8px;border-radius:999px;background:var(--accent-bg);
color:var(--accent);margin:2px 4px 2px 0;white-space:nowrap}
.tag.warn{background:var(--warn-bg);color:var(--warn)}
.muted{color:var(--muted)}.small{font-size:13px}
.note{background:var(--warn-bg);border-radius:10px;padding:12px 16px;margin:14px 0}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:90%}
.ex-head{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.ex-id{font-weight:700;color:var(--accent);min-width:44px}
.res{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:8px;font-size:14px}
.res span b{font-weight:600}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.filters button,.btn{font:inherit;font-size:14px;padding:6px 12px;border-radius:8px;border:1px solid var(--line);
background:var(--card);color:var(--fg);cursor:pointer}
.filters button.on,.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--bg)}
input,select{font:inherit;font-size:14px;padding:5px 8px;border-radius:6px;border:1px solid var(--line);
background:var(--card);color:var(--fg)}
.calc{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 18px}
.calc label{font-size:14px;display:flex;justify-content:space-between;gap:8px;align-items:center}
.calc input{width:90px;text-align:right}
footer{margin-top:48px;font-size:13px;color:var(--muted)}
figure{margin:18px 0}figure img{max-width:100%;height:auto;border-radius:10px;border:1px solid var(--line);display:block}
figcaption{font-size:13px;color:var(--muted);margin-top:6px}
b.tp{color:#d64541}b.tn{color:#2f6fd0}
@media print{nav.top,.filters,.noprint{display:none}body{background:#fff;color:#000}.card,.tbl{break-inside:avoid}}
"""

PAGES = [
    ("getting_started_en.html", "Getting started (EN)"),
    ("getting_started_ru.html", "Как начать (RU)"),
    ("exercises.html", "Exercises"),
] + [(f"{k['id']}.html", k["name"]) for k in KITS]


def page(title, current, body, lang="en", extra_css=""):
    nav = "".join(f'<a href="{f}"{" class=cur" if f == current else ""}>{escape(t)}</a>' for f, t in PAGES)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<style>{CSS}{extra_css}</style>
</head>
<body>
<nav class="top"><div><b>LSSK</b>{nav}</div></nav>
<main>
{body}
<footer>Logic Synthesis School Kit · Verilog Meetup · generated from <code>tools/lssk_data.py</code>
with prices from the <a href="{SHEET_URL}">LSSK components sheet</a> (snapshot 2026-10-14).</footer>
</main>
</body>
</html>
"""


def money(x):
    return f"${x:,.2f}"


def supplier_html(s):
    if s.startswith("http"):
        host = s.split("/")[2].replace("www.", "")
        return f'<a href="{escape(s)}">{escape(host)}</a>'
    return escape(s)


def part_label(key, q):
    if key in CATALOG and CATALOG[key][0] == "IC":
        return f"{q} × {CATALOG[key][1].replace('CD74HC', '').replace('CD', '')}" if q > 1 else CATALOG[key][1].replace("CD74HC", "").replace("CD", "")
    names = {"btn": "button", "ledmod": "8-LED module", "disp": "7-seg display", "res": "560 Ω resistor",
             "clk": "555 clock module", "bb": "breadboard", "traffic": "traffic-light LED",
             "led_r": "red 5V LED", "led_g": "green 5V LED", "led_y": "yellow 5V LED"}
    n = names[key]
    return f"{q} {n}{'s' if q > 1 and not n.endswith('s') else ''}"


def ex_chips(e):
    chips = [k for k in e["parts"] if k not in GENERIC]
    return ", ".join(part_label(k, e["parts"][k]) for k in chips)


def ex_other(e):
    return ", ".join(part_label(k, q) for k, q in e["parts"].items() if k in GENERIC and k != "bb")


def kits_for(eid):
    return [k for k in KITS if eid in k["exercises"]]


# ----------------------------------------------------------------------------
# getting_started_{en,ru}.html
# ----------------------------------------------------------------------------

# (part, qty, EN name, EN purpose, RU name, RU purpose)
START_PARTS = [
    ("bb", 1, "Breadboard, 830 points", "Everything is built on it",
     "Макетная плата на 830 точек", "На ней собирается всё"),
    ("psu", 1, "Breadboard power module", "Stable 5 V on the rails; set its jumpers to 5 V",
     "Блок питания для макетки", "Стабильные 5 В на шинах; перемычки на 5 В"),
    ("usbdc9", 1, "USB-to-DC cable, 9 V", "Feeds the power module from USB. Not the 5 V one",
     "Шнур USB-DC на 9 В", "Питание блока от USB. Не на 5 В"),
    ("led_g", 1, "5V-tolerant LED", "Step 3: no resistor needed",
     "Светодиод, толерантный к 5 В", "Шаг 3: резистор не нужен"),
    ("ledmod_b", 1, "8-LED module", "8 LEDs with a common GND pin, no resistors",
     "Линейка из 8 светодиодов", "8 светодиодов с общей землёй, без резисторов"),
    ("btn5a", 1, "Button modules (5 pcs)", "Step 5: built-in pull-down resistor, pins + / OUT / −",
     "Модули кнопок (5 шт.)", "Шаг 5: подтягивающий резистор внутри, выводы + / OUT / −"),
    ("4081", 1, "CD4081, quad AND", "Step 4: the first chip", "CD4081, четыре элемента И", "Шаг 4: первый чип"),
    ("4071", 1, "CD4071, quad OR", "Step 5: truth tables", "CD4071, четыре элемента ИЛИ", "Шаг 5: таблицы истинности"),
    ("4070", 1, "CD4070, quad XOR", "Step 5: truth tables", "CD4070, четыре элемента искл. ИЛИ", "Шаг 5: таблицы истинности"),
    ("mm40", 1, "Male-male jumpers (40)", "Power and signal wires on the board",
     "Перемычки папа-папа (40)", "Питание и сигналы на плате"),
    ("mf40", 1, "Male-female jumpers (40)", "Button modules, 3 per button",
     "Перемычки папа-мама (40)", "Кнопки, по 3 на кнопку"),
    ("wire350", 1, "Pre-cut jumper wires (350), optional", "Tidier boards than Dupont jumpers",
     "Набор нарезанных перемычек (350), по желанию", "Аккуратнее, чем перемычки Dupont"),
    ("ic_extractor", 1, "IC extractor", "Pull chips out without bending pins",
     "Приспособление для вынимания чипа", "Вынимать чипы, не сгибая ножки"),
    ("pin_straightener", 1, "IC pin straightener, recommended", "Straightens the pins of new chips",
     "Выпрямитель ножек, рекомендуется", "Выпрямляет ножки новых чипов"),
]


def build_getting_started(lang):
    ru = lang == "ru"
    head = ("<tr><th>Компонент</th><th class=n>Кол-во</th><th>Зачем</th><th class=n>Цена</th><th>Где купить</th></tr>"
            if ru else "<tr><th>Part</th><th class=n>Qty</th><th>What for</th><th class=n>Price</th><th>Where</th></tr>")
    rows = []
    for key, q, en, en_why, ru_name, ru_why in START_PARTS:
        c = CATALOG[key]
        rows.append(f"<tr><td><b>{escape(ru_name if ru else en)}</b></td><td class=n>{q}</td>"
                    f"<td>{escape(ru_why if ru else en_why)}</td><td class=n>{money(c[3])}</td>"
                    f"<td class=small>{supplier_html(c[4])}</td></tr>")
    table = f'<div class="tbl"><table>{head}{"".join(rows)}</table></div>'
    note = ("<p class='small muted'>Цены и ссылки из <a href='{sheet}'>таблицы LSSK</a>. Полный набор для "
            "первых упражнений: <a href='kit1_basics.html'>Basics kit</a>.</p>" if ru else
            "<p class='small muted'>Prices and links from the <a href='{sheet}'>LSSK sheet</a>. The full set for "
            "the first exercises: <a href='kit1_basics.html'>Basics kit</a>.</p>").format(sheet=SHEET_URL)
    with open(os.path.join(os.path.dirname(__file__), "content", f"getting_started_{lang}.html")) as f:
        body = f.read()
    subs = dict(diagrams.fragments(lang), parts_table=table + note, july23=JULY23_URL, habr=HABR_URL,
                sheet=SHEET_URL)
    for k, v in subs.items():
        body = body.replace("{{" + k + "}}", v)
    title = "LSSK: как начать" if ru else "LSSK: how to start"
    name = f"getting_started_{lang}.html"
    with open(os.path.join(ROOT, name), "w") as f:
        f.write(page(title, name, body, lang=lang, extra_css=diagrams.CSS))


# ----------------------------------------------------------------------------
# exercises.html
# ----------------------------------------------------------------------------

def build_exercises():
    rows, cards = [], []
    for sec, sec_name in SECTIONS:
        exs = [e for e in EXERCISES if e["id"].rstrip("0123456789") == sec]
        rows.append(f'<tr class="sum"><td colspan="11">{escape(sec_name)}</td></tr>')
        cards.append(f"<h2 id='sec-{sec}'>{escape(sec_name)}</h2>")
        for e in exs:
            p = e["parts"]
            kit_ids = " ".join(k["id"] for k in kits_for(e["id"]))
            leds = []
            if p.get("ledmod"): leds.append(plural(p["ledmod"], "array"))
            single = sum(p.get(k, 0) for k in ("led_r", "led_g", "led_y"))
            if single: leds.append(plural(single, "LED"))
            if p.get("traffic"): leds.append("traffic light")
            disp = f"{p['disp']}, {p.get('res', 0)}&nbsp;R" if p.get("disp") else ""
            rare_tag = ' <span class="tag warn">rare chip</span>' if e.get("rare") else ""
            rows.append(
                f'<tr data-kits="{kit_ids}"><td><a href="#{e["id"]}">{e["id"]}</a></td>'
                f'<td>{escape(e["title"])}{rare_tag}</td>'
                f'<td>{escape(ex_chips(e))}</td><td class=n>{p.get("btn", "")}</td><td>{", ".join(leds)}</td>'
                f'<td class=n>{disp}</td><td class=n>{"yes" if p.get("clk") else ""}</td>'
                f'<td class=n>≈{e["w"]}</td><td class=n>{e["mf"] or ""}</td><td class=n>{e["mm"] or ""}</td>'
                f'<td class=n>{p.get("bb", 1)}</td></tr>')
            src = "".join(f'<span class="tag">{escape(s)}</span>' for s in e["sources"])
            kit_tags = "".join(f'<a class="tag" href="{k["id"]}.html">Kit {k["n"]}: {escape(k["name"])}</a>'
                               for k in kits_for(e["id"]))
            rare = '<span class="tag warn">rare, expensive chip</span>' if e.get("rare") else ""
            one = '<p class="small muted">The listed chips are used one at a time; the wire count is for the largest one.</p>' if e.get("one_at_a_time") else ""
            alts = f'<p class="small muted">{escape(e["alts"])}</p>' if e.get("alts") else ""
            cards.append(f"""<div class="card" id="{e['id']}" data-kits="{kit_ids}">
<div class="ex-head"><span class="ex-id">{e['id']}</span><h3>{escape(e['title'])}</h3></div>
<div>{src}{rare}</div>
<p>{escape(e['text'])}</p>{one}{alts}
<div class="res">
<span><b>Chips:</b> {escape(ex_chips(e))}</span>
<span><b>Other parts:</b> {escape(ex_other(e))}</span>
<span><b>Breadboards:</b> {p.get('bb', 1)} × 830</span>
</div>
<div class="res">
<span><b>Pre-cut wires:</b> ≈{e['w']} <span class="muted">({escape(e['wb'])})</span></span>
<span><b>Dupont M-F:</b> {e['mf']}</span>
<span><b>Dupont M-M:</b> {e['mm']}</span>
</div>
<div style="margin-top:8px">{kit_tags}</div>
</div>""")
    filt = "".join(f'<button data-kit="{k["id"]}">Kit {k["n"]}: {escape(k["name"])}</button>' for k in KITS)
    body = f"""
<h1>Breadboard exercises</h1>
<p class="lead">All {len(EXERCISES)} small-scale-integration breadboard exercises from the
<a href="{JULY31_URL}">July 31</a> and <a href="{JULY23_URL}">July 23</a> Verilog Meetup posts and from
<a href="{HABR_URL}">Habr section 1</a> (lessons 1.1-1.7), merged where they overlap, with the components
each one needs from the <a href="{SHEET_URL}">LSSK sheet</a>.</p>

<div class="card small">
<b>How the counts were made.</b> Each exercise uses the kit's simplifications: 5V-tolerant LEDs and 8-LED
arrays without resistors, button modules with built-in pull-downs (VCC / OUT / GND), an assembled 555 clock
module, and the breadboard power module set to 5V. Only 7-segment displays need 560 Ω ½ W resistors.
<ul>
<li><b>Pre-cut wires</b> are jumpers on the breadboard: two per chip for power, one per signal connection,
and one per tie-off. CMOS inputs must never float, so every unused input of a used chip is tied to GND or
+5V. These are estimates from the chip pinouts (±20%); the kits add about 25% spare.</li>
<li><b>Dupont M-F</b>: 3 per button module and 3 for the 555 module (VCC, signal, GND), as in note 5.</li>
<li><b>Dupont M-M</b>: power rails between two or three breadboards.</li>
<li>Exercises are built one after another, so a kit needs the maximum of each part over its exercises,
not the sum.</li>
</ul>
</div>

<h2>Summary</h2>
<div class="filters noprint"><button class="on" data-kit="">All exercises</button>{filt}</div>
<div class="tbl"><table id="summary">
<tr><th>#</th><th>Exercise</th><th>Chips</th><th class=n>Buttons</th><th>LEDs</th><th class=n>7-seg</th>
<th class=n>555</th><th class=n>Wires</th><th class=n>M-F</th><th class=n>M-M</th><th class=n>Boards</th></tr>
{''.join(rows)}
</table></div>

{''.join(cards)}

<script>
document.querySelectorAll('.filters button').forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll('.filters button').forEach(x => x.classList.toggle('on', x === b));
  const k = b.dataset.kit;
  document.querySelectorAll('[data-kits]').forEach(el => {{
    el.style.display = !k || el.dataset.kits.split(' ').includes(k) ? '' : 'none';
  }});
}}));
</script>
"""
    with open(os.path.join(ROOT, "exercises.html"), "w") as f:
        f.write(page("LSSK breadboard exercises", "exercises.html", body))


# ----------------------------------------------------------------------------
# kit CSV + HTML
# ----------------------------------------------------------------------------

def write_csv(kit, r):
    path = os.path.join(ROOT, f"{kit['id']}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Section", "Category", "Part", "Description", "Qty", "Unit price USD", "Total USD",
                    "Used in exercises", "Why this quantity / note", "Supplier"])
        for sec, lines in (("Core", r["lines"]), ("Optional", r["optional"])):
            for l in lines:
                w.writerow([sec, l["cat"], l["name"], l["desc"], l["qty"], f"{l['price']:.2f}",
                            f"{l['total']:.2f}", l["used"], l["why"], l["supplier"]])
        s = r["pricing"]
        p = PRICING
        summary = [
            ("Parts, core", s["parts"]),
            (f"Spares and breakage allowance ({p['spares_pct']}%)", s["spares"]),
            (f"Inbound shipping and duties ({p['inbound_pct']}%)", s["inbound"]),
            ("Packaging (box, anti-static foam, bags, label)", s["packaging"]),
            ("Printed quick-start card with QR links", s["docs"]),
            (f"Kitting labor ({s['lines']} lines)", s["labor"]),
            ("Landed cost per kit", s["landed"]),
            (f"Suggested classroom / bulk price ({p['classroom_mult']}x landed)", s["classroom"]),
            (f"Suggested retail price ({p['retail_mult']}x landed)", s["retail"]),
            ("Optional add-ons, parts cost", s["optional"]),
        ]
        w.writerow([])
        for name, val in summary:
            w.writerow(["Cost summary", "", name, "", "", "", f"{val:.2f}", "", "", ""])


def lines_table(lines, show_used=True):
    out = ['<div class="tbl"><table><tr><th>Part</th><th>Description</th><th class=n>Qty</th>'
           '<th class=n>Unit</th><th class=n>Total</th>' + ("<th>Used in</th>" if show_used else "") +
           '<th>Why / note</th><th>Supplier</th></tr>']
    cat = None
    for l in lines:
        if l["cat"] != cat:
            cat = l["cat"]
            out.append(f'<tr class="sum"><td colspan="{8 if show_used else 7}">{escape(cat)}</td></tr>')
        used = ", ".join(f'<a href="exercises.html#{u}">{u}</a>' if u in EX else escape(u)
                         for u in l["used"].split(", ") if u)
        out.append(f'<tr><td><b>{escape(l["name"])}</b></td><td>{escape(l["desc"])}</td>'
                   f'<td class=n>{l["qty"]}</td><td class=n>{money(l["price"])}</td>'
                   f'<td class=n>{money(l["total"])}</td>' + (f'<td>{used}</td>' if show_used else "") +
                   f'<td class="small">{escape(l["why"])}</td><td class="small">{supplier_html(l["supplier"])}</td></tr>')
    total = sum(l["total"] for l in lines)
    out.append(f'<tr class="sum"><td colspan="4">Total</td><td class=n>{money(total)}</td>'
               f'<td colspan="{3 if show_used else 2}"></td></tr></table></div>')
    return "\n".join(out)


def calc_html(kit, s):
    p = PRICING
    return f"""
<div class="card noprint" id="calc">
<h3>Price calculator</h3>
<p class="small muted">Change the assumptions; the figures above are the defaults.</p>
<div class="calc">
<label>Parts, core ($) <input id="c_parts" type="number" step="0.01" value="{s['parts']:.2f}"></label>
<label>Spares (%) <input id="c_sp" type="number" step="1" value="{p['spares_pct']}"></label>
<label>Inbound shipping (%) <input id="c_in" type="number" step="1" value="{p['inbound_pct']}"></label>
<label>Packaging ($) <input id="c_pk" type="number" step="0.1" value="{kit['packaging']:.2f}"></label>
<label>Printed card ($) <input id="c_doc" type="number" step="0.1" value="{kit['docs']:.2f}"></label>
<label>Labor ($) <input id="c_lab" type="number" step="0.1" value="{s['labor']:.2f}"></label>
<label>Classroom multiplier <input id="c_cm" type="number" step="0.1" value="{p['classroom_mult']}"></label>
<label>Retail multiplier <input id="c_rm" type="number" step="0.1" value="{p['retail_mult']}"></label>
</div>
<div class="grid">
<div class="stat"><b id="o_landed"></b><span>landed cost</span></div>
<div class="stat"><b id="o_class"></b><span>classroom price</span></div>
<div class="stat"><b id="o_retail"></b><span>retail price</span></div>
</div>
</div>
<script>
(function(){{
  const v = id => parseFloat(document.getElementById(id).value) || 0;
  const r = x => (Math.ceil(x) - 0.01);
  function upd(){{
    const parts = v('c_parts');
    const landed = parts * (1 + (v('c_sp') + v('c_in')) / 100) + v('c_pk') + v('c_doc') + v('c_lab');
    const c = r(landed * v('c_cm')), t = r(landed * v('c_rm'));
    document.getElementById('o_landed').textContent = '$' + landed.toFixed(2);
    document.getElementById('o_class').textContent = '$' + c.toFixed(2) + '  (' + Math.round(100 * (c - landed) / c) + '% margin)';
    document.getElementById('o_retail').textContent = '$' + t.toFixed(2) + '  (' + Math.round(100 * (t - landed) / t) + '% margin)';
  }}
  document.querySelectorAll('#calc input').forEach(i => i.addEventListener('input', upd));
  upd();
}})();
</script>"""


def fsm_section(tasks):
    by_len = defaultdict(list)
    for t in tasks:
        by_len[len(t["seq"])].append(t)
    rows = []
    for n in sorted(by_len):
        ts = by_len[n]
        w = [t["wires"] for t in ts]
        chips = [sum(t["chips"].values()) for t in ts]
        rows.append(f"<tr><td class=n>{n}</td><td class=n>{len(ts)}</td><td class=n>{ts[0]['states']}</td>"
                    f"<td class=n>{ts[0]['state_bits']}</td><td class=n>{min(chips)}-{max(chips)}</td>"
                    f"<td class=n>{min(w)}-{max(w)} (avg {round(sum(w) / len(w))})</td>"
                    f"<td class=n>{sum(t['fits'] for t in ts)} / {len(ts)}</td></tr>")
    data = json.dumps([{k: t[k] for k in ("seq", "mode", "states", "state_bits", "transitions", "equations",
                                          "chips", "gates", "wires", "fits")} for t in tasks],
                      separators=(",", ":"))
    modes = json.dumps(MODES)
    return f"""
<h2 id="tasks">Custom FSM task cards</h2>
<p>Every student gets a different sequence. The generator below picks distinct sequences and prints a task
card for the student and an answer key for the teacher: the state table (state <i>k</i> = "the last
<i>k</i> inputs match the first <i>k</i> bits of the sequence"), binary state encoding, minimized
next-state equations (unused state codes are don't-cares), the gate chips and an estimate of the wires.
All {len(tasks)} tasks with 2-5-bit sequences were solved ahead of time to size this kit.</p>
<div class="tbl"><table>
<tr><th class=n>Sequence length</th><th class=n>Tasks (both variants)</th><th class=n>States</th>
<th class=n>State flip-flops</th><th class=n>Chips incl. 40174</th><th class=n>Wires</th>
<th class=n>Fit this kit</th></tr>
{''.join(rows)}
</table></div>
<p class="small muted">Design assumptions: Moore machine; the button is sampled by one spare 40174
flip-flop (synchronized input A); state bits S2..S0 in a 40174 without inverted outputs, so complemented
literals use the 4069; Reset drives the active-low CLEAR of the 40174 through an inverter; when a gate type
runs out, a wider gate with tied inputs or a NAND/NOR inverter is used.</p>

<div class="card noprint">
<div class="calc">
<label>Students <input id="t_n" type="number" min="1" max="40" value="10"></label>
<label>Sequence length <select id="t_len"><option value="3">3 bits</option><option value="4" selected>4 bits</option>
<option value="5">5 bits</option><option value="0">3-5 mixed</option></select></label>
<label>Variant <select id="t_mode"><option value="detector">Detector</option><option value="lock">Code lock</option>
<option value="">Mixed</option></select></label>
<label>Or a fixed sequence <input id="t_seq" placeholder="e.g. 1101" style="width:110px"></label>
</div>
<p style="margin:12px 0 0"><button class="btn primary" id="t_go">Generate cards</button>
<label class="small" style="margin-left:12px"><input type="checkbox" id="t_ans" checked> include answer keys</label>
<button class="btn" onclick="window.print()" style="margin-left:12px">Print</button></p>
</div>
<div id="t_out"></div>
<script>
const TASKS = {data};
const MODES = {modes};
function pick(arr, n) {{ const a = arr.slice(); for (let i = a.length - 1; i > 0; i--) {{ const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }} return a.slice(0, n); }}
function enc(k, nb) {{ return k.toString(2).padStart(nb, '0'); }}
function card(t, i, ans) {{
  const n = t.seq.length;
  const goal = t.mode === 'lock'
    ? `The green LED turns on after the button has produced the sequence <b>${{t.seq}}</b> on consecutive clock edges, and stays on until Reset.`
    : `The green LED is on for one clock period right after the button has produced the sequence <b>${{t.seq}}</b> on consecutive clock edges. Overlapping sequences count.`;
  let h = `<div class="card"><h3>Task ${{i + 1}}: ${{t.mode === 'lock' ? 'code lock' : 'sequence detector'}} for ${{t.seq}}</h3>
  <p>${{goal}} The button is sampled at every rising edge of the 555 clock (pressed = 1). Reset returns the machine to its start state.</p>
  <p class="small muted">Draw the state diagram, choose a state encoding, write the next-state and output equations, then build it with the gates and D flip-flops of the FSM kit.</p>`;
  if (ans) {{
    let rows = t.transitions.map((tr, k) => `<tr><td>S${{k}}</td><td>${{k ? t.seq.slice(0, k) : '-'}}</td><td><code>${{enc(k, t.state_bits)}}</code></td><td>S${{tr[0]}}</td><td>S${{tr[1]}}</td><td>${{k === n ? 1 : 0}}</td></tr>`).join('');
    const eq = Object.entries(t.equations).map(([k, v]) => `<code>${{k}} = ${{v}}</code>`).join('<br>');
    const chips = Object.entries(t.chips).map(([k, v]) => v > 1 ? `${{v}} × ${{k}}` : k).join(', ');
    h += `<details open><summary><b>Answer key</b></summary>
    <div class="tbl"><table><tr><th>State</th><th>Matched</th><th>Code S${{t.state_bits - 1}}..S0</th><th>Next if A=0</th><th>Next if A=1</th><th>Y</th></tr>${{rows}}</table></div>
    <p>${{eq}}</p><p class="small">Chips: ${{chips}}. Estimated wires: ≈${{t.wires}}. ${{t.fits ? 'Fits the FSM kit.' : 'Needs more gates than the FSM kit has.'}}</p></details>`;
  }}
  return h + '</div>';
}}
document.getElementById('t_go').addEventListener('click', () => {{
  const n = parseInt(document.getElementById('t_n').value) || 1;
  const len = parseInt(document.getElementById('t_len').value);
  const mode = document.getElementById('t_mode').value;
  const seq = document.getElementById('t_seq').value.trim();
  const ans = document.getElementById('t_ans').checked;
  let pool;
  if (seq) pool = TASKS.filter(t => t.seq === seq && (!mode || t.mode === mode));
  else pool = pick(TASKS.filter(t => (len ? t.seq.length === len : t.seq.length >= 3) && (!mode || t.mode === mode) && /0/.test(t.seq) && /1/.test(t.seq)), n);
  document.getElementById('t_out').innerHTML = pool.length ? pool.map((t, i) => card(t, i, ans)).join('')
    : '<p class="note">No task: use 2-5 bits of 0 and 1.</p>';
}});
</script>"""


def build_kit(kit):
    r = compute_kit(kit)
    write_csv(kit, r)
    s = r["pricing"]
    ex_list = "".join(f'<li><a href="exercises.html#{i}">{i}</a> {escape(EX[i]["title"])}</li>'
                      for i in kit["exercises"])
    also = ("<p>Also possible with the parts in this kit: " +
            ", ".join(f'<a href="exercises.html#{i}">{i}</a> <span class="muted">{escape(EX[i]["title"])}</span>'
                      for i in r["also"]) + ".</p>") if r["also"] else ""
    if len(kit["exercises"]) > 12:
        ex_block = (f"<p>All {len(kit['exercises'])} exercises in the <a href='exercises.html'>exercise list</a>. "
                    "BB9 and BB10 need the optional rare chips 40108 and 40181.</p>")
    else:
        ex_block = f"<ul>{ex_list}</ul>{also}"
    diff = ""
    if kit.get("sheet_diff"):
        diff = (f"<h2>Compared with the sheet</h2><p>The LSSK sheet has a <i>{escape(kit['sheet_column'])}</i> "
                "column for this kit. Differences:</p><ul>" +
                "".join(f"<li>{escape(d)}</li>" for d in kit["sheet_diff"]) + "</ul>")
    wex = [EX[i] for i in kit["exercises"]]
    wrows = "".join(f'<tr><td><a href="exercises.html#{e["id"]}">{e["id"]}</a></td><td>{escape(e["title"])}</td>'
                    f'<td class=n>≈{e["w"]}</td><td class=n>{e["mf"]}</td><td class=n>{e["mm"]}</td>'
                    f'<td class=n>{e["parts"].get("btn", 0)}</td></tr>' for e in wex)
    wire_part = "the 350-piece pre-cut wire kit" if any(l["key"] == "wire350" for l in r["lines"]) else \
        f"{next(l['qty'] for l in r['lines'] if l['key'] == 'mm40')} × 40 Dupont M-M jumpers"
    p = PRICING
    body = f"""
<p class="muted" style="margin:0">Kit {kit['n']} of {len(KITS)}</p>
<h1>{escape(kit['name'])}</h1>
<p class="lead">{escape(kit['tagline'])}</p>
<div class="grid">
<div class="stat"><b>{money(s['parts'])}</b><span>parts ({s['lines']} lines)</span></div>
<div class="stat"><b>{money(s['landed'])}</b><span>landed cost per kit</span></div>
<div class="stat"><b>{money(s['classroom'])}</b><span>classroom / bulk price, {s['classroom_margin']}% margin</span></div>
<div class="stat"><b>{money(s['retail'])}</b><span>retail price, {s['retail_margin']}% margin</span></div>
</div>
<p class="small">Spreadsheet version: <a href="{kit['id']}.csv">{kit['id']}.csv</a></p>

<h2>Exercises</h2>
{ex_block}

<h2>Parts</h2>
{lines_table(r['lines'])}

<h2>Optional add-ons</h2>
{lines_table(r['optional'], show_used=False)}

<h2>Wires and buttons</h2>
<p>The largest build needs about <b>{r['wmax']}</b> wires on the breadboard{f" and {r['mmax']} between boards" if r['mmax'] else ""}
and <b>{r['mfmax']}</b> male-female jumpers. With about 25% spare, that is {wire_part}. Each button module and
the 555 module take three M-F jumpers.</p>
{"" if len(wex) > 12 else f'''<div class="tbl"><table><tr><th>#</th><th>Exercise</th><th class=n>Pre-cut wires</th>
<th class=n>M-F</th><th class=n>M-M</th><th class=n>Buttons</th></tr>{wrows}</table></div>'''}

<h2>Cost and price</h2>
<div class="tbl"><table>
<tr><td>Parts, core (sheet prices)</td><td class=n>{money(s['parts'])}</td></tr>
<tr><td>Spares and breakage allowance, {p['spares_pct']}%</td><td class=n>{money(s['spares'])}</td></tr>
<tr><td>Inbound shipping and duties, {p['inbound_pct']}%</td><td class=n>{money(s['inbound'])}</td></tr>
<tr><td>Packaging: box, anti-static foam for the chips, bags, label</td><td class=n>{money(s['packaging'])}</td></tr>
<tr><td>Printed quick-start card with QR links to the instructions</td><td class=n>{money(s['docs'])}</td></tr>
<tr><td>Kitting labor: {money(p['labor_base'])} + {money(p['labor_per_line'])} per line × {s['lines']} lines</td><td class=n>{money(s['labor'])}</td></tr>
<tr class="sum"><td>Landed cost per kit</td><td class=n>{money(s['landed'])}</td></tr>
<tr><td>Classroom / bulk price (10+ kits), {p['classroom_mult']}× landed</td><td class=n>{money(s['classroom'])}</td></tr>
<tr><td>Retail price (web shop, Maker Faire), {p['retail_mult']}× landed</td><td class=n>{money(s['retail'])}</td></tr>
<tr><td class="muted">Optional add-ons, parts cost</td><td class="n muted">{money(s['optional'])}</td></tr>
</table></div>
<p class="small muted">Prices are the sheet's unit prices; many are AliExpress bulk prices, and the chip
prices are single-quantity distributor prices that drop with volume. Outbound shipping to the customer is
not included.</p>
{calc_html(kit, s)}
{diff}
{fsm_section(TASKS) if kit['id'] == 'kit5_fsm' else ''}
"""
    with open(os.path.join(ROOT, f"{kit['id']}.html"), "w") as f:
        f.write(page(f"LSSK {kit['name']}", f"{kit['id']}.html", body))
    return r


TASKS = []


def main():
    global TASKS
    fsm_kit = next(k for k in KITS if k["id"] == "kit5_fsm")
    inv = {l["key"]: l["qty"] for l in compute_kit(fsm_kit)["lines"]}
    TASKS = [dict(t, fits=fits(t, inv)) for t in all_tasks(max_len=5)]
    for lang in ("en", "ru"):
        build_getting_started(lang)
    build_exercises()
    for kit in KITS:
        r = build_kit(kit)
        s = r["pricing"]
        print(f"{kit['id']:20s} parts {s['parts']:7.2f}  landed {s['landed']:7.2f}  "
              f"class {s['classroom']:7.2f}  retail {s['retail']:7.2f}  also: {', '.join(r['also'])}")


if __name__ == "__main__":
    main()
