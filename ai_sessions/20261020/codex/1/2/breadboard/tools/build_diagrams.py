#!/usr/bin/env python3
"""One pin/net database for diagrams, jumper CSV and the chip-level HDL."""
from pathlib import Path
import csv,json,subprocess,argparse
from collections import defaultdict
from html import escape as E
from draw_fsm import draw as draw_fsm
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'traffic_light'
Q_PINS=[3,2,4,7,10,1,5,6,9,11]
CHIPS={
'U1':{'part':'CD4017BE','n':16,'row':8,'pins':{**{p:f'S{i}' for i,p in enumerate(Q_PINS)},8:'GND',12:'NC',13:'GND',14:'clk',15:'rst',16:'+5V'},'names':{**{p:f'Q{i}' for i,p in enumerate(Q_PINS)},8:'VSS',12:'CARRY',13:'INHIBIT',14:'CLOCK',15:'RESET',16:'VDD'}},
'U2':{'part':'CD4072BE','n':14,'row':22,'pins':{1:'red',2:'S0',3:'S1',4:'S2',5:'S3',6:'NC',7:'GND',8:'NC',9:'S6',10:'S7',11:'S8',12:'S9',13:'green',14:'+5V'},'names':{1:'J',2:'A',3:'B',4:'C',5:'D',6:'NC',7:'VSS',8:'NC',9:'E',10:'F',11:'G',12:'H',13:'K',14:'VDD'}},
'U3':{'part':'CD4071BE','n':14,'row':35,'pins':{1:'S4',2:'S5',3:'yellow',4:'NC',5:'GND',6:'GND',7:'GND',8:'GND',9:'GND',10:'NC',11:'NC',12:'GND',13:'GND',14:'+5V'},'names':{1:'A',2:'B',3:'J',4:'K',5:'C',6:'D',7:'VSS',8:'E',9:'F',10:'L',11:'M',12:'G',13:'H',14:'VDD'}}}
PORTS={'clk':'h47','rst':'h50'}
LEDS={'red':('b48','b49'),'yellow':('b52','b53'),'green':('b56','b57')}
COLORS={'+5V':'#bd2d3a','GND':'#3f4d59','clk':'#764cb1','rst':'#cf6c19','red':'#c42f41','yellow':'#b38100','green':'#10826b'}
for i in range(10):COLORS[f'S{i}']=['#ad3041','#ba4654','#8b375d','#a6507b','#a47700','#b98808','#237b52','#278e73','#267d9a','#3f67a3'][i]
def phole(c,p):
 d=CHIPS[c];h=d['n']//2
 return f"{'e' if p<=h else 'f'}{d['row']+(p-1 if p<=h else d['n']-p):02d}"
def strip(h):
 if h[:2] in ['LP','LM','RP','RM']:return h[:2]+('top' if int(h[2:])<=25 else 'bottom')
 return ('L' if h[0]<'f' else 'R')+str(int(h[1:]))
occupied=set(PORTS.values())|{h for pair in LEDS.values() for h in pair}
for c,d in CHIPS.items():occupied.update(phole(c,p) for p in d['pins'])
occupied.update(['LP01','LM01','LP05','LM05','LP06','LM06'])
def spare(h):
 for col in ('abcd' if h[0]<'f' else 'jihg'):
  x=col+h[1:]
  if x not in occupied:occupied.add(x);return x
 raise ValueError(('strip full',h))
wires=[]
def wire(net,a,b,kind):
 assert a!=b
 wires.append({'id':f'W{len(wires)+1:02d}','net':net,'from':a,'to':b,'kind':kind})
for rail in ['LP','LM','RP','RM']:
 for h in [rail+'25',rail+'26']:assert h not in occupied;occupied.add(h)
 wire('+5V' if rail[1]=='P' else 'GND',rail+'25',rail+'26','rail')
for l,r,n in [('LP02','RP02','+5V'),('LM02','RM02','GND')]:
 occupied.update([l,r]);wire(n,l,r,'rail')
rail_next=defaultdict(lambda:8)
def railhole(net,side):
 rail=side+('P' if net=='+5V' else 'M')
 while rail+f'{rail_next[rail]:02d}' in occupied:rail_next[rail]+=1
 h=rail+f'{rail_next[rail]:02d}';occupied.add(h);rail_next[rail]+=1;return h
nets=defaultdict(list)
for c,d in CHIPS.items():
 for p,net in d['pins'].items():
  if net!='NC':nets[net].append(phole(c,p))
for net,h in PORTS.items():nets[net].append(h)
for net,(a,k) in LEDS.items():nets[net].append(a);nets['GND'].append(k)
for net,holes in nets.items():
 if net in ['+5V','GND']:
  for h in holes:wire(net,spare(h),railhole(net,'L' if h[0]<'f' else 'R'),'power')
 else:
  assert len(holes)==2,(net,holes)
  wire(net,spare(holes[0]),spare(holes[1]),'signal')
# Connectivity through breadboard copper and all wires, independent of drawing geometry.
parent={}
def find(x):
 parent.setdefault(x,x)
 if parent[x]!=x:parent[x]=find(parent[x])
 return parent[x]
def union(a,b):parent[find(a)]=find(b)
for w in wires:union(strip(w['from']),strip(w['to']))
net_roots={}
for net,holes in nets.items():
 roots={find(strip(h)) for h in holes}
 if net in ['+5V','GND']:roots.add(find(strip('LP01' if net=='+5V' else 'LM01')))
 assert len(roots)==1,(net,roots)
 net_roots[net]=next(iter(roots))
assert len(set(net_roots.values()))==len(net_roots),'shorted nets'
ends=[w[k] for w in wires for k in ['from','to']]
assert len(ends)==len(set(ends)), 'two wires in one hole'
for c,d in CHIPS.items():
 for p,n in d['pins'].items():
  if n=='NC':assert find(strip(phole(c,p))) not in net_roots.values()
assert len(wires)==37
OUT.mkdir(exist_ok=True)
(OUT/'images').mkdir(exist_ok=True)
with (OUT/'jumpers.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['id','net','from','to','kind']);w.writeheader();w.writerows(wires)
(OUT/'netlist.json').write_text(json.dumps({'chips':CHIPS,'ports':PORTS,'leds':LEDS,'wires':wires},indent=2)+'\n')
# Emit the structural circuit using the actual package-pin database.
portnames={'U1':{p:f'p{p}_q{i}' for i,p in enumerate(Q_PINS)},'U2':{p:f'p{p}_{s.lower()}' for p,s in CHIPS['U2']['names'].items()},'U3':{p:f'p{p}_{s.lower()}' for p,s in CHIPS['U3']['names'].items()}}
portnames['U1'].update({12:'p12_carry',13:'p13_inhibit',14:'p14_clock',15:'p15_reset'})
def expr(n):return "1'b0" if n=='GND' else f'state [{n[1:]}]' if n.startswith('S') else '' if n=='NC' else n
sv=['`timescale 1ns / 1ps','`default_nettype none','','// Generated by tools/build_diagrams.py from the same pins/nets as the drawings.','// Synthesizable with the ideal chip models; all supply pins are physical-only.','','module traffic_light_chips','(','    input  wire       clk,','    input  wire       rst,','','    output wire       red,','    output wire       yellow,','    output wire       green,','    output wire [9:0] state',');','']
for c in CHIPS:
 d=CHIPS[c];ports=[]
 for p,n in d['pins'].items():
  if d['names'][p] in ['VSS','VDD','NC']:continue
  ports.append(f"        .{portnames[c][p]:<12} ({expr(n)})")
 sv.append(f"    {d['part'][:-1].lower()} {c.lower()}\n    (\n"+',\n'.join(ports)+'\n    );\n')
sv+=['endmodule','','`default_nettype wire','']
(OUT/'rtl/traffic_light_chips.sv').write_text('\n'.join(sv))

class SVG:
 def __init__(self,w,h,title):
  self.w=w;self.h=h;self.a=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{E(title)}</title><rect width="100%" height="100%" fill="#fff"/>']
 def text(self,x,y,t,size=20,fill='#193244',anchor='start'):
  self.a.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans,sans-serif" font-size="{size}" fill="{fill}" text-anchor="{anchor}">{E(str(t))}</text>')
 def rect(self,x,y,w,h,fill='#edf3f7',stroke='#506e82',rx=8):self.a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" rx="{rx}"/>')
 def path(self,d,color='#315a71',width=3,extra=''):self.a.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" {extra}/>')
 def circle(self,x,y,r,fill,stroke='none'):self.a.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}"/>')
 def save(self,name):
  p=OUT/'images'/name;p.write_text('\n'.join(self.a+['</svg>'])+'\n')
  return p

def gate(s,x,y,n,color,label):
 s.path(f'M {x} {y-65} Q {x+90} {y-65} {x+140} {y} Q {x+90} {y+65} {x} {y+65} Q {x+43} {y} {x} {y-65} Z',color,3)
 s.text(x+68,y+7,'OR',21,color,'middle');s.text(x+175,y+7,label,23,color)
 offsets=[-42,-14,14,42] if n==4 else [-22,22]
 return [(x+10,y+o) for o in offsets],(x+140,y)

for lang in ['en','ru']:
 t=lambda en,ru:en if lang=='en' else ru
 s=SVG(1450,880,t('1. Generic traffic-light logic','1. Логическая схема светофора'))
 s.text(45,55,t('1 · Ten states, three OR functions','1 · Десять состояний, три функции ИЛИ'),30)
 s.rect(200,160,360,570);s.text(380,205,t('10-state cyclic FSM','Циклический автомат'),25,anchor='middle');s.text(380,242,'S0 → S1 → … → S9 → S0',21,anchor='middle')
 for i in range(10):s.text(495,300+i*38,f'S{i}',20);s.path(f'M 540 {293+i*38} H 560')
 for k,y in [('clk ↑',620),('rst = 1',680)]:s.text(45,y+5,k,21);s.path(f'M 130 {y} H 200')
 s.text(220,760,t('Reset → S0; one active state','Сброс → S0; одно активное состояние'),20)
 for indices,y,color,label in [([0,1,2,3],300,COLORS['red'],t('RED','КРАСНЫЙ')),([4,5],480,COLORS['yellow'],t('YELLOW','ЖЁЛТЫЙ')),([6,7,8,9],660,COLORS['green'],t('GREEN','ЗЕЛЁНЫЙ'))]:
  pts,out=gate(s,920,y,len(indices),color,label)
  for j,((gx,gy),i) in enumerate(zip(pts,indices)):
   sy=293+i*38;lane=640+i*22;s.path(f'M 560 {sy} H {lane} V {gy} H {gx}',color,2.3)
 s.text(45,835,t('No chip pin numbers here: the block defines behavior, not a storage encoding.','Здесь нет номеров выводов: блок задаёт поведение, а не кодирование памяти.'),19)
 s.save(f'logic_{lang}.svg')
 s=SVG(1480,1090,t('2. Chip connections','2. Соединения микросхем'))
 s.text(40,55,t('2 · Chip connections at +5 V','2 · Соединения микросхем при +5 В'),30)
 s.rect(140,150,300,625);s.text(290,192,'U1 · CD4017BE',25,anchor='middle')
 for i,p in enumerate(Q_PINS):
  yy=240+i*45;s.text(290,yy+6,f'Q{i} · pin {p}',20);s.path(f'M 425 {yy} H 440')
 s.text(160,725,'14 CLOCK ← clk',19);s.text(160,755,'15 RESET ← rst',19)
 s.rect(780,130,290,530);s.text(925,171,'U2 · CD4072BE',24,anchor='middle')
 u2target={}
 for j,(i,p) in enumerate(zip([0,1,2,3,6,7,8,9],[2,3,4,5,9,10,11,12])):
  yy=220+j*48;u2target[i]=yy;s.text(795,yy+6,f'{p} ← S{i}',19)
 s.text(900,325,'1 → red',20,COLORS['red']);s.path('M 1070 320 H 1260',COLORS['red']);s.text(1270,327,t('RED','КРАСНЫЙ'),20,COLORS['red'])
 s.text(900,545,'13 → green',20,COLORS['green']);s.path('M 1070 540 H 1260',COLORS['green']);s.text(1270,547,t('GREEN','ЗЕЛЁНЫЙ'),20,COLORS['green'])
 s.rect(780,710,290,190);s.text(925,750,'U3 · CD4071BE',24,anchor='middle')
 for i,p,yy in [(4,1,790),(5,2,845)]:s.text(795,yy+6,f'{p} ← S{i}',19)
 s.text(900,825,'3 → yellow',19,COLORS['yellow']);s.path('M 1070 820 H 1260',COLORS['yellow']);s.text(1270,827,t('YELLOW','ЖЁЛТЫЙ'),20,COLORS['yellow'])
 for i in range(10):
  sy=240+i*45;ty=u2target.get(i,790 if i==4 else 845);lane=485+i*25
  s.path(f'M 440 {sy} H {lane} V {ty} H 780',COLORS[f'S{i}'],2.2)
 for j,line in enumerate([t('Supplies: U1.16, U2.14, U3.14 → +5 V; U1.8, U2.7, U3.7 → GND.','Питание: U1.16, U2.14, U3.14 → +5 В; U1.8, U2.7, U3.7 → GND.'),t('U1.13 → GND. U3 inputs 5, 6, 8, 9, 12, 13 → GND. LED cathodes → GND.','U1.13 → GND. Входы U3 5, 6, 8, 9, 12, 13 → GND. Катоды LED → GND.'),t('Leave open: U1.12; U2.6,8; U3.4,10,11. Signals are active high.','Не подключать: U1.12; U2.6,8; U3.4,10,11. Активный уровень сигналов — 1.')]):s.text(40,965+j*35,line,19)
 s.save(f'connections_{lang}.svg')
 s=SVG(1490,720,t('DIP pin diagrams, top view','Цоколёвка DIP, вид сверху'))
 s.text(40,48,t('Top view · notch up · all supplies +5 V','Вид сверху · выемка вверх · питание +5 В'),27)
 for idx,(c,d) in enumerate(CHIPS.items()):
  x=170+idx*490;y=160;w=160;h=(d['n']//2-1)*52+50
  s.text(x+80,110,c+' · '+d['part'],23,anchor='middle');s.rect(x,y,w,h,'#263d4d');s.path(f'M {x+55} {y} Q {x+80} {y+35} {x+105} {y}','#fff',2)
  for p in range(1,d['n']+1):
   left=p<=d['n']//2;row=p-1 if left else d['n']-p;yy=y+25+row*52
   s.path(f'M {x-20 if left else x+w} {yy} h 20','#556b76',5)
   s.text(x+12 if left else x+w-12,yy+6,p,17,'#fff','start' if left else 'end')
   label=d['names'][p];s.text(x-27 if left else x+w+27,yy+6,label,18,anchor='end' if left else 'start')
 s.text(40,650,t('NC = no connection. Unused outputs stay open; unused logic inputs go to GND.','NC — не подключать. Неиспользуемые выходы свободны; логические входы — на GND.'),20)
 s.save(f'pinouts_{lang}.svg')
 # Full board view with every on-board wire, including supply rail bridges.
 s=SVG(1500,1870,t('3. Breadboard with every jumper','3. Макетная плата со всеми перемычками'))
 s.text(40,55,t('3 · One 830-contact board · 37 jumpers','3 · Одна плата на 830 контактов · 37 перемычек'),30)
 s.text(40,94,t('All wires are shown. Endpoints are authoritative; line crossings are not junctions.','Показаны все провода. Соединения задают концы; пересечения линий не соединены.'),20)
 cols={**{c:680+20*i for i,c in enumerate('abcde')},**{c:860+20*i for i,c in enumerate('fghij')}}
 def xy(h):
  if h[:2] in ['LP','LM','RP','RM']:
   n=int(h[2:]);return {'LP':560,'LM':590,'RP':1040,'RM':1070}[h[:2]],220+(n-1)*29+(18 if n>25 else 0)
  return cols[h[0]],220+(int(h[1:])-1)*23
 s.rect(525,165,580,1540,'#f5f3e9','#9b9e9d',18)
 for c,x in cols.items():
  s.text(x,197,c,18,anchor='middle')
  for r in range(1,64):s.circle(x,220+(r-1)*23,3.2,'#9da3a7')
 for r in range(1,64):s.text(640,225+(r-1)*23,r,13,anchor='end')
 for rail in ['LP','LM','RP','RM']:
  x,_=xy(rail+'01');s.text(x,190,rail,15,anchor='middle')
  for r in range(1,51):
   x,y=xy(rail+f'{r:02d}');s.circle(x,y,3.5,'#aa3941' if rail[1]=='P' else '#36414d')
  for first,last in [(1,25),(26,50)]:
   x,y1=xy(rail+f'{first:02d}');_,y2=xy(rail+f'{last:02d}');s.path(f'M {x-10} {y1} V {y2}',COLORS['+5V' if rail[1]=='P' else 'GND'],2)
  s.text(x,1730,rail,15,anchor='middle')
 for c,d in CHIPS.items():
  y=xy(phole(c,1))[1]-10;hh=(d['n']//2-1)*23+20;s.rect(773,y,74,hh,'#263d4d','#263d4d',3)
  s.path(f'M 795 {y} Q 810 {y+20} 825 {y}','#fff',2);s.text(810,y+hh/2,c,22,'#fff','middle')
  for p in range(1,d['n']+1):
   x,yy=xy(phole(c,p));s.path(f'M {x} {yy} H {773 if x<800 else 847}','#657986',5);s.text(782 if x<800 else 838,yy+4,p,10,'#fff','start' if x<800 else 'end')
 # Use separate outside lanes for signal wires, with net labels at the lane.
 sig_index=0
 for idx,w in enumerate(wires):
  a,b=xy(w['from']),xy(w['to']);color=COLORS[w['net']];x1,y1=a;x2,y2=b
  if w['kind']=='rail':path=f'M {x1} {y1} L {x2} {y2}'
  elif w['kind']=='power':path=f'M {x1} {y1} L {x2} {y2}'
  else:
   lane=120+sig_index*24;sig_index+=1
   path=f'M {x1} {y1} H {lane} V {y2} H {x2}'
  s.path(path,'#fff',5)
  s.path(path,color,2.5,f'id="{w["id"]}"')
  for x,y in [a,b]:s.circle(x,y,4,color)
  s.text(x1+5,y1-5,w['id'],11,color)
  if w['kind']=='signal':s.text(1120,240+(sig_index-1)*57,w['id']+' · '+w['net'],18,color);s.text(1120,261+(sig_index-1)*57,w['from']+' → '+w['to'],16)
 # LEDs are explicitly current-limited 5 V indicators.
 for net,(an,ca) in LEDS.items():
  x,y=xy(an);_,yk=xy(ca);s.path(f'M {x} {y} V {yk}',COLORS[net],4);s.circle(x,(y+yk)/2,9,COLORS[net]);s.text(780,y+8,net.upper(),18,COLORS[net])
 for net,h in PORTS.items():
  x,y=xy(h);s.circle(x,y,7,'#fff',COLORS[net]);s.text(1120,y+6,f'{net} → {h}',19,COLORS[net])
 s.text(45,1768,t('Clock: OUT → h47, + → LP05, − → LM05. Reset module: OUT → h50, + → LP06, − → LM06.','Такт: OUT → h47, + → LP05, − → LM05. Модуль сброса: OUT → h50, + → LP06, − → LM06.'),18)
 s.text(45,1804,t('Regulated +5 V → LP01; supply GND → LM01. Rails split between holes 25 and 26; bridge all four.','Стабильные +5 В → LP01; земля БП → LM01. Разрывы шин 25–26 замкнуты четырьмя перемычками.'),18)
 s.text(45,1840,t('Module leads and two supply leads are additional. LED anode/cathode: b48/b49, b52/b53, b56/b57.','Провода модулей и два провода питания — отдельно. Анод/катод LED: b48/b49, b52/b53, b56/b57.'),18)
 s.save(f'breadboard_{lang}.svg')
 s=SVG(1380,570,t('Traffic-light timing','Временная диаграмма светофора'))
 s.text(40,50,t('One complete 10-second cycle at 1 Hz','Полный цикл 10 секунд при частоте 1 Гц'),28)
 x0=200;step=105
 for i in range(11):
  x=x0+i*step;s.path(f'M {x} 90 V 490','#d3dce3',1);s.text(x,110,i,18,anchor='middle')
 s.text(40,110,t('time, s','время, с'),20)
 s.text(40,160,'state',20)
 for i in range(10):s.text(x0+i*step+step/2,160,f'S{i}',19,anchor='middle')
 for k,(label,high,color) in enumerate([('clk',None,'#315a71'),('red',range(4),COLORS['red']),('yellow',range(4,6),COLORS['yellow']),('green',range(6,10),COLORS['green'])]):
  yy=235+k*72;s.text(40,yy,label,20)
  if high is None:
   d=f'M {x0} {yy-30}'
   for i in range(10):d+=f' H {x0+(i+.5)*step} V {yy} H {x0+(i+1)*step} V {yy-30}'
  else:
   d=f'M {x0} {yy-30 if 0 in high else yy}'
   for i in range(10):d+=f' V {yy-30 if i in high else yy} H {x0+(i+1)*step}'
  s.path(d,color,3)
 s.text(40,545,t('Reset establishes S0 at t=0. Rising edges at t=1…10 advance the state. Delays omitted.','Сброс задаёт S0 при t=0. Фронты t=1…10 меняют состояние. Задержки не показаны.'),19)
 s.save(f'timing_{lang}.svg')

(OUT/'research/wiring_validation.json').write_text(json.dumps({'status':'PASS','packages':3,'dip_pins':44,'jumpers':len(wires),'signal':15,'power':16,'rails':6,'checks':['No double-booked holes','No net shorts','All functional pins connected','NC pins isolated','Split rails bridged','Structural HDL generated from pin database'],'scope':'Static wiring validation, not a physical build or analog timing test'},indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--png',action='store_true');args=p.parse_args()
 draw_fsm()
 if args.png:
  for src in sorted((OUT/'images').glob('*.svg')):
   subprocess.run(['inkscape',str(src),'--export-type=png','--export-filename='+str(src.with_suffix('.png'))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 print('Generated 14 SVG diagrams, structural HDL and 37 checked jumper connections'+(' + PNGs' if args.png else ''))
