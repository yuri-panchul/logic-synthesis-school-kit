#!/usr/bin/env python3
"""Draw both getting-started editions from explicit pin nets and checked layouts.

Six drawings, each with separate XOR and D-flip-flop experiments, in SVG/PNG.
No source guide is changed. SVG is original vector artwork, not generated art.
"""
from pathlib import Path
from collections import defaultdict
from html import escape
import csv
import hashlib
import json
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
INK = '#203746'
MUTED = '#536b7c'
COLORS = {'+5V':'#bf3148', 'GND':'#28629f', 'A':'#11806c', 'B':'#7a4bac',
          'DATA':'#11806c', 'RESET':'#7a4bac', 'CLK_RAW':'#ad6c04',
          'CLK_INV':'#c28320', 'CLK':'#ad6c04', 'XOR':'#11806c',
          'Q':'#11806c', 'BUF':'#11806c', 'LED':'#11806c'}
SOURCES = {
    'old_en':ROOT/'old_session_20261014/start_en.html',
    'old_ru':ROOT/'old_session_20261014/start_ru.html',
    'new_en':ROOT/'start_en.html', 'new_ru':ROOT/'start_ru.html',
}

def color(net): return COLORS.get(net, INK)

def circuit(old, experiment):
    c = {'edition':'old' if old else 'new', 'experiment':experiment, 'chips':{}, 'parts':{}}
    def chip(ref, part, count, col, pins):
        assert set(pins) == set(range(1,count+1))
        c['chips'][ref] = {'part':part,'count':count,'col':col,'pins':pins}
    # Pin tuple: displayed function, net, input/output/power role. None = NC.
    if experiment == 'xor':
        chip('U1','CD4070BE',14,9,{
            1:('A','A','I'),2:('B','B','I'),3:('Y','XOR','O'),
            4:('Y2',None,'O'),5:('A2','GND','I'),6:('B2','GND','I'),7:('VSS','GND','P'),
            8:('A3','GND','I'),9:('B3','GND','I'),10:('Y3',None,'O'),11:('Y4',None,'O'),
            12:('A4','GND','I'),13:('B4','GND','I'),14:('VDD','+5V','P')})
        buttons=['A','B']; output='XOR'
    else:
        chip('U1','CD4013BE',14,9,{
            1:('Q','Q','O'),2:('/Q',None,'O'),3:('CLK','CLK','I'),4:('RESET','RESET','I'),
            5:('D','DATA','I'),6:('SET','GND','I'),7:('VSS','GND','P'),8:('SET2','GND','I'),
            9:('D2','GND','I'),10:('RESET2','GND','I'),11:('CLK2','GND','I'),
            12:('/Q2',None,'O'),13:('Q2',None,'O'),14:('VDD','+5V','P')})
        buttons=['DATA','RESET']; output='Q'
        if old:
            chip('U3','SN74HCT14N',14,26,{
                1:('1A','CLK_RAW','I'),2:('1Y','CLK_INV','O'),3:('2A','CLK_INV','I'),
                4:('2Y','CLK','O'),5:('3A','GND','I'),6:('3Y',None,'O'),7:('GND','GND','P'),
                8:('4Y',None,'O'),9:('4A','GND','I'),10:('5Y',None,'O'),11:('5A','GND','I'),
                12:('6Y',None,'O'),13:('6A','GND','I'),14:('VCC','+5V','P')})
    if old:
        chip('U2','SN74HCT244N',20,43 if experiment=='dff' else 32,{
            1:('/1OE','GND','I'),2:('1A1',output,'I'),3:('2Y4',None,'O'),4:('1A2','GND','I'),
            5:('2Y3',None,'O'),6:('1A3','GND','I'),7:('2Y2',None,'O'),8:('1A4','GND','I'),
            9:('2Y1',None,'O'),10:('GND','GND','P'),11:('2A1','GND','I'),
            12:('1Y4',None,'O'),13:('2A2','GND','I'),14:('1Y3',None,'O'),15:('2A3','GND','I'),
            16:('1Y2',None,'O'),17:('2A4','GND','I'),18:('1Y1','BUF','O'),
            19:('/2OE','GND','I'),20:('VCC','+5V','P')})
        c['parts']['R1']={'value':'2.2 kΩ','pins':{'1':'BUF','2':'LED'},'holes':{'1':'b57','2':'b61'}}
        for i,(ref,dev) in enumerate(c['chips'].items(),1):
            # A ceramic at the VDD strip and adjacent free grounded strip.
            col=dev['col']
            c['parts'][f'C{i}']={'value':'100 nF','pins':{'1':'+5V','2':'GND'},
                                'holes':{'1':f'b{col}','2':f'b{col-1}'},'near':ref}
        c['parts']['C0']={'value':'10 µF','pins':{'+':'+5V','−':'GND'},'holes':{'+':'b3','−':'b4'}}
    modules={
        'PWR':{'name':'5 V supply / питание','pins':{'+5V':'+5V','GND':'GND'}},
        'S1':{'name':buttons[0],'pins':{'VCC':'+5V','GND':'GND','OUT':buttons[0]}},
        'S2':{'name':buttons[1],'pins':{'VCC':'+5V','GND':'GND','OUT':buttons[1]}},
        'LED1':{'name':'5 V LED','pins':{'A':'LED' if old else output,'K':'GND'}},
    }
    if experiment=='dff':
        modules['OSC']={'name':'555 · 0.5–1 Hz','pins':{'VCC':'+5V','GND':'GND','OUT':'CLK_RAW' if old else 'CLK'}}
    c['modules']=modules
    return c


class SVG:
    def __init__(self,w,h,title,desc):
        self.w,self.h=w,h
        self.items=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
                    f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>',
                    '<style>text{font-family:DejaVu Sans,Arial,sans-serif} .mono{font-family:DejaVu Sans Mono,monospace}</style>']
        self.rect(0,0,w,h,'#fff',stroke='none')
    def rect(self,x,y,w,h,fill='#fff',stroke=INK,r=0,sw=2):
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def text(self,x,y,text,size=18,fill=INK,weight='normal',anchor='start',mono=False):
        self.items.append(f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"'+(' class="mono"' if mono else '')+f'>{escape(str(text))}</text>')
    def line(self,pts,stroke=INK,sw=2.5,halo=False,dash=None):
        points=' '.join(f'{x},{y}' for x,y in pts)
        if halo:self.items.append(f'<polyline points="{points}" fill="none" stroke="white" stroke-width="{sw+4}" stroke-linejoin="round"/>')
        self.items.append(f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def path(self,d,fill='none',stroke=INK,sw=2.5):
        self.items.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def circle(self,x,y,r=4,fill=INK,stroke='none',sw=1):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def tag(self,x,y,text,net=None,size=15):
        width=len(text)*size*.62+14
        self.rect(x-4,y-size,width,size+8,'white',stroke='none',r=3)
        self.text(x+3,y,text,size,color(net) if net else MUTED,weight='bold')
    def ground(self,x,y):
        self.line([(x,y),(x,y+12)],color('GND'))
        for dy,half in [(12,13),(18,8),(24,3)]:self.line([(x-half,y+dy),(x+half,y+dy)],color('GND'),2)
    def resistor(self,x,y,length=86,label='R1 · 2.2 kΩ'):
        self.line([(x,y),(x+14,y)])
        self.rect(x+14,y-8,length-28,16,'#fff6d6',sw=2)
        self.line([(x+length-14,y),(x+length,y)])
        self.text(x+length/2,y-18,label,16,anchor='middle')
    def cap(self,x,y,label,polar=False):
        self.line([(x,y),(x,y+28)],color('+5V'))
        self.line([(x-15,y+28),(x+15,y+28)])
        self.line([(x-15,y+38),(x+15,y+38)])
        self.line([(x,y+38),(x,y+64)],color('GND'))
        self.text(x+25,y+38,label,16)
        if polar:self.text(x-28,y+23,'+',18,color('+5V'),weight='bold')
    def buffer(self,x,y,invert=False,schmitt=False):
        self.path(f'M{x},{y-25} L{x},{y+25} L{x+58},{y} Z','#fff')
        if schmitt:self.line([(x+10,y+7),(x+19,y+7),(x+19,y-7),(x+29,y-7),(x+29,y+7),(x+37,y+7)],INK,1.8)
        if invert:self.circle(x+64,y,6,'white',INK,2)
        return (x+70 if invert else x+58,y)
    def xor(self,x,y):
        self.path(f'M{x},{y-42} Q{x+36},{y} {x},{y+42} Q{x+65},{y+42} {x+104},{y} Q{x+65},{y-42} {x},{y-42}', '#fff')
        self.path(f'M{x-10},{y-42} Q{x+26},{y} {x-10},{y+42}')
        self.text(x+50,y+6,'=1',18,anchor='middle')
    def led(self,x,y):
        self.rect(x,y-48,185,132,'#f2f8f4',stroke='#9eb8ac',r=9)
        self.text(x+92,y-24,'5 V LED',20,weight='bold',anchor='middle')
        self.line([(x,y),(x+65,y)],color('LED'))
        self.path(f'M{x+65},{y-12} L{x+65},{y+12} L{x+85},{y} Z','#f4bc4b')
        self.line([(x+87,y-13),(x+87,y+13)])
        self.line([(x+87,y),(x+150,y),(x+150,y+22)],color('GND'))
        self.ground(x+150,y+22)
        self.text(x+10,y+70,'I limited / огр. тока',13,MUTED)
        for xx,yy in [(96,-8),(108,-2)]:
            self.line([(x+xx,y+yy),(x+xx+18,y+yy-12)],INK,1.5)
            self.line([(x+xx+18,y+yy-12),(x+xx+11,y+yy-11)],INK,1.5)
    def save(self,path):path.write_text('\n'.join(self.items+['</svg>'])+'\n')


def header(s,old,kind):
    edition='OLD · 14 Oct 2026 / СТАРАЯ' if old else 'NEW · current guide / НОВАЯ'
    s.text(40,42,edition,25,weight='bold')
    s.text(40,73,kind,20,MUTED)
    s.text(40,100,'A: XOR experiment / опыт XOR     B: D flip-flop experiment / опыт с D-триггером',16,MUTED)

def input_box(s,x,y,name,clock=False):
    s.rect(x,y-30,190,60,'#edf4fa',stroke='#7c9eb7',r=7)
    s.text(x+95,y+5,name,19,weight='bold',anchor='middle')
    s.text(x+95,y+49,'+5V · GND',13,MUTED,anchor='middle')
    if clock:s.text(x+95,y-42,'0.5–1 Hz',14,MUTED,anchor='middle')


def draw_generic(old):
    s=SVG(1500,1210 if old else 1120,'Old/new generic circuits','Two separate experiments: XOR and a positive-edge D flip-flop with asynchronous reset.')
    header(s,old,'1 · Generic elements / Общие логические элементы')
    s.rect(25,125,1450,375,'#fbfcfd','#d6e1e8',12)
    s.text(50,162,'A · XOR',23,weight='bold')
    input_box(s,65,245,'A');input_box(s,65,355,'B')
    s.xor(450,300)
    s.line([(255,245),(360,245),(360,278),(463,278)],color('A'))
    s.line([(255,355),(390,355),(390,322),(463,322)],color('B'))
    if old:
        s.line([(554,300),(770,300)],color('XOR'));s.buffer(770,300)
        s.text(800,252,'Buffer / буфер',17,anchor='middle')
        s.text(800,350,'enabled / включён',14,MUTED,anchor='middle')
        s.line([(828,300),(975,300)],color('BUF'));s.resistor(975,300)
        s.line([(1061,300),(1195,300)],color('LED'));s.led(1195,300)
    else:
        s.line([(554,300),(1050,300)],color('XOR'));s.tag(770,285,'Y = A ⊕ B','XOR');s.led(1050,300)
    s.text(65,458,'Button modules: released = 0, pressed = 1 / Кнопочные модули: отпущена = 0, нажата = 1',17,MUTED)
    s.rect(25,520,1450,465,'#fbfcfd','#d6e1e8',12)
    s.text(50,558,'B · D flip-flop / D-триггер',23,weight='bold')
    input_box(s,65,640,'DATA');input_box(s,65,775,'Clock / такт',True);input_box(s,65,910,'RESET')
    x=660;y=620
    s.rect(x,y,180,260,'#fff',INK,5)
    s.text(x+90,y+35,'D FF',22,weight='bold',anchor='middle')
    for label,yy in [('D',660),('CLK',775),('RESET',850)]:
        s.text(x+28,yy+5,label,17)
    s.path(f'M{x},{775-11} L{x+17},{775} L{x},{775+11}')
    s.text(x+150,695,'Q',20,anchor='middle')
    s.text(x+110,915,'SET = 0',16)
    s.line([(x+90,y+260),(x+90,929)]);s.ground(x+90,929)
    s.line([(255,640),(540,640),(540,660),(660,660)],color('DATA'))
    s.line([(255,910),(580,910),(580,850),(660,850)],color('RESET'))
    if old:
        s.line([(255,775),(355,775)],color('CLK_RAW'))
        s.buffer(355,775,True,True);s.line([(425,775),(475,775)],color('CLK_INV'))
        s.buffer(475,775,True,True);s.line([(545,775),(660,775)],color('CLK'))
        s.text(450,730,'2 × Schmitt NOT',17,anchor='middle')
        s.line([(840,690),(960,690)],color('Q'));s.buffer(960,690)
        s.line([(1018,690),(1090,690)],color('BUF'));s.resistor(1090,690)
        s.line([(1176,690),(1230,690)],color('LED'));s.led(1230,690)
        s.text(1000,641,'Buffer / буфер',16,anchor='middle')
    else:
        s.line([(255,775),(660,775)],color('CLK'))
        s.line([(840,690),(1120,690)],color('Q'));s.led(1120,690)
    s.text(900,830,'↑CLK: Q ← D',22,weight='bold')
    s.text(900,863,'RESET = 1: Q = 0',20)
    s.text(900,892,'asynchronous / асинхронно',16,MUTED)
    if old:
        s.text(45,1025,'A · Power / питание',18,weight='bold')
        s.text(765,1025,'B · Power / питание',18,weight='bold')
        for xs,values in [([105,310,515],['100 nF','100 nF','10 µF']),([805,985,1165,1345],['100 nF','100 nF','100 nF','10 µF'])]:
            s.line([(xs[0],1060),(xs[-1],1060)],color('+5V'))
            s.line([(xs[0],1124),(xs[-1],1124)],color('GND'))
            s.tag(xs[0],1050,'+5V','+5V');s.ground(xs[0],1124)
            for xx,value in zip(xs,values):
                s.cap(xx,1060,value,value=='10 µF');s.circle(xx,1060,3,color('+5V'));s.circle(xx,1124,3,color('GND'))
        s.text(45,1180,'Each 100 nF is local to one IC / Каждый 100 нФ установлен у своей микросхемы.',17,MUTED)
    else:
        s.text(45,1030,'Direct indicator and clock connections, as in the current guide.',18,MUTED)
        s.text(45,1060,'Прямое подключение индикатора и такта, как в текущей инструкции.',18,MUTED)
    return s


def chip_block(s,x,y,w,h,ref,part):
    s.rect(x,y,w,h,'white',INK,8)
    s.text(x+w/2,y+28,ref,19,weight='bold',anchor='middle')
    s.text(x+w/2,y+55,part,18,weight='bold',anchor='middle')

def port(s,x,y,label,left=True,net=None):
    s.line([(x-18 if left else x,y),(x if left else x+18,y)],color(net),2.5)
    s.text(x+10 if left else x-10,y-8,label,16,color(net),anchor='start' if left else 'end')

def draw_chips(old):
    s=SVG(1500,1790,'Chip connections','Pin-numbered chip connections. Port positions are schematic, not physical package positions.')
    header(s,old,'2 · Chip connections / Соединения микросхем')
    s.text(40,127,'Pin positions are schematic / Положение выводов условное.  Same net label = connection / Одинаковая метка = соединение.',14,MUTED)
    for exp,top in [('xor',155),('dff',945)]:
        c=circuit(old,exp)
        s.rect(25,top,1450,750,'#fbfcfd','#d6e1e8',12)
        s.text(45,top+38,'A · XOR' if exp=='xor' else 'B · D flip-flop / D-триггер',24,weight='bold')
        if exp=='xor':
            input_box(s,55,top+140,'S1 · A');input_box(s,55,top+255,'S2 · B')
            x,y,w,h=425,top+90,225,245
            chip_block(s,x,y,w,h,'U1','CD4070BE')
            for yy,label,net in [(top+180,'1 · A','A'),(top+260,'2 · B','B')]:port(s,x,yy,label,True,net)
            port(s,x+w,top+210,'3 · Y',False,'XOR')
            s.line([(245,top+140),(330,top+140),(330,top+180),(x-18,top+180)],color('A'))
            s.line([(245,top+255),(360,top+255),(360,top+260),(x-18,top+260)],color('B'))
            s.xor(x+80,top+220)
            source=(x+w+18,top+210)
        else:
            input_box(s,55,top+110,'S1 · DATA');input_box(s,55,top+305,'OSC · 555',True);input_box(s,55,top+415,'S2 · RESET')
            x,y,w,h=650,top+80,205,340
            chip_block(s,x,y,w,h,'U1','CD4013BE')
            for yy,label,net in [(top+170,'5 · D','DATA'),(top+305,'3 · CLK','CLK'),(top+380,'4 · RESET','RESET')]:port(s,x,yy,label,True,net)
            s.path(f'M{x},{top+294} L{x+15},{top+305} L{x},{top+316}')
            port(s,x+w,top+210,'1 · Q',False,'Q')
            s.line([(245,top+110),(580,top+110),(580,top+170),(x-18,top+170)],color('DATA'))
            s.line([(245,top+415),(605,top+415),(605,top+380),(x-18,top+380)],color('RESET'))
            if old:
                chip_block(s,330,top+195,235,160,'U3','SN74HCT14N')
                s.buffer(365,top+305,True,True);s.buffer(480,top+305,True,True)
                s.line([(245,top+305),(365,top+305)],color('CLK_RAW'))
                s.line([(435,top+305),(480,top+305)],color('CLK_INV'))
                s.line([(550,top+305),(x-18,top+305)],color('CLK'))
                for xx,pin in [(350,1),(439,2),(465,3),(555,4)]:s.text(xx,top+285,pin,14,anchor='middle')
                s.tag(445,top+340,'2 → 3','CLK_INV',13)
            else:s.line([(245,top+305),(x-18,top+305)],color('CLK'))
            s.text(x+25,top+405,'6 · SET → GND',16,color('GND'))
            source=(x+w+18,top+210)
        if old:
            bx=930 if exp=='dff' else 875;by=top+90
            chip_block(s,bx,by,205,245,'U2','SN74HCT244N')
            port(s,bx,top+210,'2 · 1A1',True,'Q' if exp=='dff' else 'XOR')
            port(s,bx+205,top+210,'18 · 1Y1',False,'BUF')
            s.line([source,(bx-18,top+210)],color('Q' if exp=='dff' else 'XOR'))
            s.buffer(bx+76,top+225)
            s.text(bx+102,top+303,'1, 19 · /OE → GND',15,color('GND'),anchor='middle')
            s.line([(bx+223,top+210),(1170,top+210)],color('BUF'))
            s.resistor(1170,top+210,80)
            s.line([(1250,top+210),(1270,top+210)],color('LED'))
            s.led(1270,top+210)
        else:
            s.line([source,(1190,top+210)],color('Q' if exp=='dff' else 'XOR'));s.led(1190,top+210)
        # Supply nets and every unused pin are explicit; no omitted floating inputs.
        summary_y=top+485
        rows=[]
        for ref,d in c['chips'].items():
            gnd=[str(p) for p,(_,net,kind) in d['pins'].items() if net=='GND' and kind!='P']
            nc=[str(p) for p,(_,net,_) in d['pins'].items() if net is None]
            vcc=next(p for p,(_,n,k) in d['pins'].items() if n=='+5V' and k=='P')
            g=next(p for p,(_,n,k) in d['pins'].items() if n=='GND' and k=='P')
            rows.append(f'{ref}: {vcc} → +5V; {g} → GND; '+','.join(gnd)+' → GND; NC: '+','.join(nc))
        for i,row in enumerate(rows):s.text(50,summary_y+i*25,row,15,MUTED,mono=True)
        s.text(50,top+570,'S1, S2'+(', OSC' if exp=='dff' else '')+': VCC → +5V; GND → GND. LED1: A ← signal / сигнал; K → GND.',15,MUTED)
        if old:
            # Separate, labeled power subcircuit keeps signal routing readable.
            for j,(ref,d) in enumerate(c['parts'].items()):
                if not ref.startswith('C'):continue
                xx=160+(j-1)*285
                yy=top+615
                s.tag(xx-10,yy-5,'+5V','+5V',13);s.cap(xx,yy,ref,ref=='C0');s.ground(xx,yy+64)
                s.text(xx-15,yy+103,d['value'],13,MUTED)
            s.text(50,top+736,'100 nF at each IC / у каждой ИС; C0 = 10 µF',14,MUTED)
    s.text(40,1745,'USB 5 V → 9 V boost cable / повышающий кабель → power module / модуль питания → +5V, GND',17,MUTED)
    return s


def pin_hole(dev,pin):
    half=dev['count']//2
    # DIP notch LEFT, top view: pin 1 is on the LOWER row f.
    return f'f{dev["col"]+pin-1}' if pin<=half else f'e{dev["col"]+dev["count"]-pin}'

def strip(hole):
    if hole[:2] in ('TP','TG','BP','BG'):
        return hole[:2]+('L' if int(hole[2:])<=25 else 'R')
    return ('U' if hole[0]<='e' else 'L')+hole[1:]

def make_layout(c):
    endpoints={};occupied=set();wires=[]
    def endpoint(name,net,hole,kind='I'):
        if hole:
            assert hole not in occupied,(name,hole)
            occupied.add(hole)
        endpoints[name]={'net':net,'hole':hole,'kind':kind}
    for ref,dev in c['chips'].items():
        for p,(label,net,kind) in dev['pins'].items():endpoint(f'{ref}.{p}',net,pin_hole(dev,p),kind)
    for ref,part in c['parts'].items():
        for p,net in part['pins'].items():endpoint(f'{ref}.{p}',net,part['holes'][p],'passive')
    for ref,module in c['modules'].items():
        for p,net in module['pins'].items():endpoint(f'{ref}.{p}',net,None,'module')
    def wire(a,b,net,label='',external=None):
        for h in [a,b]:
            assert h not in occupied,('shared physical hole',h)
            occupied.add(h)
        wires.append({'id':f'J{len(wires)+1:02}','a':a,'b':b,'net':net,'label':label,'external':external})
    def free(e):
        if e['hole'] is None:return next(n for n,v in endpoints.items() if v is e)
        side=e['hole'][0];col=e['hole'][1:]
        for row in ('cdab' if side<='e' else 'hgij'):
            h=row+col
            if h not in occupied:return h
        raise AssertionError(('no hole',e))
    def rail(net,preferred,lower=False):
        prefix=('B' if lower else 'T')+('P' if net=='+5V' else 'G')
        options=[i for i in range(1,51) if prefix+str(i) not in occupied]
        return prefix+str(min(options,key=lambda i:abs((i-1+(i-1)//5+3)-preferred)))
    for r in ('TP','TG','BP','BG'):wire(r+'25',r+'26','+5V' if r.endswith('P') else 'GND','rail bridge')
    wire('TP1','BP1','+5V','top/bottom rails');wire('TG1','BG1','GND','top/bottom rails')
    # Supplies, unused-input tie-offs, module power and capacitor connections.
    for name,e in endpoints.items():
        if e['net'] not in ('+5V','GND'):continue
        h=free(e);col=int(e['hole'][1:]) if e['hole'] else {'PWR':2,'S1':10,'S2':23,'OSC':36,'LED1':60}[name.split('.')[0]]
        lower=bool(e['hole'] and e['hole'][0]>='f') or (e['hole'] is None and not name.startswith('PWR'))
        dest=rail(e['net'],col,lower)
        wire(h,dest,e['net'],name,external=name if not e['hole'] else None)
    nets=defaultdict(list)
    for name,e in endpoints.items():
        if e['net'] not in (None,'+5V','GND'):nets[e['net']].append((name,e))
    for net,members in nets.items():
        assert len(members)==2,(net,members)
        (na,a),(nb,b)=members
        aa,bb=free(a),free(b)
        ext=na if a['hole'] is None else nb if b['hole'] is None else None
        wire(aa,bb,net,f'{na} → {nb}',external=ext)
    return {'endpoints':endpoints,'wires':wires,'occupied':sorted(occupied)}


def validate_layout(c,layout):
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    def node(h):return h if '.' in h else strip(h)
    for w in layout['wires']:parent[find(node(w['a']))]=find(node(w['b']))
    roots=defaultdict(set)
    for name,e in layout['endpoints'].items():
        actual=find(node(e['hole'] or name))
        roots[actual].add(e['net'] if e['net'] is not None else name+' NC')
    assert all(len(n)==1 for n in roots.values()),('short',roots)
    expected=defaultdict(set)
    for name,e in layout['endpoints'].items():
        if e['net'] is not None:expected[e['net']].add(find(node(e['hole'] or name)))
    assert all(len(r)==1 for r in expected.values()),('open',expected)
    assert find('TPL')!=find('TGL')
    # Follow the complete nets through the active pin paths, independently of artwork.
    p=c['chips']['U1']['pins']
    if c['experiment']=='xor':assert [p[i][1] for i in (1,2,3)]==['A','B','XOR']
    else:
        assert [p[i][1] for i in (5,3,4,6,1)]==['DATA','CLK','RESET','GND','Q']
        if c['edition']=='old':
            q=c['chips']['U3']['pins']
            assert [q[i][1] for i in (1,2,3,4)]==['CLK_RAW','CLK_INV','CLK_INV','CLK']
    if c['edition']=='old':
        q=c['chips']['U2']['pins'];assert q[1][1]==q[19][1]=='GND'
        assert q[2][1]==('XOR' if c['experiment']=='xor' else 'Q') and q[18][1]=='BUF'
        assert c['parts']['R1']['pins']=={'1':'BUF','2':'LED'}
    return {'status':'PASS','nets':len(expected),'jumper_leads':len(layout['wires']),
            'checks':['DIP orientation','exclusive hole occupancy','split-rail continuity','no shorted nets',
                      'all specified connections present','unused outputs isolated','active pin path']}


def hole_xy(h,top):
    if h[:2] in ('TP','TG','BP','BG'):
        i=int(h[2:]);col=i-1+(i-1)//5+3
        y={'TP':135,'TG':162,'BP':535,'BG':562}[h[:2]]
    else:
        row=h[0];col=int(h[1:]);y=(220+24*'abcde'.index(row)) if row<='e' else (384+24*'fghij'.index(row))
    return 130+(col-1)*20,top+y


def draw_breadboards(old,circuits,layouts):
    s=SVG(1540,1800,'Breadboard layouts','Top-view breadboards with real connected five-hole strips; each panel is a separate build.')
    header(s,old,'3 · Breadboard placement / Размещение на макетной плате')
    for exp,top in [('xor',130),('dff',930)]:
        c=circuits[exp];layout=layouts[exp]
        s.rect(25,top,1490,765,'#fbfcfd','#d6e1e8',12)
        s.text(45,top+35,'A · XOR' if exp=='xor' else 'B · D flip-flop / D-триггер',24,weight='bold')
        s.text(500,top+35,'Top view · notch LEFT · pin 1 BELOW / Вид сверху · выемка СЛЕВА · вывод 1 СНИЗУ',15,MUTED)
        s.rect(90,top+107,1320,486,'#f6f3e9','#bdc5c9',12)
        s.rect(107,top+337,1288,27,'#e7e2d7',stroke='none',r=8)
        s.text(1385,top+355,'gap',12,MUTED,anchor='end')
        for col in range(1,64):
            x,_=hole_xy(f'a{col}',top)
            for half,rows in [(0,'abcde'),(1,'fghij')]:
                s.line([hole_xy(rows[0]+str(col),top),hole_xy(rows[-1]+str(col),top)],'#e4dfd2',6)
                for row in rows:
                    xx,yy=hole_xy(row+str(col),top);s.circle(xx,yy,3.2,'#c4c8c8')
            if col==1 or col%5==0 or col==63:
                s.text(x,top+199,col,12,MUTED,anchor='middle');s.text(x,top+508,col,12,MUTED,anchor='middle')
        for row in 'abcdefghij':
            _,y=hole_xy(row+'1',top);s.text(108,y+5,row,14,MUTED,anchor='end');s.text(1392,y+5,row,14,MUTED)
        for rail in ('TP','TG','BP','BG'):
            net='+5V' if rail.endswith('P') else 'GND'
            for lo,hi in [(1,25),(26,50)]:s.line([hole_xy(rail+str(lo),top),hole_xy(rail+str(hi),top)],color(net),1)
            for n in range(1,51):
                x,y=hole_xy(rail+str(n),top);s.circle(x,y,3,'#9babb6')
                if n in [1,25,26,50]:s.text(x,y-9,n,10,MUTED,anchor='middle')
            _,y=hole_xy(rail+'1',top);s.text(110,y+5,rail,13,color(net),weight='bold',anchor='end')
        # Module connector names are logical labels; the supplied module dictates pin order.
        positions={'PWR':(100,top+63),'S1':(110,top+665),'S2':(410,top+665),
                   'OSC':(750,top+665),'LED1':(1190,top+665)}
        module_xy={}
        for ref,m in c['modules'].items():
            x,y=positions[ref];w=240 if ref!='LED1' else 200
            s.rect(x,y,w,62,'#eaf3f8' if ref!='LED1' else '#e8f4e9','#8aa4b4',7)
            s.text(x+w/2,y+24,f'{ref} · {m["name"]}',16,weight='bold',anchor='middle')
            for i,pin in enumerate(m['pins']):
                xx=x+35+i*78;yy=y+62 if ref=='PWR' else y
                module_xy[f'{ref}.{pin}']=(xx,yy)
                s.circle(xx,yy,4,color(m['pins'][pin]))
                s.text(xx,y+48 if ref=='PWR' else y+48,pin,13,color(m['pins'][pin]),anchor='middle')
        def xy(endpoint):return module_xy[endpoint] if '.' in endpoint else hole_xy(endpoint,top)
        # Power and ground first; signal routes remain visually identifiable.
        signal_index=0
        for w in sorted(layout['wires'],key=lambda w:w['net'] not in ('+5V','GND')):
            a,b=xy(w['a']),xy(w['b']);net=w['net']
            if w['label']=='rail bridge':
                delta=-18 if w['a'][:2] in ('TP','TG') else 18
                points=[a,(a[0],a[1]+delta),(b[0],b[1]+delta),b]
            elif w['label']=='top/bottom rails':
                xx=1440 if net=='+5V' else 1470
                points=[a,(xx,a[1]),(xx,b[1]),b]
            elif w['external']:
                ext=w['external'];other=b if w['a']==ext else a;mp=xy(ext)
                if ext.startswith('PWR'):
                    points=[mp,(mp[0],other[1]-8),(other[0],other[1]-8),other]
                else:
                    lane=top+615+(signal_index%5)*8
                    points=[mp,(mp[0],lane),(other[0],lane),other]
                    if net not in ('+5V','GND'):signal_index+=1
            elif net in ('+5V','GND'):
                points=[a,(a[0],b[1]),b]
            else:
                # Signals between ICs route below the terminal strips, not through IC bodies.
                lane=top+603+signal_index*9;signal_index+=1
                points=[a,(a[0],lane),(b[0],lane),b]
            s.line(points,color(net),2.4,halo=True)
            for xx,yy in [a,b]:s.circle(xx,yy,3.8,color(net))
        # Draw ICs and component bodies over their occupied holes.
        for ref,d in c['chips'].items():
            x,_=hole_xy('e'+str(d['col']),top);width=(d['count']//2-1)*20+22
            s.rect(x-11,top+330,width,40,'#253747',stroke='#122736',r=4)
            s.path(f'M{x-11},{top+340} Q{x+3},{top+350} {x-11},{top+360}',stroke='#c5d2dd',sw=2)
            s.text(x+width/2-11,top+355,ref+' · '+d['part'].replace('SN74',''),13,'white',weight='bold',anchor='middle')
            for p,(label,net,kind) in d['pins'].items():
                xx,yy=hole_xy(pin_hole(d,p),top);edge=top+370 if p<=d['count']//2 else top+330
                s.line([(xx,yy),(xx,edge)],'#606e78',5)
                s.text(xx,top+400 if p<=d['count']//2 else top+308,p,11,INK,anchor='middle')
                if net is None:
                    s.line([(xx-3,yy-3),(xx+3,yy+3)],'#8b8f92',1.4);s.line([(xx-3,yy+3),(xx+3,yy-3)],'#8b8f92',1.4)
            s.circle(x,top+362,3,'#ecbe61')
        for ref,d in c['parts'].items():
            a,b=[hole_xy(h,top) for h in d['holes'].values()]
            s.line([a,b],INK,2)
            mid=(a[0]+b[0])/2
            if ref.startswith('R'):
                s.rect(mid-24,a[1]-7,48,14,'#e8c98f',INK,2)
                s.text(mid,a[1]-18,ref+' 2.2 kΩ',13,anchor='middle')
            else:
                s.circle(mid,a[1],10,'#b58143' if ref!='C0' else '#416877',INK,1)
                s.text(mid,a[1]-20,ref,13,weight='bold',anchor='middle')
                if ref=='C0':s.text(a[0]-7,a[1]+26,'+',15,color('+5V'),weight='bold')
            for xx,yy in [a,b]:s.circle(xx,yy,3,INK)
        s.text(50,top+752,'TP/BP = +5V; TG/BG = GND · dots join; crossings without dots do not / точки соединяют; пересечения без точек — нет',14,MUTED)
        if old:s.text(490,top+80,'C0: 10 µF (+ marked / + отмечен); C1…: 100 nF. R1: 2.2 kΩ.',15,MUTED)
    s.text(40,1745,'A and B are separate builds; reuse the board / A и B — отдельные сборки; макетку можно использовать повторно.',17,MUTED)
    s.text(40,1775,'50 holes per power rail; split 25/26 bridged / По 50 отверстий в шине; разрывы 25/26 соединены перемычками.',16,MUTED)
    return s


def main():
    (OUT/'checks').mkdir(exist_ok=True)
    results={};allmodels={}
    for old in (True,False):
        edition='old' if old else 'new'
        circuits={e:circuit(old,e) for e in ('xor','dff')}
        layouts={e:make_layout(c) for e,c in circuits.items()}
        for e,c in circuits.items():results[edition+'_'+e]=validate_layout(c,layouts[e])
        drawings={'generic':draw_generic(old),'chips':draw_chips(old),'breadboard':draw_breadboards(old,circuits,layouts)}
        for kind,s in drawings.items():
            svg=OUT/f'{edition}_{kind}.svg';s.save(svg)
            subprocess.run(['inkscape',str(svg),'--export-type=png','--export-width=2300',
                            '--export-filename='+str(svg.with_suffix('.png'))],check=True,capture_output=True)
        allmodels[edition]={'circuits':circuits,'layouts':layouts}
        for e,layout in layouts.items():
            with (OUT/'checks'/f'{edition}_{e}_jumpers.csv').open('w') as f:
                writer=csv.DictWriter(f,fieldnames=['id','a','b','net','label','external']);writer.writeheader();writer.writerows(layout['wires'])
    (OUT/'checks/netlists.json').write_text(json.dumps(allmodels,indent=2,ensure_ascii=False)+'\n')
    results['source_sha256']={k:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in SOURCES.items()}
    (OUT/'checks/connectivity.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v for k,v in results.items() if k!='source_sha256'},indent=2))

if __name__=='__main__':main()
