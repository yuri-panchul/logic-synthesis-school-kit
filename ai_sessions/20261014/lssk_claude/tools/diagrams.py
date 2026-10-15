"""Inline SVG diagrams for the getting-started pages (after Yuri Panchul's notes 1-5)."""


def _holes(x0, x1, y, step=16, r=2.4):
    return "".join(f'<circle class="hole" cx="{x}" cy="{y}" r="{r}"/>' for x in range(x0, x1 + 1, step))


def breadboard(L):
    s = [f'<svg class="fig" viewBox="0 0 820 300" role="img" aria-label="{L["aria"]}">',
         '<rect class="bbody" x="10" y="10" width="540" height="280" rx="10"/>']
    for y, cls in ((34, "rail-n"), (52, "rail-p"), (254, "rail-n"), (272, "rail-p")):
        s.append(f'<line class="{cls}" x1="52" x2="532" y1="{y}" y2="{y}"/>' + _holes(60, 524, y))
    for y, t in ((39, "−"), (57, "+"), (259, "−"), (277, "+")):
        s.append(f'<text class="lbl {"tp" if t == "+" else "tn"}" x="28" y="{y}">{t}</text>')
    for x in range(60, 525, 16):
        s.append(f'<line class="{"strip hi" if x in (124, 140) else "strip"}" x1="{x}" x2="{x}" y1="84" y2="140"/>')
        s.append(f'<line class="{"strip hi" if x == 300 else "strip"}" x1="{x}" x2="{x}" y1="172" y2="228"/>')
        s.append("".join(f'<circle class="hole" cx="{x}" cy="{y}" r="2.4"/>'
                         for y in (84, 98, 112, 126, 140, 172, 186, 200, 214, 228)))
    s.append('<rect class="gap" x="40" y="149" width="500" height="14" rx="3"/>')
    for x, n in ((60, "1"), (124, "5"), (204, "10"), (284, "15"), (364, "20"), (444, "25")):
        s.append(f'<text class="num" x="{x}" y="76" text-anchor="middle">{n}</text>')
    for path, y, k in (("M532,43 L580,43", 38, "rails"), ("M146,112 L580,112", 107, "strip"),
                       ("M540,156 L580,156", 152, "gap"), ("M532,263 L580,263", 258, "split")):
        s.append(f'<path class="lead" d="{path}"/><text class="ann" x="588" y="{y}">{L[k + "1"]}</text>'
                 f'<text class="ann" x="588" y="{y + 18}">{L[k + "2"]}</text>')
    s.append("</svg>")
    return "".join(s)


def first_circuit(L):
    s = [f'<svg class="fig" viewBox="0 0 820 460" role="img" aria-label="{L["aria"]}">',
         '<rect class="bbody" x="60" y="20" width="690" height="290" rx="10"/>']
    for y, cls in ((42, "rail-n"), (58, "rail-p"), (270, "rail-n"), (286, "rail-p")):
        s.append(f'<line class="{cls}" x1="96" x2="728" y1="{y}" y2="{y}"/>' + _holes(104, 728, y))
    for y, t, cls in ((47, "GND", "tn"), (63, "+5V", "tp"), (275, "GND", "tn"), (291, "+5V", "tp")):
        s.append(f'<text class="lbl {cls}" x="758" y="{y}">{t}</text>')
    for y in (88, 102, 116, 130, 144, 174, 188, 202, 216, 230):
        s.append(_holes(104, 728, y, r=2.2))
    s.append('<rect class="gap" x="96" y="152" width="640" height="14" rx="3"/>')
    # power module on the left end, fed from USB
    s.append('<rect class="pwr" x="18" y="26" width="68" height="278" rx="6"/>'
             f'<text class="pwrt" transform="translate(56,165) rotate(-90)" text-anchor="middle">{L["pwr"]}</text>'
             '<path class="cable" d="M18,220 C0,230 0,260 6,322"/>'
             f'<text class="ann" x="4" y="342">{L["usb"]}</text>')
    # 14-pin DIP across the gap: pins 1-7 bottom left to right, 14-8 top left to right
    xs = [312 + 16 * i for i in range(7)]
    s.append('<rect class="chip" x="300" y="134" width="120" height="50" rx="3"/>'
             '<path class="notch" d="M300,151 A8,8 0 0 1 300,167"/>')
    for i, x in enumerate(xs):
        s.append(f'<rect class="pin" x="{x - 3}" y="128" width="6" height="7"/>'
                 f'<rect class="pin" x="{x - 3}" y="183" width="6" height="7"/>'
                 f'<text class="pn" x="{x}" y="146" text-anchor="middle">{14 - i}</text>'
                 f'<text class="pn" x="{x}" y="181" text-anchor="middle">{i + 1}</text>')
    s.append('<text class="chipt" x="360" y="164" text-anchor="middle">4081</text>')
    # power jumpers: pin 14 to +5V, pin 7 to GND
    s.append('<path class="w-red" d="M312,88 L312,58"/><circle class="end" cx="312" cy="88" r="3"/>'
             '<circle class="end" cx="312" cy="58" r="3"/>'
             '<path class="w-blk" d="M408,230 L408,270"/><circle class="end" cx="408" cy="230" r="3"/>'
             '<circle class="end" cx="408" cy="270" r="3"/>'
             f'<text class="ann" x="320" y="80">{L["pin14"]}</text>'
             f'<text class="ann" x="416" y="256">{L["pin7"]}</text>')
    # LED: long leg in the pin-3 column, short leg in the GND rail
    s.append('<path class="leg" d="M344,230 L350,243"/><path class="leg" d="M368,270 L360,256"/>'
             '<circle class="ledon" cx="355" cy="250" r="9"/>'
             '<circle class="end" cx="344" cy="230" r="3"/><circle class="end" cx="368" cy="270" r="3"/>')
    # two button modules on male-female jumpers
    for bx, label, pin_x in ((170, "A", 312), (270, "B", 328)):
        s.append(f'<rect class="btnm" x="{bx - 34}" y="360" width="68" height="46" rx="5"/>'
                 f'<circle class="btncap" cx="{bx}" cy="388" r="13"/>'
                 f'<text class="lbl" x="{bx}" y="428" text-anchor="middle">{L["button"]} {label}</text>')
        for dx, t in ((-20, "+"), (0, "OUT"), (20, "−")):
            s.append(f'<text class="pn" x="{bx + dx}" y="372" text-anchor="middle">{t}</text>')
        s.append(f'<path class="w-red" d="M{bx - 20},360 C{bx - 20},330 {bx - 20},320 {bx - 20},286"/>'
                 f'<path class="w-blk" d="M{bx + 20},360 C{bx + 20},330 {bx + 20},310 {bx + 20},270"/>'
                 f'<path class="w-sig" d="M{bx},360 C{bx},310 {pin_x},290 {pin_x},230"/>')
        for x, y in ((bx - 20, 286), (bx + 20, 270), (pin_x, 230)):
            s.append(f'<circle class="end" cx="{x}" cy="{y}" r="3"/>')
    for i, k in enumerate(("mf", "notch", "io", "led")):
        s.append(f'<text class="ann" x="400" y="{352 + 20 * i}">{L[k]}</text>')
    s.append("</svg>")
    return "".join(s)


def led(L):
    return (f'<svg class="fig narrow" viewBox="0 0 260 186" role="img" aria-label="{L["aria"]}">'
            '<path class="ledbody" d="M90,70 a30,30 0 0 1 60,0 v18 h-60 z"/>'
            '<rect class="ledrim" x="84" y="86" width="72" height="8" rx="2"/>'
            '<line class="legb" x1="104" y1="94" x2="104" y2="160"/><line class="legb" x1="136" y1="94" x2="136" y2="135"/>'
            '<text class="lbl tp" x="104" y="180" text-anchor="middle">+</text>'
            '<text class="lbl tn" x="136" y="155" text-anchor="middle">−</text>'
            f'<text class="ann" x="6" y="122">{L["long"]}</text><text class="ann" x="6" y="140">{L["anode"]}</text>'
            f'<text class="ann" x="150" y="112">{L["short"]}</text><text class="ann" x="150" y="130">{L["cathode"]}</text>'
            '</svg>')


LABELS = {
    "en": dict(
        breadboard=dict(aria="Breadboard connections", rails1="Rails: all holes along", rails2="the line are connected",
                        strip1="Each column of 5 holes", strip2="is one connection", gap1="Center gap: put chips",
                        gap2="across it", split1="Some boards split the", split2="rails in the middle"),
        circuit=dict(aria="First circuit: 4081 chip, two buttons and an LED", pwr="POWER MODULE · 5V",
                     usb="USB / 9V USB-DC", pin14="pin 14 → +5V", pin7="pin 7 → GND", led="LED: long leg in the pin 3 column, short leg in GND",
                     button="button", mf="Buttons: male-female jumpers, + / OUT / −",
                     notch="Notch on the left: pin 1 is bottom-left", io="Pins 1, 2 = inputs A, B · pin 3 = output Y"),
        led=dict(aria="LED legs", long="long leg", anode="anode → +5V", short="short leg", cathode="cathode → GND"),
    ),
    "ru": dict(
        breadboard=dict(aria="Соединения макетной платы", rails1="Шины питания: все", rails2="отверстия вдоль линии",
                        strip1="Столбик из 5 отверстий", strip2="соединён внутри", gap1="Канавка посередине:",
                        gap2="чип ставится поперёк", split1="На некоторых платах", split2="шины разрезаны пополам"),
        circuit=dict(aria="Первая схема: чип 4081, две кнопки и светодиод", pwr="БЛОК ПИТАНИЯ · 5V",
                     usb="USB / USB-DC 9V", pin14="ножка 14 → +5V", pin7="ножка 7 → GND",
                     led="Светодиод: длинная ножка у ножки 3, короткая в GND", button="кнопка", mf="Кнопки: перемычки папа-мама, + / OUT / −",
                     notch="Полукруг слева: ножка 1 внизу слева", io="Ножки 1, 2 = входы A, B · ножка 3 = выход Y"),
        led=dict(aria="Ножки светодиода", long="длинная ножка", anode="анод → +5V", short="короткая ножка",
                 cathode="катод → GND"),
    ),
}

CSS = """
svg.fig{width:100%;height:auto;display:block;margin:12px 0}
svg.fig.narrow{max-width:300px}
svg .bbody{fill:var(--card);stroke:var(--line);stroke-width:2}
svg .gap{fill:var(--th)}
svg .hole{fill:var(--muted);opacity:.55}
svg .rail-p{stroke:#d64541;stroke-width:7;opacity:.35;stroke-linecap:round}
svg .rail-n{stroke:#2f6fd0;stroke-width:7;opacity:.35;stroke-linecap:round}
svg .strip{stroke:var(--line);stroke-width:7;stroke-linecap:round}
svg .strip.hi{stroke:var(--accent);opacity:.55}
svg text{fill:var(--fg);font-family:system-ui,sans-serif}
svg .lbl{font-size:16px;font-weight:700}svg .tp{fill:#d64541}svg .tn{fill:#2f6fd0}
svg .num{font-size:11px;fill:var(--muted)}
svg .ann{font-size:14px;fill:var(--muted)}
svg .lead{stroke:var(--muted);stroke-dasharray:3 3;fill:none}
svg .pwr{fill:#2f6fd0;opacity:.85}svg .pwrt{fill:#fff;font-size:13px;font-weight:600}
svg .cable{stroke:var(--muted);stroke-width:5;fill:none;stroke-linecap:round}
svg .chip{fill:#2b2f33}svg .notch{fill:var(--card)}svg .pin{fill:#b9bec3}
svg .pn{font-size:10px;fill:#e4e8eb;font-weight:600}
svg .chipt{fill:#fff;font-size:13px;font-weight:700}
svg .w-red,svg .w-blk,svg .w-sig{fill:none;stroke-width:4;stroke-linecap:round}
svg .w-red{stroke:#d64541}svg .w-blk{stroke:#3a3f44}svg .w-sig{stroke:#e0a100}
svg .end{fill:var(--fg)}
svg .leg,svg .legb{stroke:#9aa3ab;stroke-width:3;fill:none}
svg .ledon{fill:#f2c200;stroke:#c99f00;stroke-width:2}
svg .ledbody{fill:#9bd36a;stroke:#5f9a35;stroke-width:2}svg .ledrim{fill:#5f9a35}
svg .btnm{fill:#2f6fd0}svg .btncap{fill:#e2453c;stroke:#a82d27;stroke-width:2}
"""


def fragments(lang):
    L = LABELS[lang]
    return {"svg_breadboard": breadboard(L["breadboard"]), "svg_circuit": first_circuit(L["circuit"]),
            "svg_led": led(L["led"])}
