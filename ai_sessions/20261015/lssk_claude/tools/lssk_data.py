"""Data for the Logic Synthesis School Kit (LSSK) exercise list and kits.

Prices and supplier links come from the LSSK tab of the components
spreadsheet (snapshot 2026-10-14):
https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8

Exercises come from
  * "An improved way of teaching school kids digital electronics using
    venerable small-scale integration ICs" (verilog-meetup.com, 2026-07-31),
  * "A prequel to FPGA and ASIC design using small-scale integration chips"
    (verilog-meetup.com, 2026-07-23),
  * Habr article 1071736, section 1 (lessons 1.1-1.7),
  * "Teaching children electronics is due for a major redesign" (Google doc).
"""

SHEET_URL = "https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit?usp=sharing"
JULY31_URL = "https://verilog-meetup.com/2026/07/31/an-improved-way-of-teaching-school-kids-digital-electronics-using-venerable-small-scale-integration-ics/"
JULY23_URL = "https://verilog-meetup.com/2026/07/23/a-prequel-to-fpga-and-asic-design-using-small-scale-integration-chips/"
HABR_URL = "https://habr.com/en/articles/1071736/"
DOC_URL = "https://docs.google.com/document/d/1lVcfQOqSg-6YrX_VTWy0q345JGLUEWaLRE-17egVzpo/edit?usp=sharing"

ELEXP = "Elexp (elexp.com)"
JAMECO = "Jameco (jameco.com)"
FUTURLEC = "Futurlec (futurlec.com)"
ALI = "https://www.aliexpress.us/item/"

# key: (category, name, description, unit price USD, supplier or URL, sheet "Quantity all")
CATALOG = {
    # Basic gates
    "4081": ("IC", "CD4081", "Quad 2-input AND", 0.55, ELEXP, 2),
    "4071": ("IC", "CD4071", "Quad 2-input OR", 0.25, ELEXP, 2),
    "4069": ("IC", "CD4069", "Hex inverter (NOT)", 0.30, ELEXP, 2),
    "4070": ("IC", "CD4070", "Quad 2-input XOR", 0.45, ELEXP, 2),
    "4073": ("IC", "CD4073", "Triple 3-input AND", 0.45, ELEXP, 2),
    "4082": ("IC", "CD4082", "Dual 4-input AND", 0.35, ELEXP, 2),
    "4011": ("IC", "CD4011", "Quad 2-input NAND", 0.35, ELEXP, 2),
    "4012": ("IC", "CD4012", "Dual 4-input NAND", 0.30, ELEXP, 2),
    "4023": ("IC", "CD4023", "Triple 3-input NAND", 0.30, ELEXP, 2),
    "4068": ("IC", "CD4068", "8-input AND/NAND", 0.39, ELEXP, 2),
    "4001": ("IC", "CD4001", "Quad 2-input NOR", 0.30, ELEXP, 2),
    "4002": ("IC", "CD4002", "Dual 4-input NOR", 0.25, ELEXP, 2),
    "4025": ("IC", "CD4025", "Triple 3-input NOR", 0.35, ELEXP, 2),
    "4078": ("IC", "CD4078", "8-input OR/NOR", 0.32, ELEXP, 2),
    "4072": ("IC", "CD4072", "Dual 4-input OR", 0.25, ELEXP, 2),
    "4075": ("IC", "CD4075", "Triple 3-input OR", 0.25, FUTURLEC, 2),
    "4077": ("IC", "CD4077", "Quad 2-input XNOR (the sheet says 3-input; the 4077 is 2-input)", 0.30, FUTURLEC, 2),
    # Flip-flops, registers, counters
    "4013": ("IC", "CD4013", "Dual D flip-flop with set/reset", 0.35, ELEXP, 1),
    "40174": ("IC", "CD40174", "Hex D flip-flop with common clock and clear", 0.58, ELEXP, 2),
    "4076": ("IC", "CD4076", "4-bit D register with 3-state outputs", 0.19, JAMECO, 2),
    "4029": ("IC", "CD4029", "Presettable up/down binary/BCD counter", 0.80, ELEXP, 1),
    "4015": ("IC", "CD4015", "Dual 4-bit serial-in/parallel-out shift register", 0.35, ELEXP, 1),
    "4014": ("IC", "CD4014", "8-stage parallel-in/serial-out shift register", 0.19, JAMECO, 2),
    "4017": ("IC", "CD4017", "Decade counter with 10 decoded outputs", 0.40, ELEXP, 1),
    # Arithmetic and building blocks
    "4008": ("IC", "CD4008", "4-bit full adder", 1.00, "https://leeselectronic.com/en/product/7192-7192ICCMOS40084BITADDER.html", 1),
    "4032": ("IC", "CD4032", "Triple serial adder", 0.31, "https://store.comet.bg/en/Catalogue/Product/187/", 1),
    "4063": ("IC", "CD4063", "4-bit magnitude comparator", 0.30, FUTURLEC, 1),
    "4048": ("IC", "CD4048", "Multifunction expandable 8-input gate", 0.55, "https://www.ti.com/product/CD4048B", 1),
    "4051": ("IC", "CD4051", "8-channel analog multiplexer/demultiplexer", 0.45, ELEXP, 1),
    "4052": ("IC", "CD4052", "Dual 4-channel analog multiplexer/demultiplexer", 0.45, ELEXP, 1),
    "4053": ("IC", "CD4053", "Triple 2-channel analog multiplexer/demultiplexer", 0.45, ELEXP, 1),
    "4019": ("IC", "CD4019", "Quad AND/OR select gate", 0.40, ELEXP, 1),
    "4028": ("IC", "CD4028", "BCD-to-decimal decoder", 0.35, ELEXP, 1),
    "4555": ("IC", "CD4555", "Dual binary 1-of-4 decoder/demultiplexer", 0.29, "Jameco / Futurlec", 1),
    "4086": ("IC", "CD4086", "Expandable 4-wide 2-input AND-OR-INVERT gate", 0.70, FUTURLEC, 1),
    "4532": ("IC", "CD4532", "8-to-3 priority encoder", 0.60, "https://www.elexp.com/products/10cd4532logic-cmos-8-bit-priority-en", 1),
    "40105": ("IC", "CD74HC40105", "4-bit x 16-word FIFO", 1.74, "https://www.ti.com/product/CD74HC40105/part-details/CD74HC40105E", 1),
    "40108": ("IC", "CD40108", "4x4 multiport register file (hard to find)", 28.84, "https://www.electronicplus.com/", 0),
    "40181": ("IC", "CD40181", "4-bit ALU (hard to find)", 19.78, "https://www.electronicplus.com/", 0),
    # Display
    "4511": ("IC", "CD4511", "BCD-to-7-segment latch/decoder/driver", 0.65, ELEXP, 3),
    "hexdec": ("IC", "HEX decoder", "HEX-to-7-segment latch/decoder/driver (shows A-F too; Habr 1.2 suggests DM9368)", 2.29, ALI + "2255801090867335.html", 3),
    "disp_g": ("Display", "7-segment, green", "Common-cathode single-digit 7-segment display, green", 0.90, "https://www.elexp.com/products/08fndgrcc7-segment-display-c-c-green-c", 2),
    "disp_r": ("Display", "7-segment, red", "Common-cathode single-digit 7-segment display, red", 0.90, "https://www.elexp.com/products/08fnd5007-segment-display-c-c-red-char", 1),
    "res": ("Display", "Resistor 560 Ω ½ W", "Segment resistor for 7-segment displays (½ W leads fit breadboard holes best)", 0.04, "https://www.elexp.com/products/13-55560res-1-2-w-5-560-ohm", 30),
    # LEDs and inputs
    "led_r": ("LED", "5V LED, red", "5V-tolerant LED with built-in current limiting, red", 0.45, "https://www.elexp.com/products/08li3330-hv5high-voltage-leds-5v-red", 0),
    "led_g": ("LED", "5V LED, green", "5V-tolerant LED with built-in current limiting, green", 0.45, "https://www.elexp.com/products/08lg3330-hv5high-voltage-leds-5v-green", 0),
    "led_y": ("LED", "5V LED, yellow", "5V-tolerant LED with built-in current limiting, yellow", 0.45, "https://www.elexp.com/products/08ly3330-hv5high-voltage-leds-5v-yellow", 0),
    "ledmod_b": ("LED", "8-LED module, blue", "8-LED bar module, common GND, no resistors needed (bulk of 20 price)", 0.38, ALI + "3256804380748521.html", 1),
    "ledmod_r": ("LED", "8-LED module, red", "8-LED bar module, common GND, no resistors needed (bulk of 20 price)", 0.38, ALI + "3256804380748521.html", 1),
    "traffic": ("LED", "Traffic-light LED module", "Red/yellow/green LED module, 5V version (not the 1V one)", 0.40, ALI + "3256806333906622.html", 1),
    "btn5a": ("Input", "Buttons, 5 pcs", "5 button modules 12x12 mm with built-in pull-down resistor (VCC / OUT / GND)", 0.66, ALI + "3256806475044826.html", 1),
    "btn5b": ("Input", "Buttons, 5 pcs (2nd pack)", "5 button modules 12x12 mm with built-in pull-down; needed for adder and comparator exercises", 2.03, ALI + "3256803953260036.html", 1),
    "touch4": ("Input", "4-button module with LEDs", "4 buttons touch button module with hat and LED indicator (check output polarity)", 2.09, ALI + "3256810032908986.html", 0),
    "keypad8": ("Input", "2x4 keypad", "2x4 keypad, 8 push buttons", 0.96, ALI + "3256809059002407.html", 0),
    "kbd8": ("Input", "8-button keyboard module", "8-button keyboard module with LED indicator", 1.19, ALI + "3256808344487487.html", 0),
    "clk": ("Clock", "555 clock module", "Assembled 555 clock generator module, blue (set to ~0.5-1 Hz)", 0.53, ALI + "3256809517040635.html", 1),
    # Power
    "psu": ("Power", "Breadboard power module", "MB102-style breadboard power supply module; set the jumpers to 5V", 1.00, ALI + "2251832530395866.html", 1),
    "usbdc9": ("Power", "USB-to-DC cable 9V", "USB-to-DC barrel cable with 9V boost; the module regulates it to a stable 5V", 1.17, ALI + "3256806703746727.html", 1),
    "jack": ("Power", "DC barrel jack, breadboard", "Breadboard-friendly 2.1 mm DC jack; use only with the 5V USB-to-DC cable", 1.10, "https://www.amazon.com/dp/B074LK7G86", 0),
    "usbdc5": ("Power", "USB-to-DC cable 5V", "USB-to-DC cable, 5V; only for the DC-jack option (gives ~3.5V through the power module)", 0.84, ALI + "3256806703746727.html", 0),
    "bat_adapter": ("Power", "9V battery clip to DC", "9V battery to DC plug adapter, for demos away from USB", 0.59, "https://www.amazon.com/dp/B09L858G5T", 0),
    "bat9": ("Power", "9V battery", "9V battery, for demos away from USB", 0.67, "", 0),
    # Breadboards, wires, tools
    "bb": ("Breadboard", "Breadboard 830", "Solderless breadboard, 830 points (EL-CP-003)", 3.00, "https://www.amazon.com/EL-CP-003-Breadboard-Solderless-Distribution-Connecting/dp/B01EV6LJ7G", 0),
    "bb_set": ("Breadboard", "Breadboard set 2+2", "Breadboard set: 2 large (830) + 2 small", 7.99, "https://www.amazon.com/dp/B08115P2T4", 1),
    "mm40": ("Wires", "Dupont M-M x40", "40 male-male Dupont jumpers, 10 or 15 cm", 1.30, ALI + "3256805315188857.html", 1),
    "mf40": ("Wires", "Dupont M-F x40", "40 male-female Dupont jumpers, 10 or 15 cm (button and clock modules)", 1.30, ALI + "3256805315188857.html", 1),
    "wire350": ("Wires", "Pre-cut jumper wires x350", "Jameco ValuePro 350-piece pre-formed 22 AWG wire jumpers, 14 lengths", 11.95, "https://www.jameco.com/z/WJW-60P-R-Jameco-ValuePro-350-pc-Wire-Jumper-Refill-for-Part-Number-19290-14-Lengths-10-Colors-25-of-Each-Length_20080.html", 1),
    "ic_extractor": ("Tool", "IC extractor", "IC extractor with insulated handle", 1.20, "https://www.elexp.com/products/060404ic-extractor-insulated-handle", 1),
    "pin_straightener": ("Tool", "IC pin straightener", "IC pin straightener", 8.95, "https://www.elexp.com/products/03ics-01ic-pin-straightener", 1),
}

SECTIONS = [
    ("G", "Getting started"),
    ("B", "Basics"),
    ("BB", "Building blocks"),
    ("M", "Mini-projects"),
    ("P", "Projects"),
]

J31 = "July 31 post"
HB = "Habr"
NOTES = "Notes 1-5 (July 23 post)"
DOC = "Doc"

# Generic requirement keys used in exercises:
#   btn - button modules, ledmod - 8-LED modules, disp - 7-segment displays,
#   res - 560 Ohm resistors, clk - 555 clock module, bb - 830-point breadboards,
#   traffic - traffic-light LED module, led_r/led_g/led_y - single 5V LEDs.
# Wires: w = pre-cut wires on the breadboard (incl. power and tie-offs of unused
# CMOS inputs), mf = male-female Dupont (button and clock modules, 3 each),
# mm = male-male Dupont (rails between breadboards).
EXERCISES = [
    dict(id="G1", title="Getting started: breadboard, power, 5V LEDs, a gate chip and buttons",
         sources=[NOTES, HB + " 1.1"],
         text="Learn how the breadboard is connected inside, power it from the breadboard power module "
              "(jumpers at 5V, 9V USB-to-DC cable), light a 5V-tolerant LED straight from the rails, plug in "
              "the 8-LED module, insert a 4081, 4071 or 4070 chip, drive two inputs from button modules and "
              "watch the output LED.",
         parts={"4081": 1, "btn": 2, "led_g": 1, "ledmod": 1, "bb": 1},
         alts="Any of 4081 / 4071 / 4070 works for the first chip.",
         w=10, mf=6, mm=0, wb="2 chip power, 6 tie-offs, 2 LED module"),
    dict(id="B1", title="Demo the basic gates 4081 (AND), 4071 (OR), 4069 (NOT), 4070 (XOR)",
         sources=[J31 + ": Basics", HB + " 1.1"],
         text="One chip at a time: drive one gate from two buttons, show the output on an LED and write the "
              "truth table.",
         parts={"4081": 1, "4071": 1, "4069": 1, "4070": 1, "btn": 2, "led_g": 1, "bb": 1},
         one_at_a_time=True,
         w=8, mf=6, mm=0, wb="2 power, 6 tie-offs of the unused gate inputs (4069: 5)"),
    dict(id="B2", title="De Morgan's laws",
         sources=[HB + " 1.1"],
         text="Build both sides of ~(A & B) == ~A | ~B and of ~(A | B) == ~A & ~B and compare the two "
              "LEDs for all four input combinations. In a class, half of the students get 4081, half get "
              "4071, and everybody gets 4069. These laws are used later in the FSM exercises.",
         parts={"4081": 1, "4071": 1, "4069": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=29, mf=6, mm=0, wb="6 power, 5 signal, 15 tie-offs, 3 LED module"),
    dict(id="B3", title="Explore a gate chip from its datasheet",
         sources=[HB + " 1.1"],
         text="Each student gets one chip and its datasheet, describes its function in words (for NOR: "
              "'1 only when all inputs are 0') and writes the truth table. Chips: 4073, 4082, 4011, 4012, "
              "4023, 4068, 4001, 4002, 4025, 4078, 4072, 4075, 4077. For the 8-input gates, drive 4 inputs "
              "from buttons and the rest from wires plugged into +5V/GND. Can be homework.",
         parts={"4073": 1, "4082": 1, "4011": 1, "4012": 1, "4023": 1, "4068": 1, "4001": 1, "4002": 1,
                "4025": 1, "4078": 1, "4072": 1, "4075": 1, "4077": 1, "btn": 4, "led_g": 1, "bb": 1},
         one_at_a_time=True,
         w=8, mf=12, mm=0, wb="2 power, up to 6 tie-offs or input wires"),
    dict(id="B4", title="4013 D flip-flop with asynchronous reset",
         sources=[J31 + ": Basics", HB + " 1.3", DOC + " pic. 5"],
         text="Clock the flip-flop from the assembled 555 module at about 0.5-1 Hz. Show CLK, D and Q on "
              "LEDs, see that changes of D inside the clock period are ignored and only the value at the "
              "rising edge is stored. Use the reset button to clear Q asynchronously.",
         parts={"4013": 1, "clk": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=12, mf=9, mm=0, wb="2 power, 1 SET tie, 4 tie-offs of the 2nd flip-flop, 1 clock, 4 LED module"),
    dict(id="B5", title="4029 up/down binary/BCD counter",
         sources=[J31 + ": Basics", HB + " 1.3"],
         text="Count clock pulses from the 555 module, switch up/down and binary/decimal with buttons, "
              "show Q1-Q4 and carry-out on the LED array.",
         parts={"4029": 1, "clk": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=15, mf=9, mm=0, wb="2 power, PE and CARRY-IN ties, 4 preset-input ties, 1 clock, 6 LED module"),
    dict(id="B6", title="4015 serial-in / parallel-out shift register",
         sources=[J31 + ": Basics", HB + " 1.3"],
         text="Shift the bit from a button into the register on every clock and show the whole state on the "
              "LED array. Cascade both 4-bit halves to get 8 bits.",
         parts={"4015": 1, "clk": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=15, mf=9, mm=0, wb="2 power, 2 clock, 1 cascade, 1 reset, 9 LED module"),
    dict(id="B7", title="Seven-segment display and the 4511 decoder",
         sources=[J31 + ": Basics", HB + " 1.2"],
         text="First connect the common cathode to GND through a 560 Ω resistor and light each segment by "
              "touching its pin with a wire from +5V. Then drive the display from a 4511 with a BCD code from "
              "four buttons, one 560 Ω ½ W resistor per segment.",
         parts={"4511": 1, "disp": 1, "res": 8, "btn": 4, "bb": 1},
         w=13, mf=12, mm=0, wb="2 power, 3 control ties (LT, BI, LE), ~5 routing to the display, 1 cathode, 2 probe"),
    dict(id="B8", title="4008 4-bit adder with buttons and the LED array",
         sources=[HB + " 1.2", J31 + ": Basics"],
         text="Treat the adder as a black box: enter A and B with buttons (or wires into +5V/GND) and read "
              "the sum and carry on the LED array. Practice binary numbers.",
         parts={"4008": 1, "btn": 8, "ledmod": 1, "bb": 1},
         w=9, mf=24, mm=0, wb="2 power, 1 carry-in tie, 6 LED module"),
    dict(id="B9", title="4008 adder with three 4511 decoders and three displays",
         sources=[J31 + ": Basics", HB + " 1.2", DOC + " pic. 12-13"],
         text="Show A, B and the sum in decimal on three 7-segment displays, the carry on a decimal point. "
              "The 4511 shows only 0-9 (10-15 are blank), so keep the sum at 9 or below, or use the HEX "
              "decoder (DM9368) if available.",
         parts={"4008": 1, "4511": 3, "disp": 3, "res": 22, "btn": 8, "bb": 2},
         w=49, mf=24, mm=4, wb="3 for the 4008; 3 x 15 for each 4511 + display (power, ties, data, routing, cathode); 1 carry to DP"),

    dict(id="BB1", title="4048 reconfigurable 8-input gate",
         sources=[J31 + ": Building blocks", HB + " 1.6"],
         text="Select the function (NOR, OR, AND, NAND, OR/AND, ...) with the Ka/Kb/Kc pins and check the "
              "truth table.",
         parts={"4048": 1, "btn": 4, "led_g": 1, "bb": 1},
         w=11, mf=12, mm=0, wb="2 power, 3 function-select wires, Kd and EXPAND ties, 4 input wires"),
    dict(id="BB2", title="4014 parallel-in / serial-out shift register",
         sources=[J31 + ": Building blocks", HB + " 1.4"],
         text="Load a parallel value with the LOAD button, then watch it come out bit by bit at Q8 on every "
              "clock. This is the serializer used later in the bit-serial adder.",
         parts={"4014": 1, "clk": 1, "btn": 5, "ledmod": 1, "bb": 1},
         w=12, mf=18, mm=0, wb="2 power, 4 parallel-input wires, 1 serial-in tie, 1 clock, 4 LED module"),
    dict(id="BB3", title="4063 4-bit magnitude comparator",
         sources=[J31 + ": Building blocks", HB + " 1.6"],
         text="Compare two 4-bit numbers from buttons and show A<B, A=B, A>B on the traffic-light LED.",
         parts={"4063": 1, "btn": 8, "traffic": 1, "bb": 1},
         w=9, mf=24, mm=0, wb="2 power, 3 cascade-input ties, 4 traffic light"),
    dict(id="BB4", title="Multiplexers 4051, 4052, 4053, 4019",
         sources=[J31 + ": Building blocks", HB + " 1.6"],
         text="Set the data inputs with wires into +5V/GND, change the select inputs with buttons and watch "
              "the output LED. 4051-4053 are analog switches: the output floats when INH = 1.",
         parts={"4051": 1, "4052": 1, "4053": 1, "4019": 1, "btn": 3, "ledmod": 1, "bb": 1},
         one_at_a_time=True,
         w=15, mf=9, mm=0, wb="worst case 4019: 2 power, 8 data wires, 5 LED module"),
    dict(id="BB5", title="4028 BCD-to-decimal decoder",
         sources=[J31 + ": Building blocks", HB + " 1.6"],
         text="Enter a BCD code with four buttons and see exactly one of the ten outputs light. The decoder "
              "is reused later to build multiplexers from a decoder and a selector.",
         parts={"4028": 1, "btn": 4, "ledmod": 2, "bb": 1},
         w=14, mf=12, mm=0, wb="2 power, 10 outputs, 2 LED module GND"),
    dict(id="BB6", title="4532 8-to-3 priority encoder with a 4511 display",
         sources=[J31 + ": Building blocks", HB + " 1.6"],
         text="Press several of the eight buttons and see the number of the highest one on the 7-segment "
              "display; GS and EO on LEDs.",
         parts={"4532": 1, "4511": 1, "disp": 1, "res": 7, "btn": 8, "ledmod": 1, "bb": 1},
         w=21, mf=24, mm=0, wb="2 power, 1 EI tie, 3 LED; 4511 block 15"),
    dict(id="BB7", title="4017 decade counter with decoded outputs",
         sources=[J31 + ": Building blocks", HB + " 1.6"],
         text="Watch the single running light over Q0-Q9. Inside, the 4017 is a 5-stage Johnson counter "
              "with decoding; compare it with M10.",
         parts={"4017": 1, "clk": 1, "btn": 1, "ledmod": 2, "bb": 1},
         w=17, mf=6, mm=0, wb="2 power, 1 clock, 1 CLK INH tie, 11 outputs, 2 LED module GND"),
    dict(id="BB8", title="40105 FIFO demo",
         sources=[J31 + ": Building blocks", HB + " 1.5", DOC + " pic. 9-10"],
         text="Push 3-bit numbers from three data buttons, pop them in the same order, and watch DOR "
              "(data-out ready) and the head of the queue on the LED module. SI loads a word on its rising "
              "edge and SO drops one on its falling edge, so the push and pop buttons go through the two "
              "flip-flops of a 4013: every press gives one clean edge in step with the clock, even when the "
              "button bounces. This is stage 1 of the FIFO build guide.",
         parts={"40105": 1, "4013": 1, "clk": 1, "btn": 6, "ledmod": 1, "bb": 2},
         guide="fifo_build.html",
         w=19, mf=21, mm=4, wb="stage 1 of the build guide: 4 power, 4 tie-offs, 1 LED module GND, 9 signals, "
                               "1 temporary; 4 rail jumpers to the second board"),
    dict(id="BB9", title="40108 4x4 register file",
         sources=[J31 + ": Building blocks", HB + " 1.6"],
         text="Write 4-bit words to four addresses and read them back. The 40108 is hard to find and "
              "expensive.",
         parts={"40108": 1, "clk": 1, "btn": 7, "ledmod": 1, "bb": 1},
         rare=True,
         w=19, mf=24, mm=0, wb="2 power, 4 address wires, 3 enable ties, 1 clock, 9 LED module"),
    dict(id="BB10", title="40181 4-bit ALU",
         sources=[J31 + ": Building blocks", HB + " 1.6", DOC + " pic. 11"],
         text="As in Svetlana Mosyagina's demo: A and B from eight buttons, a mode button switches between "
              "addition (S = 1001) and subtraction (S = 0110) through a 4069 inverter, the result goes to "
              "the LED array. The 40181 is hard to find and expensive.",
         parts={"40181": 1, "4069": 1, "btn": 9, "ledmod": 1, "bb": 1},
         rare=True,
         w=23, mf=27, mm=0, wb="4 power, M tie, 6 mode wiring, 5 inverter tie-offs, 7 LED module"),

    dict(id="M1", title="Half adder from XOR and AND",
         sources=[HB + " 1.4"],
         text="Sum = A ^ B, carry = A & B.",
         parts={"4070": 1, "4081": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=21, mf=6, mm=0, wb="4 power, 2 fan-out, 12 tie-offs, 3 LED module"),
    dict(id="M2", title="Full adder from basic gates",
         sources=[J31 + ": Mini-projects", HB + " 1.4"],
         text="Sum = A ^ B ^ Cin, Cout = A & B | Cin & (A ^ B).",
         parts={"4070": 1, "4081": 1, "4071": 1, "btn": 3, "ledmod": 1, "bb": 1},
         w=30, mf=9, mm=0, wb="6 power, 7 signal, 14 tie-offs, 3 LED module"),
    dict(id="M3", title="2-bit adder from a half adder and a full adder",
         sources=[J31 + ": Mini-projects"],
         text="Bit 0: half adder, bit 1: full adder; three result bits on the LED array.",
         parts={"4070": 1, "4081": 1, "4071": 1, "btn": 4, "ledmod": 1, "bb": 1},
         w=30, mf=12, mm=0, wb="6 power, 10 signal, 10 tie-offs, 4 LED module"),
    dict(id="M4", title="8-bit adder from two cascaded 4008",
         sources=[HB + " 1.4"],
         text="Connect carry-out of the low 4008 to carry-in of the high one. A from eight buttons, B from "
              "wires into +5V/GND.",
         parts={"4008": 2, "btn": 8, "ledmod": 1, "led_r": 1, "bb": 1},
         w=24, mf=24, mm=0, wb="4 power, 1 cascade, 1 carry-in tie, 8 B-operand wires, 10 LEDs"),
    dict(id="M5", title="8:1 mux from a 4028 decoder and an AND/OR selector (instead of 4051)",
         sources=[J31 + ": Mini-projects", HB + " 1.6"],
         text="The decoder turns the 3-bit select into one-hot; eight ANDs gate the data, an 8-input OR "
              "merges them. Compare with the 4051 from BB4.",
         parts={"4028": 1, "4081": 2, "4078": 1, "btn": 3, "led_g": 1, "bb": 1},
         w=33, mf=9, mm=0, wb="8 power, 1 tie, 8 decoder-to-AND, 8 data, 8 AND-to-OR"),
    dict(id="M6", title="8:1 mux from 4028, two 4086 AND-OR-INVERT and 4069 (instead of 4051)",
         sources=[J31 + ": Mini-projects", HB + " 1.6"],
         text="The inverted output of the first 4086 drives the INHIBIT input of the second one, which "
              "merges all eight terms; a 4069 inverts the final output.",
         parts={"4028": 1, "4086": 2, "4069": 1, "btn": 3, "led_g": 1, "bb": 1},
         w=35, mf=9, mm=0, wb="8 power, 1 tie, 8 decoder, 8 data, 3 expand, 3 enable ties, 4 tie-offs"),
    dict(id="M7", title="Dual 4:1 mux from a 4555 decoder and AND/OR (instead of 4052)",
         sources=[J31 + ": Mini-projects", HB + " 1.6"],
         text="One half of the 4555 decodes the select; eight ANDs and two 4-input ORs form two channels.",
         parts={"4555": 1, "4081": 2, "4072": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=37, mf=6, mm=0, wb="8 power, 4 decoder ties, 8 decoder, 8 data, 8 AND-to-OR, 1 LED GND"),
    dict(id="M8", title="Dual 4:1 mux from 4555, 4086 and 4069 (instead of 4052)",
         sources=[J31 + ": Mini-projects", HB + " 1.6"],
         text="Each channel is one 4-wide AND-OR-INVERT plus an inverter.",
         parts={"4555": 1, "4086": 2, "4069": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=39, mf=6, mm=0, wb="8 power, 4 decoder ties, 8 decoder, 8 data, 4 AOI ties, 2 inverter, 4 tie-offs, 1 LED"),
    dict(id="M9", title="4019 bit-mask merge vs the same function from basic gates",
         sources=[J31 + ": Mini-projects", HB + " 1.6"],
         text="D = A & KA | B & KB for 4 bits: build it with 4019, then with 2 x 4081 + 4071, and show both "
              "results side by side on the LED array.",
         parts={"4019": 1, "4081": 2, "4071": 1, "btn": 2, "ledmod": 1, "bb": 1},
         w=49, mf=6, mm=0, wb="8 power, 16 data, 8 KA/KB fan-out, 8 AND-to-OR, 9 LED module"),
    dict(id="M10", title="Johnson counter from 4015 and 4069",
         sources=[J31 + ": Mini-projects", HB + " 1.6", "Sheet (4017 row)"],
         text="Feed the inverted last stage back into the shift register. Compare the pattern with the 4017 "
              "decade counter (BB7), which is a Johnson counter inside.",
         parts={"4015": 1, "4069": 1, "clk": 1, "btn": 1, "ledmod": 1, "bb": 1},
         w=25, mf=6, mm=0, wb="4 power, 2 clock, 2 reset, 2 feedback, 1 cascade, 9 LED module, 5 tie-offs"),
    dict(id="M11", title="Traffic-light FSM from a 4017 and OR gates",
         sources=[HB + " 1.7", DOC + " pic. 15"],
         text="As built by Timofei and Nil Nikiforov: red = Q0|Q1|Q2|Q3, yellow = Q4|Q5, "
              "green = Q6|Q7|Q8|Q9; at 1 Hz that is 4 s red, 2 s yellow, 4 s green.",
         parts={"4017": 1, "4072": 1, "4071": 1, "clk": 1, "traffic": 1, "bb": 1},
         w=29, mf=3, mm=0, wb="6 power, 3 control, 10 decoded outputs to ORs, 6 tie-offs, 4 traffic light"),
    dict(id="M12", title="Compare a binary counter with a Johnson counter on the 4063",
         sources=[HB + " 1.6 (Maya Grigoryeva's project)"],
         text="A 4029 counter and a 4015 + 4069 Johnson counter run from one clock; the 4063 compares their "
              "values and shows less / equal / greater on the traffic light.",
         parts={"4063": 1, "4029": 1, "4015": 1, "4069": 1, "clk": 1, "traffic": 1, "bb": 1},
         w=44, mf=3, mm=0, wb="8 power, 11 counter setup, 8 comparator inputs, 3 cascade ties, 9 Johnson wiring, 5 tie-offs"),

    dict(id="P1", title="Bit-serial adder: 4032 with two 4014 serializers, a 4015 deserializer and three displays",
         sources=[J31 + ": Projects", HB + " 1.4", DOC + " pic. 12-14"],
         text="LOAD puts A and B into two 4014 shift registers; on every clock one bit of each goes into "
              "the 4032 serial adder and the sum bit goes into the 4015. Three 4511 + displays show A, B "
              "and the sum. Compare with the combinational 4008. A good group project for 3 students.",
         parts={"4032": 1, "4014": 2, "4015": 1, "4511": 3, "disp": 3, "res": 21, "clk": 1, "btn": 9, "bb": 3},
         w=85, mf=30, mm=4, wb="14 power, 14 serializer wiring and ties, 7 4032 ties, 5 deserializer, 39 displays, 4 clock, 2 load"),
    dict(id="P2", title="Bit-serial adder from basic gates and a D flip-flop for the carry",
         sources=[J31 + ": Projects", HB + " 1.4"],
         text="Replace the 4032 in P1 with the full adder from M2 and a 4013 that stores the carry between "
              "clock cycles. This shows what is inside the 4032.",
         parts={"4014": 2, "4015": 1, "4511": 3, "4070": 1, "4081": 1, "4071": 1, "4013": 1,
                "disp": 3, "res": 21, "clk": 1, "btn": 9, "bb": 3},
         w=110, mf=30, mm=4, wb="P1 minus the 4032 (13) plus the full adder (27) and the carry flip-flop (11)"),
    dict(id="P3", title="FIFO adder: three 40105 FIFOs and a 4008 with backpressure",
         sources=[J31 + ": Projects", HB + " 1.5"],
         text="Operands are pushed into FIFO A and FIFO B in different clock cycles (shared data buttons, "
              "separate push buttons). A 4082 4-input AND decides when to move a pair: A has data (DOR_A), B "
              "has data (DOR_B), C has room (DIR_C) and no transfer is under way. A 4013 flip-flop turns "
              "this into one transfer pulse t: its rising edge loads A + B into C, its falling edge one clock "
              "later pops A and B. A 'pop C' button is the consumer: when it stops, C fills up and backpressure "
              "stalls A and B. Operands are 3 bits wide, so the sum always fits into C. Habr 1.5 notes that "
              "the circuit was not tested yet; the build guide's wiring is checked by a pin-level simulation.",
         parts={"40105": 3, "4008": 1, "4082": 1, "4013": 2, "clk": 1, "btn": 7, "ledmod": 2,
                "led_y": 1, "bb": 2},
         guide="fifo_build.html",
         w=74, mf=24, mm=4, wb="14 power, 16 tie-offs, 42 signals, 2 LED module GND; counted from the build guide"),
    dict(id="P4", title="Round-robin arbiter with 2 requests and 2 grants",
         sources=[HB + " 1.6", DOC + " pic. 6-8, 16"],
         text="A 4013 flip-flop remembers who got the last grant (L = 1: requester 1). "
              "g0 = r0 & ~(r1 & ~L), g1 = r1 & ~(r0 & L), next L = g1 | (L & ~r0). With both requests "
              "held high the grants alternate every clock. Built from 4 chips: two NANDs of a 4011, three "
              "ANDs of a 4081, one OR of a 4071 and a 4013; L & NAND(r0, L) = L & ~r0 saves an inverter.",
         parts={"4081": 1, "4011": 1, "4071": 1, "4013": 1, "clk": 1, "btn": 3, "ledmod": 1, "bb": 1},
         guide="arbiter_build.html",
         w=41, mf=12, mm=0, wb="8 power, 15 signal, 17 tie-offs, 1 LED module GND; counted from the build guide"),
    dict(id="P5", title="FSM that recognizes the sequence 01 (the Harris & Harris snail)",
         sources=[J31 + ": Projects", HB + " 1.7"],
         text="Moore FSM with 3 states in 2 flip-flops: S0' = ~A, S1' = S0 & A, Y = S1. One button is "
              "sampled every clock (0.5-1 Hz).",
         parts={"4013": 1, "4081": 1, "4069": 1, "clk": 1, "btn": 2, "ledmod": 1, "bb": 1},
         alts="The 40174 (hex) or 4076 (4-bit) registers can replace the 4013.", alt_parts=["40174", "4076"],
         w=32, mf=9, mm=0, wb="6 power, 7 logic, 4 clock/reset, 4 LED module, 11 tie-offs"),
    dict(id="P6", title="Your own FSM: recognize a custom button sequence (code lock)",
         sources=[J31 + ": Projects", HB + " 1.7", DOC],
         text="The teacher assigns each student a 3-5-bit sequence, as a detector or as a code lock that "
              "stays open until Reset. The student draws the state diagram, encodes the states, derives the "
              "next-state equations and builds them with gates and a 40174. Solving all 120 tasks with "
              "2-5-bit sequences shows that one task needs up to 3 state flip-flops (+1 to synchronize the "
              "button), up to 8 gate chips and 34-98 wires; the gate assortment below covers every one of "
              "them. The FSM kit page generates the task cards and the answer keys.",
         parts={"40174": 1, "4081": 2, "4073": 2, "4082": 1, "4071": 1, "4075": 1, "4072": 1, "4069": 1,
                "4011": 1, "4001": 1, "clk": 1, "btn": 2, "ledmod": 1, "led_g": 1, "bb": 2},
         alts="4076 or 4013 can replace the 40174.", alt_parts=["4076"],
         w=98, mf=9, mm=0, wb="worst 5-bit task: power, logic, tie-offs, clock/reset and LEDs (typical 5-bit task about 77)"),
    dict(id="P7", title="Bit-serial comparator FSM vs the 4063",
         sources=[J31 + ": Projects", HB + " 1.7"],
         text="Two flip-flops hold GT and LT; every clock takes one bit of A and of B, LSB first: "
              "GT' = A & ~B | GT & (A xnor B), LT' = ~A & B | LT & (A xnor B), EQ = NOR(GT, LT) on the "
              "traffic light. Variants: MSB first, cascaded 4063s, 4 bits per clock. Compare with BB3.",
         parts={"4013": 1, "4081": 1, "4071": 1, "4069": 1, "4077": 1, "4001": 1, "clk": 1, "btn": 3,
                "traffic": 1, "bb": 1},
         w=59, mf=12, mm=0, wb="12 power, 23 signal, 20 tie-offs, 4 traffic light"),
]

# Kits.  `exercises` are the target exercises; part quantities are the maximum
# any single exercise needs (exercises are built one after another).
KITS = [
    dict(id="kit1_basics", n=1, name="Basics kit",
         tagline="The minimum set for the Basics exercises: gates, D flip-flop, counter, shift register, "
                 "7-segment display and the 4008 adder.",
         exercises=["G1", "B1", "B2", "B4", "B5", "B6", "B7", "B8", "B9"],
         optional=[("hexdec", 3, "Instead of 4511: shows 10-15 as A-F"),
                   ("wire350", 1, "Replaces the Dupont M-M jumpers for tidier boards"),
                   ("pin_straightener", 1, "Teacher tool"),
                   ("bat_adapter", 1, "Battery power away from USB"), ("bat9", 1, "Battery power away from USB")],
         packaging=3.00, docs=1.00,
         sheet_column="Quality basics",
         sheet_diff=[
             "The sheet's 'basics' column has one 4511, one display and no 560 Ω resistors; the July 31 "
             "basics list asks for three 4511s and three displays for the 4008 exercise (B9), so this kit "
             "has three, plus the 22 segment resistors they need.",
             "The sheet's column has a 4072 (dual 4-input OR) but no 4071; the exercise list names the 4071, "
             "so this kit has the 4071.",
             "The sheet's column has one breadboard; B9 with three displays does not fit on one 830-point "
             "board, so this kit has two.",
             "A second pack of 5 buttons is added for the 8-input adder (the sheet notes that it is needed "
             "for adder and comparator exercises).",
             "One single 5V-tolerant LED is added for the first 'try it' step of the getting-started notes.",
         ]),
    dict(id="kit2_comprehensive", n=2, name="Comprehensive kit",
         tagline="Everything for all exercises in the list, from the first gate to the bit-serial adder, "
                 "FIFO adder, arbiter and FSMs.",
         exercises=[e["id"] for e in EXERCISES],
         use_sheet_qty=True,
         optional=[("40108", 1, "Only for BB9; hard to find"), ("40181", 1, "Only for BB10; hard to find"),
                   ("hexdec", 3, "Shows 10-15 as A-F instead of a blank 4511 display"),
                   ("touch4", 1, "Data entry for the FIFO exercises"),
                   ("keypad8", 1, "Alternative input"), ("kbd8", 1, "Alternative input"),
                   ("bat_adapter", 1, "Battery power away from USB"), ("bat9", 1, "Battery power away from USB")],
         packaging=6.00, docs=2.00,
         sheet_column="Quantity all",
         sheet_diff=[
             "Two 4008s instead of one (M4, the 8-bit adder, cascades two).",
             "Three 40105s instead of one (P3, the FIFO adder, uses three).",
             "Two 4086s instead of one (M6/M8: an 8-input mux needs two 4-wide AND-OR-INVERT gates).",
             "The HEX decoders, 40108 and 40181 are listed as optional: the 4511 covers the display "
             "exercises, and the two rare chips are only needed for BB9 and BB10.",
             "One more 830-point breadboard: P1 and P2 need three large boards.",
             "Three single 5V-tolerant LEDs (red, green, yellow) for the getting-started notes and the "
             "FIFO status outputs.",
         ]),
    dict(id="kit3_fifo", n=3, name="FIFO kit",
         tagline="A 40105 FIFO demo, then the FIFO adder: three FIFOs, a 4008 and flow control with "
                 "backpressure.",
         exercises=["G1", "BB8", "P3"],
         optional=[("touch4", 1, "4-bit data entry with LED indicators, as in the sheet's FIFO column"),
                   ("4511", 2, "Show FIFO data in decimal"), ("disp_g", 2, "Show FIFO data in decimal"),
                   ("res", 14, "For the two optional displays"),
                   ("pin_straightener", 1, "Teacher tool")],
         packaging=2.50, docs=1.00,
         sheet_column="Quality FIFO",
         sheet_diff=[
             "The sheet's 'FIFO' column has no 40105, no 4008, no clock module and no M-F jumpers for the "
             "buttons; this kit adds all of them.",
             "Two 4013s and a 4082 replace the second 4081: the build guide synchronises the push and pop "
             "buttons with flip-flops and makes the transfer pulse with a flip-flop, because a clock-gated "
             "AND of the ready flags moves several pairs in one clock tick.",
             "The sheet's 2 x 4511 and the 4-button LED module are listed as optional here: LED modules and "
             "button modules are enough for the exercises.",
         ]),
    dict(id="kit4_arbiter", n=4, name="Round-robin arbiter kit",
         tagline="A 2-request, 2-grant round-robin arbiter from four chips: AND, NAND, OR and a D flip-flop.",
         exercises=["G1", "P4"],
         optional=[("4069", 1, "Inverters for alternative designs"),
                   ("traffic", 1, "Show grants and state as traffic lights"),
                   ("wire350", 1, "Replaces the Dupont M-M jumpers for tidier boards"),
                   ("pin_straightener", 1, "Teacher tool")],
         packaging=2.00, docs=1.00),
    dict(id="kit5_fsm", n=5, name="FSM kit",
         tagline="Sequence-recognizing finite state machines: the '01' detector, then a custom code lock "
                 "for each student.",
         exercises=["G1", "P5", "P6"],
         optional=[("4070", 1, "XOR for the bit-serial comparator (P7)"), ("4077", 1, "XNOR for P7"),
                   ("traffic", 1, "Traffic light for P7"),
                   ("4015", 1, "Compare the FSM with a shift-register-and-AND detector"),
                   ("4076", 1, "Alternative state register"),
                   ("pin_straightener", 1, "Teacher tool")],
         packaging=2.50, docs=1.00),
]

# Pricing assumptions (editable on each kit page).
PRICING = dict(
    spares_pct=5,        # breakage and miscounted parts
    inbound_pct=10,      # shipping and duties for parts
    labor_per_line=0.14, # kitting: about 25 s per line item at $20/h
    labor_base=1.00,
    classroom_mult=1.6,  # classroom / bulk price (10+ kits), ~38% gross margin
    retail_mult=2.2,     # direct / retail price, ~55% gross margin
)
