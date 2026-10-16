"""Source-backed inventory and bounded, reusable classroom configurations."""
import json, math
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
ROOT=Path(__file__).resolve().parents[1]
DATE='2026-10-15'
PRICE_DATE='2026-10-14'
SHEET='https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit'
SOURCES={
 'brief':('Project rationale — Yuri Panchul, September 2026','https://docs.google.com/document/d/1lVcfQOqSg-6YrX_VTWy0q345JGLUEWaLRE-17egVzpo/edit'),
 'prequel':('Illustrated starting notes — 23 July 2026','https://verilog-meetup.com/2026/07/23/a-prequel-to-fpga-and-asic-design-using-small-scale-integration-chips/'),
 'improved':('Exercise list — 31 July 2026','https://verilog-meetup.com/2026/07/31/an-improved-way-of-teaching-school-kids-digital-electronics-using-venerable-small-scale-integration-ics/'),
 'course':('Annual course, breadboard lessons 1.1–1.7 — 22 August 2026','https://habr.com/en/articles/1071736/'),
 'review':('Review and single-FIFO request — 15 October 2026','20261015_review1.txt'),
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
add('touch','TTP223 assembled capacitive touch switch, self-locking / toggle mode','0.25',
    note='Explicitly requested in review1; USD 0.25/module is an unverified budgeting assumption, not a retrieved listing price. Supply with pins fitted and toggle mode already selected.',
    url='https://www.aliexpress.us/item/3256805900856431.html',category='User-requested part')
E=[]
def ex(id,title,ics,boards,buttons,bars,mm,src,lesson,goal,*,displays=0,clock=False,touch=0,traffic=0,led=0,note='',status='Estimated build'):
 """mm is an estimated working wire count; the kit adds 25%."""
 bom=dict(ics)
 bom.update(board=boards,power=1,cable=1,extractor=1)
 for k,v in dict(button=buttons,bar=bars,display=displays,clock=int(clock),touch=touch,traffic=traffic,led=led).items():
  if v:bom[k]=v
 if displays:bom['r560']=7*displays
 # Individual 3-pin button/touch modules, 9-pin LED bars, clock and traffic LEDs.
 mf=3*(buttons+touch)+9*bars+3*int(clock)+4*traffic
 bom['mm']=mm
 if mf:bom['mf']=mf
 E.append(dict(id=id,title=title,bom=bom,src=src,lesson=lesson,goal=goal,note=note,status=status))
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
ex('C11','Single FIFO with clock, push/pop and four data switches',{'40105':1,'4081':1,'4069':1},2,2,1,40,'improved,review','Building blocks / review1','Set a 4-bit word with four self-locking TTP223 switches. PUSH and POP are requests sampled with the assembled clock; observe Q[3:0], EMPTY and FULL.',clock=True,touch=4,note='Two operational buttons: PUSH and POP. Initialize MR with a rail jumper. Six channels of one 8-LED bar are used. AND/inverter quantities budget clock/command logic and flag polarity; the FIFO pin-level timing adapter remains to be verified.')
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
ex('P03','Automatic three-FIFO adder with backpressure',{'40105':3,'4008':1,'4081':3,'4069':2},4,3,3,120,B,'Projects / 1.5; review1 RTL','At each clock cycle, enqueue A and B independently. Automatically consume their oldest pair and enqueue the sum when both are available and the result FIFO can accept it.',clock=True,note='Three operational controls: A_VALID, B_VALID and SUM_READY. Data[3:0] for each operand and reset use rail jumpers. Target behavior is the supplied valid/ready RTL at width=4, depth=16. Gate quantities are a preliminary Boolean/clock-interface budget, not a completed 40105 pulse-adapter netlist.')
ex('P04','Two-request round-robin arbiter',{'4081':1,'4011':1,'4071':1,'4013':1},2,3,1,50,'course','1.6 project 13','Observe requests, grants and priority. The assembled clock accepts one grant each rising edge; persistent simultaneous requests alternate.',clock=True,note='Four logic ICs. Buttons are r0, r1 and RESET. The assembled 555 module provides the clock directly.')
ex('P05','Sequence recognizer: 01',{'4013':1,'4069':1,'4081':1},2,2,1,40,B,'Projects / 1.7','DATA is 1 while pressed and 0 while released. The assembled clock samples one bit per rising edge; RESET starts a new stream.',clock=True,note='Reset seen_zero and MATCH to 0. seen_zero_next=NOT X; match_next=seen_zero AND X. Both 4013 halves use the assembled clock.')
ex('P06','Custom 2–4 bit sequence FSM',{'40174':1,'4076':1,'4073':3,'4072':3,'4071':1,'4069':1},4,2,1,140,B,'Projects / 1.7','Set DATA before each rising edge of the assembled clock. Build a recognizer for a teacher-assigned binary pattern of length 2–4; show state and MATCH on LEDs.',clock=True,note='Use 40174 for two state bits and registered MATCH. 4076 is the source alternative register. Three 4073s provide eight minterms; three 4072s plus one 4071 provide three 8-term OR trees. The custom task generator uses the same clocked input convention.')
comp={'4013':1,'4069':1,'4070':1,'4081':2,'4071':2,'4063':1}
ex('P07','Bit-serial comparator, least-significant bit first',comp,3,3,1,100,B,'Projects / 1.7','On each rising edge of the assembled clock, overwrite greater/less for differing input bits or retain the comparison for equal bits. Reset both flags to 0.',clock=True,note='Two data buttons and RESET. Equality=NOT(greater OR less). 4063 provides a four-bit reference comparison using rail-patched operands.')
ex('P08','Bit-serial comparator, most-significant bit first',comp,3,3,1,100,'course','1.7 variant','On assembled-clock edges, latch the first differing input pair and ignore subsequent differences. Compare the final flags with 4063.',clock=True)
ex('P09','Cascaded 8-bit comparator',{'4063':2},2,0,0,70,'course','1.7 variant','Patch sixteen operand bits; cascade from the least-significant nibble to the most-significant comparator.',traffic=1)
ex('P10','FSM comparing one nibble per clock',{'4063':1,'4013':1,'4069':1,'4081':2,'4071':2},3,9,0,100,'course','1.7 variant','Use 4063 for each input nibble pair and two state bits to remember the first unequal nibble. The assembled clock advances the comparison; RESET starts a word.',clock=True,traffic=1,note='Eight data buttons and RESET. The least-significant-nibble-first variant overwrites the comparison on every unequal nibble.')
ex('P11','Traffic-light FSM: 4 red, 2 yellow, 4 green',{'4017':1,'4072':1,'4071':1},2,1,0,62,'course','1.7','OR Q0–Q3 for red, Q4–Q5 for yellow, Q6–Q9 for green. Count cycles and verify exactly one lamp is lit.',clock=True,traffic=1)
ex('P12','Compare binary and Johnson counter streams',{'4029':1,'4015':1,'4069':1,'4063':1},2,1,1,86,'course','1.6 combined project','Clock a 4-bit binary counter and a 4-stage Johnson counter together; display both vectors and the greater/equal/less comparison.',clock=True,traffic=1)
ex('O01','Hexadecimal display with DM9368',{'4008':1,'DM9368':3},3,8,1,85,'course','1.2 optional alternative','Wire the source’s DM9368 alternative to display hexadecimal operands and result.',displays=3,note='DM9368 has its own pinout and integrated segment current sources; use its datasheet. The 560 Ω resistors belong to the 4511 version and are not fitted here.',status='Legacy part; procurement required')
# The DM9368 alternative supplies segment current internally.
del E[-1]['bom']['r560']
# Updated wire allowances exclude the deleted support circuits; still estimates.
working_mm={'B01':10,'B02':18,'B03':18,'B04':18,'B05':18,'B06':42,'B07':22,'B08':28,'B09':28,'B10':36,'B11':28,'B12':82,
'A01':28,'A02':38,'A03':46,'A04':50,'C01':30,'C02':32,'C03':28,'C04':30,'C05':30,'C06':30,'C07':30,'C08':30,'C09':44,'C10':28,
'C12':48,'C13':50,'M01':68,'M02':68,'M03':66,'M04':62,'M05':68,'M06':30,'P01':120,'P02':150,'P09':50,'P11':40,'P12':60}
for e in E:
 if e['id'] in working_mm:e['bom']['mm']=working_mm[e['id']]
 if e['id'].startswith('G'):e['bom']['mm']=22
BY_ID={e['id']:e for e in E}
KITS={
 'basics':dict(title='Basics',ids=['B01','B02','B03','B04','B05','B06','B07','B08','B09','B10','B11','B12'],minutes=20,packaging='3.00',description='Every exercise in the July article’s Basics section, including three simultaneous decimal displays, plus the first-lesson De Morgan comparison.'),
 'comprehensive':dict(title='Comprehensive',ids=[e['id'] for e in E],minutes=60,packaging='6.00',description='All explicitly described breadboard exercises and bounded variants in the two source lists, including rare ICs and the optional hexadecimal display.'),
 'fifo':dict(title='Automatic three-FIFO adder',ids=['P03'],minutes=25,packaging='4.00',description='Two operand queues feed an adder and a result queue automatically, following the supplied SystemVerilog valid/ready design.'),
 'arbiter':dict(title='Two-request round-robin arbiter',ids=['P04'],minutes=20,packaging='3.00',description='A four-core-IC arbiter with requests, grants, retained priority, a slow assembled clock.'),
 'fsm':dict(title='FSM and custom sequence tasks',ids=['P05','P06'],minutes=30,packaging='4.00',description='A 01 starter and a configurable, overlapping recognizer for any 2–4 bit binary sequence. Includes an assembled clock and an offline task generator.'),
 'single_fifo':dict(title='Single FIFO',ids=['C11'],minutes=20,packaging='3.00',description='One FIFO, assembled clock, PUSH/POP buttons, four TTP223 self-locking data switches and LEDs for 4-bit data, EMPTY and FULL.'),
}
def kit_bom(ids):
 b={}
 for id in ids:
  for p,q in BY_ID[id]['bom'].items():b[p]=max(b.get(p,0),q)
 # Rebuild one exercise at a time. Pack rounding on consumables / connector types.
 for p in ('mm','mf'):
  if p in b:b[p]=math.ceil(b[p]*1.25/40)*40
 # Button modules are allocated individually from bulk supplier packs.
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
