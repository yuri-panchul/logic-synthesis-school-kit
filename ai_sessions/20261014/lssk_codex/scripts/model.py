"""Source-backed inventory and bounded, reusable classroom configurations."""
import json, math
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
ROOT=Path(__file__).resolve().parents[1]
DATE='2026-10-14'
SHEET='https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit'
SOURCES={
 'brief':('Project rationale — Yuri Panchul, September 2026','https://docs.google.com/document/d/1lVcfQOqSg-6YrX_VTWy0q345JGLUEWaLRE-17egVzpo/edit'),
 'prequel':('Illustrated starting notes — 23 July 2026','https://verilog-meetup.com/2026/07/23/a-prequel-to-fpga-and-asic-design-using-small-scale-integration-chips/'),
 'improved':('Exercise list — 31 July 2026','https://verilog-meetup.com/2026/07/31/an-improved-way-of-teaching-school-kids-digital-electronics-using-venerable-small-scale-integration-ics/'),
 'course':('Annual course, breadboard lessons 1.1–1.7 — 22 August 2026','https://habr.com/en/articles/1071736/'),
 'sheet':('LSSK component spreadsheet',SHEET+'?range=LSSK!A1:Q76'),
}
raw=json.loads((ROOT/'research/lssk_rows.json').read_text())
rows={int(next(iter(r)).lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ')):r for r in raw if r}
parts={}
def add(id,name,price,unit='piece',row=None,note='',url='',pack=1,category='LSSK'):
 parts[id]=dict(id=id,name=name,unit=unit,price=str(price),row=row,note=note,url=url,pack=pack,category=category)
for n in range(2,44):
 r=rows[n];num=r.get(f'D{n}','');num=num.removesuffix('.0')
 if n==40:continue
 desc=r.get(f'E{n}','')
 if num=='4077':desc='Quad 2-input XNOR (source typo corrected)'
 if num=='4086':desc='One expandable 4-wide, 2-input AND-OR-INVERT function'
 if num=='4019':desc='Four AND/OR selectors with two shared enables'
 if num=='40105':num='40105';desc='CD74HC40105E, 16 × 4 FIFO, PDIP-16'
 name=desc if num=='40105' else (num if num=='DM9368' else 'CD'+num)+': '+desc
 add(num,name,r[f'J{n}'],row=n,url=r.get(f'Q{n}','') if r.get(f'Q{n}','').startswith('http') else '',note='Historical sheet price; availability unverified.' if num in ['40108','40181','4032','DM9368'] else '')
ids={58:('jack5','Direct 2.1 mm barrel breakout, no regulator; 5 V only'),59:('cable5','USB-to-barrel cable marked 5 V; direct path'),45:('board','Full-size solderless breadboard (830-point class)'),46:('led','5 V current-limited red LED'),49:('display','Common-cathode seven-segment display, green'),51:('r560','560 Ω, 0.5 W resistor'),53:('extractor','Insulated IC extractor'),54:('clock','Assembled 555 clock module, blue'),56:('power','Breadboard regulator module, output set to 5 V'),57:('cable','USB-to-barrel boost cable, marked 9 V'),62:('bar','8-channel 5 V current-limited LED module'),64:('traffic','5 V three-LED traffic-light module'),66:('button','Individual 3-pin button module with embedded pull resistor'),70:('mm','Male–male jumper, 10–15 cm'),71:('mf','Male–female jumper, 10–15 cm')}
for n,(id,name) in ids.items():
 r=rows[n];pack=5 if id=='button' else 40 if id in ['mm','mf'] else 1
 add(id,name,Decimal(r[f'J{n}'])/pack,row=n,url=r.get(f'Q{n}',''),pack=pack,note=('Normalize the $2.03 five-module lot to $0.406/module. Confirm listing supplies modules with resistors, not bare switches.' if id=='button' else 'Normalize the $1.30 pack to $0.0325 per lead.' if id in ['mm','mf'] else ''))
for id,name,price,note,url in [
 ('buffer','SN74HCT244N, octal LED observation buffer, PDIP-20','0.80','Engineering allowance; not in LSSK. One per eight observed logic outputs.','https://www.ti.com/lit/ds/symlink/sn74hct244.pdf'),
 ('schmitt','SN74HCT14N, Schmitt trigger / clock conditioner, PDIP-14','0.60','Engineering allowance; two inverters per non-inverting conditioned signal.','https://www.ti.com/lit/ds/symlink/sn74hct14.pdf'),
 ('c100','100 nF ceramic decoupling capacitor','0.05','One per IC, including support ICs; not listed in LSSK.',''),
 ('c1','1 µF capacitor for button debounce','0.10','One per debounced pushbutton; 100 kΩ × 1 µF = 100 ms nominal.',''),
 ('c10','10 µF, ≥10 V bulk capacitor','0.10','One per breadboard; observe polarity if electrolytic.',''),
 ('r100k','100 kΩ debounce resistor','0.02','Series resistor between button output and RC/Schmitt input.',''),
 ('r2200','2.2 kΩ LED observation resistor','0.02','After HCT buffer; limits output load to <2.3 mA at 5 V even before LED voltage drop.',''),
 ]:add(id,name,price,note=note,url=url,category='Engineering supplement')
E=[]
def ex(id,title,ics,boards,buttons,bars,mm,src,lesson,goal,*,displays=0,clock=False,pulses=0,traffic=0,led=0,note='',status='Estimated build'):
 """mm is a conservative raw wire allowance including support ICs; kit adds 25%."""
 bom=dict(ics)
 bom.update(board=boards,power=1,cable=1,extractor=1)
 for k,v in dict(button=buttons,bar=bars,display=displays,clock=int(clock),traffic=traffic,led=led).items():
  if v:bom[k]=v
 if displays:bom['r560']=7*displays
 channels=8*bars+3*traffic+led
 buffers=math.ceil(channels/8)
 schmitt=math.ceil((2*pulses+2*int(clock))/6)
 if buffers:bom['buffer']=buffers;bom['r2200']=channels
 if schmitt:bom['schmitt']=schmitt
 if pulses:bom['r100k']=pulses;bom['c1']=pulses
 bom['c100']=sum(ics.values())+buffers+schmitt;bom['c10']=boards
 # 3 leads per individual button, 9 per 8-LED bar, 3 for clock, 4 for traffic light.
 mf=3*buttons+9*bars+3*int(clock)+4*traffic
 bom['mm']=mm
 if mf:bom['mf']=mf
 E.append(dict(id=id,title=title,bom=bom,src=src,lesson=lesson,goal=goal,note=note,status=status,pulses=pulses))
B='improved,course'
ex('B01','Power, breadboard, LED and button',{},1,1,0,12,'course','1.1','Identify connected rows and split rails; light the special 5 V LED and measure the button’s idle/pressed levels.',led=1)
for id,n,name in [('B02','4070','XOR'),('B03','4081','AND'),('B04','4071','OR'),('B05','4069','NOT')]:
 ex(id,name+' truth table',{n:1},1,1 if n=='4069' else 2,1,34,B,'Basics / 1.1','Measure every input combination; record the output as 0 or 1.')
ex('B06','Both De Morgan identities',{'4081':1,'4071':1,'4069':1},2,2,1,62,'course','1.1','Compare ¬(A∧B) with ¬A∨¬B, and ¬(A∨B) with ¬A∧¬B. Rewire between the two comparisons.')
ex('B07','D flip-flop with asynchronous reset',{'4013':1},1,2,1,40,B,'Basics / 1.3','Change D between rising clock edges; Q must hold. Reset must clear Q without waiting for a clock.',clock=True)
ex('B08','Binary / BCD up-down counter',{'4029':1},1,2,1,44,B,'Basics / 1.3','Count in both directions; compare binary wrap at 15 with BCD wrap at 9. Preset data uses rail patch leads.',clock=True)
ex('B09','Serial-in, parallel-out register',{'4015':1},1,2,1,44,B,'Basics / 1.3','Cascade the two 4-bit sections; follow a single 1 through eight positions.',clock=True)
ex('B10','Seven-segment exploration and BCD display',{'4511':1},1,4,0,42,B,'Basics / 1.2','Map a–g with one 560 Ω resistor per segment, then show 0–9 using 4511.',displays=1,note='4511 does not display hexadecimal A–F. Tie LE low and lamp-test/blanking inactive for transparent operation.')
ex('B11','4-bit adder with binary output',{'4008':1},1,8,1,44,B,'Basics / 1.2','Enter two 4-bit operands; show four sum bits and carry. Carry-in is tied low.')
ex('B12','4-bit adder with three decimal displays',{'4008':1,'4511':3},3,8,1,100,'improved','Basics','Display A, B and the low four sum bits simultaneously. Use bar channel 0 for carry.',displays=3,note='For readable decimal digits choose A+B ≤9. For larger results inspect the binary LEDs or use the separate DM9368 variant; three 4511s are not a binary-to-decimal converter.')
for i,(chip,arity) in enumerate([('4073',3),('4082',4),('4011',2),('4012',4),('4023',3),('4068',8),('4001',2),('4002',4),('4025',3),('4078',8),('4072',4),('4075',3),('4077',2)],1):
 ex(f'G{i:02}',parts[chip]['name'].split(': ',1)[1]+' investigation',{chip:1},1,arity,1,38,'course','1.1 individual projects','Use the selected gate and its datasheet to predict and check a truth table. Other gates in the same package can remain unused with inputs tied.',note='CD4077 has two inputs per XNOR gate, not three.' if chip=='4077' else '')
ex('A01','Half adder from gates',{'4070':1,'4081':1},1,2,1,44,'course','1.4','Build sum=A XOR B and carry=A AND B; test all four input pairs.')
ex('A02','Full adder from gates',{'4070':1,'4081':1,'4071':1},2,3,1,54,B,'Mini-projects / 1.4','Use two XOR, two AND and one OR gates; verify all eight input triples.')
ex('A03','2-bit adder: half adder plus full adder',{'4070':1,'4081':1,'4071':1},2,4,1,62,'improved','Mini-projects','Use a half adder for bit 0 and a full adder for bit 1. Verify 3+3=110; no external carry-in.')
ex('A04','8-bit parallel adder',{'4008':2},2,0,2,78,'course','1.4 group 2','Cascade carry-out to carry-in. Set sixteen operand bits with rail patch leads; observe 8 sum bits and carry.')
ex('C01','Configurable logic function',{'4048':1},1,8,1,46,B,'Building blocks / 1.6','Patch mode controls to fixed levels, then investigate how the same data inputs implement different functions.')
ex('C02','Parallel-in, serial-out register',{'4014':1},1,2,1,48,B,'Building blocks / 1.4','Patch an 8-bit parallel word, load it on a clock edge, then shift and record the serial sequence.',clock=True)
ex('C03','4-bit magnitude comparator',{'4063':1},1,8,0,44,B,'Building blocks / 1.6','Compare A and B; initialize cascade inputs to equal=1, less=greater=0.',traffic=1)
for id,ch,btn,bars in [('C04','4051',3,1),('C05','4052',2,1),('C06','4053',3,1),('C07','4019',1,1)]:
 ics={ch:1}
 if ch=='4019':ics['4069']=1
 ex(id,ch+' multiplexer',ics,1,btn,bars,46,B,'Building blocks / 1.6','Patch fixed data patterns, vary select inputs and observe selected channels.',note='405x: VEE=GND for 0–5 V signals, INH low. 4019: complementary shared Ka/Kb select all four bits together.')
ex('C08','BCD-to-decimal decoder',{'4028':1},1,4,2,48,B,'Building blocks / 1.6','Observe ten one-hot outputs for inputs 0–9; check the response to 10–15.')
ex('C09','8-to-3 priority encoder with decimal display',{'4532':1,'4511':1},2,8,1,60,B,'Building blocks / 1.6','Assert multiple requests and show the highest selected input number; show valid status separately.',displays=1)
ex('C10','Decoded decade counter',{'4017':1},1,1,2,46,B,'Building blocks / 1.6','Follow the single active output through Q0–Q9; reset to Q0.',clock=True)
ex('C11','Single FIFO: independent enqueue / dequeue',{'40105':1},2,7,1,64,'improved','Building blocks','Buttons: data[3:0], PUSH, POP and RESET. Observe data[3:0], DIR and DOR. Store several words and recover them in order.',pulses=2,note='Selected part is CD74HC40105E: SI loads on rising edge; SO removes on falling edge. Use conditioned PUSH/POP signals. Empty output data are invalid.')
ex('C12','4 × 4 register file',{'40108':1},2,8,1,68,B,'Building blocks / 1.6','Patch addresses and use data/write controls to store and read four independent words.',note='Rare CD40108 required; no substitute silently assumed. Confirm manufacturer pinout and read/write timing before the lesson.',status='Rare part; procurement required')
ex('C13','4-bit ALU',{'40181':1},2,9,1,70,B,'Building blocks / 1.6','Select addition, subtraction and a logic operation. Patch function controls from the actual datasheet; input 8 operand bits plus mode.',note='Rare CD40181 required; a 74LS181 is not an automatic electrical or pin-for-pin substitute.',status='Rare part; procurement required')
ex('M01','4051 replaced by decoder + AND/OR',{'4028':1,'4081':2,'4072':1,'4071':1},2,3,1,88,B,'Mini-projects / 1.6','Tie decoder bit 3 low; gate eight fixed data bits with decoded selects and OR the terms. Compare against C04 by rewiring.')
ex('M02','4051 replaced by decoder + AND-OR-INVERT',{'4028':1,'4086':2,'4069':1,'4071':1},2,3,1,88,B,'Mini-projects / 1.6','Use two four-term 4086 sections, invert each output and OR them. Compare against C04 by rewiring.',note='One 4086 contains one four-term AOI function; an 8:1 replacement needs two. Set each enable high and inhibit low.')
ex('M03','4052 replaced by decoder + AND/OR',{'4555':1,'4081':2,'4072':1},2,2,1,86,B,'Mini-projects / 1.6','Decode the two select bits for two channels. Each channel uses four AND terms and one 4-input OR; compare with C05.')
ex('M04','4052 replaced by decoder + AND-OR-INVERT',{'4555':1,'4086':2,'4069':1},2,2,1,82,B,'Mini-projects / 1.6','Use one 4086 per 4:1 channel and invert both outputs; compare with C05.')
ex('M05','4019 vector selection and gate equivalent',{'4019':1,'4081':2,'4071':1,'4069':1},2,2,1,88,B,'Mini-projects / 1.6','Compare Y=(A AND {4{Ka}}) OR (B AND {4{Kb}}) for two 4-bit vectors, using common enables.',note='The source calls this a bit-mask merge. 4019 has shared enables, not four independent mask bits. For an arbitrary 4-bit mask use the included 8 AND + 4 OR + 4 NOT gates and rail-patched mask bits; one 4019 alone cannot implement that version.')
ex('M06','Johnson counter from shift register',{'4015':1,'4069':1},1,1,1,48,B,'Mini-projects / 1.6','Use four stages with inverted last-stage feedback. Observe eight states; compare with the fixed 10-state CD4017 by rebuilding C10.',clock=True)
serial={'4032':1,'4014':2,'4015':1,'4511':3}
ex('P01','Serial adder with serializers and three displays',serial,4,2,1,150,B,'Projects / 1.4 group 3','Patch two operands; load both 4014s, reset carry, then shift into 4032 and collect the result in 4015. Show three low nibbles through 4511.',displays=3,clock=True,note='Start with operands whose sum is ≤9 for the three decimal displays. Label bit order and count exactly eight shift edges. Carry reset and load timing depend on the 4032/4014 datasheets; prove timing before a class.',status='Timing design; bench verification pending')
ex('P02','Serial adder with discrete carry register',{'4014':2,'4015':1,'4013':1,'4070':1,'4081':1,'4071':1,'4511':3},4,2,1,190,B,'Projects / 1.4','Replace the 4032 of P01 with the A02 full adder and one 4013 for carry; preserve the serializer, output register and displays.',displays=3,clock=True,note='Rising-edge registers capture the pre-edge sum and carry. Reset carry before the first bit; load the serializers separately from the shift phase.',status='Timing design; bench verification pending')
ex('P03','Three-FIFO adder with backpressure',{'40105':3,'4008':1,'4081':2,'4013':1},4,6,3,160,B,'Projects / 1.5','Queue A and B independently, capture their sum in C, then remove the consumed pair. Observe all three data words and six ready flags.',pulses=5,note='Four data patch leads per input word; buttons are PUSH_A, PUSH_B, TRANSFER, POP_C, RESET and ARM/confirm. Stage capture before popping A/B. Result is modulo 16; carry is observed separately and is not queued. Detailed protocol in FIFO kit.',status='Proposed controlled-transfer design; bench verification pending')
ex('P04','Two-request round-robin arbiter',{'4081':1,'4011':1,'4071':1,'4013':1},2,4,1,82,'course','1.6 project 13','Observe requests, grants and priority. A STEP accepts one grant; persistent simultaneous requests must alternate.',clock=True,pulses=1,note='Four core ICs. Button assignments: r0, r1, STEP, RESET. Select STEP or conditioned timer with a patch lead while powered off; never connect the outputs together.')
ex('P05','Sequence recognizer: 01',{'4013':1,'4069':1,'4081':1},2,3,1,66,B,'Projects / 1.7','DATA=pressed 1/released 0; each SAMPLE press records one bit; RESET starts fresh. Store whether the previous bit was 0 and pulse MATCH for a following 1.',pulses=1,note='Reset both seen_zero and MATCH to 0; seen_zero_next=NOT X and match_next=seen_zero AND X. This rejects an initial 1. Both 4013 halves sample the same conditioned edge.')
ex('P06','Custom 2–4 bit sequence FSM',{'40174':1,'4076':1,'4073':3,'4072':3,'4071':1,'4069':1},4,3,1,170,B,'Projects / 1.7','Generate a prefix-state machine for any binary pattern of length 2–4; synthesize the truth table using up to eight 3-input minterms.',pulses=1,note='Use 40174 for two state bits plus registered MATCH. 4076 is included as the source’s alternative register, not connected simultaneously. Three 4073s provide 9 minterms; three 4072s plus one 4071 provide three independent 8-term OR trees. Custom task generator in FSM kit.')
comp={'4013':1,'4069':1,'4070':1,'4081':2,'4071':2,'4063':1}
ex('P07','Bit-serial comparator, least-significant bit first',comp,3,4,1,130,B,'Projects / 1.7','For each new pair, overwrite greater/less on a differing pair, or retain the previous comparison on an equal pair. Reset both flags to 0.',pulses=1,note='Two data buttons, SAMPLE and RESET. Equality = NOT(greater OR less). 4063 is included for a four-bit reference comparison using rail-patched operands.')
ex('P08','Bit-serial comparator, most-significant bit first',comp,3,4,1,130,'course','1.7 variant','Latch the first differing bit pair; ignore later differences. Compare the final flags with 4063 on the same four-bit words.',pulses=1)
ex('P09','Cascaded 8-bit comparator',{'4063':2},2,0,0,70,'course','1.7 variant','Patch sixteen operand bits; cascade from the least-significant nibble to the most-significant comparator.',traffic=1)
ex('P10','FSM comparing one nibble per sample',{'4063':1,'4013':1,'4069':1,'4081':2,'4071':2},3,10,0,132,'course','1.7 variant','Use 4063 for each pair of nibbles and two state bits to remember the first unequal nibble (MS-nibble first). RESET before each word.',pulses=1,traffic=1,note='Data[7:0], SAMPLE and RESET use ten button modules. Least-significant-nibble-first variant overwrites on every unequal nibble.')
ex('P11','Traffic-light FSM: 4 red, 2 yellow, 4 green',{'4017':1,'4072':1,'4071':1},2,1,0,62,'course','1.7','OR Q0–Q3 for red, Q4–Q5 for yellow, Q6–Q9 for green. Count cycles and verify exactly one lamp is lit.',clock=True,traffic=1)
ex('P12','Compare binary and Johnson counter streams',{'4029':1,'4015':1,'4069':1,'4063':1},2,1,1,86,'course','1.6 combined project','Clock a 4-bit binary counter and a 4-stage Johnson counter together; display both vectors and the greater/equal/less comparison.',clock=True,traffic=1)
ex('O01','Hexadecimal display with DM9368',{'4008':1,'DM9368':3},3,8,1,110,'course','1.2 optional alternative','Replace all three BCD display drivers of B12 with separately wired DM9368 drivers to show hexadecimal digits.',displays=3,note='Optional source variant included in Comprehensive. DM9368 has a different pinout, TTL input loading and built-in segment current sources. Use three HCT244 buffers to isolate operand/sum buses; see engineering notes. 560 Ω resistors are reserved for the 4511 version and are not fitted here.',status='Legacy part; bench verification pending')
# DM9368 interface: buffer all 12 data inputs plus LED observers, not just LEDs.
o=E[-1];o['bom']['buffer']+=2;o['bom']['c100']+=2;del o['bom']['r560']
del o['bom']['power'];del o['bom']['cable'];o['bom']['jack5']=1;o['bom']['cable5']=1
# The simple 01 FSM uses two 4013 flops: seen-zero = NOT(DATA), reset 0;
# MATCH is registered from seen-zero AND DATA. This handles initial 1 correctly.
BY_ID={e['id']:e for e in E}
KITS={
 'basics':dict(title='Basics',ids=['B01','B02','B03','B04','B05','B06','B07','B08','B09','B10','B11','B12','A01','A02','A03'],minutes=25,packaging='3.00',description='Every exercise in the July article’s Basics section, including three simultaneous decimal displays, plus De Morgan and gate-level addition.'),
 'comprehensive':dict(title='Comprehensive',ids=[e['id'] for e in E],minutes=60,packaging='6.00',description='All explicitly described breadboard exercises and bounded variants in the two source lists, including rare ICs and the optional hexadecimal display.'),
 'fifo':dict(title='FIFO',ids=['C11','P03'],minutes=35,packaging='4.00',description='A standalone FIFO introduction and the three-FIFO adder with a manually staged, ready-qualified transfer protocol.'),
 'arbiter':dict(title='Two-request round-robin arbiter',ids=['P04'],minutes=25,packaging='3.00',description='A four-core-IC arbiter with requests, grants, retained priority, clean manual STEP and a slow automatic clock.'),
 'fsm':dict(title='FSM and custom sequence tasks',ids=['P05','P06'],minutes=40,packaging='4.00',description='A 01 starter and a configurable, overlapping recognizer for any 2–4 bit binary sequence. Includes an offline task generator.'),
}
def kit_bom(ids):
 b={}
 for id in ids:
  for p,q in BY_ID[id]['bom'].items():b[p]=max(b.get(p,0),q)
 # Rebuild one exercise at a time. Pack rounding on consumables / connector types.
 for p in ('mm','mf'):
  if p in b:b[p]=math.ceil(b[p]*1.25/40)*40
 if 'button' in b:b['button']=math.ceil(b['button']/5)*5
 # Capacitors cover the largest active design, not every stored unused IC.
 if 'c100' in b:b['c100']=math.ceil(b['c100']*1.2)
 return b
D=Decimal
def money(n):return D(n).quantize(D('.01'),rounding=ROUND_HALF_UP)
def cost(bom,kit):
 lines={p:money(D(parts[p]['price'])*q) for p,q in bom.items()}
 materials=sum(lines.values(),D(0))
 freight=money(materials*D('.15'));replacement=money(materials*D('.05'))
 labor=money(D(kit['minutes'])*D(20)/D(60));packaging=D(kit['packaging'])
 loaded=materials+freight+replacement+labor+packaging
 target=loaded/D('.57') # 40% contribution margin after 3% payment fee
 retail=(target/D(5)).to_integral_value(rounding=ROUND_CEILING)*5
 fee=money(retail*D('.03'));contribution=retail-loaded-fee
 return dict(lines=lines,materials=materials,freight=freight,replacement=replacement,labor=labor,packaging=packaging,loaded=loaded,retail=retail,fee=fee,contribution=contribution,margin=money(contribution/retail*100),low=money(materials*D('.75')*D('1.2')+labor+packaging),high=money(materials*D('1.5')*D('1.2')+labor+packaging))
for k,v in KITS.items():v['bom']=kit_bom(v['ids']);v['cost']=cost(v['bom'],v)
