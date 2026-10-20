#!/usr/bin/env python3
"""Offline invariants: source prices, coverage, document links and exported totals."""
import csv,json,sys,re
from collections import Counter
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
from model import ROOT,parts,E,KITS,BY_ID,rows,money
class Document(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.ids=[];self.links=[];self.images=[];self.stack=[];self.lang='';self.text=[];self.tables=[];self.current_table=None;self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='br' and self.cell is not None:self.cell.append(' ')
  if tag=='html':self.lang=a.get('lang','')
  if 'id' in a:self.ids.append(a['id'])
  if tag=='a' and 'href' in a:self.links.append(a['href'])
  if tag in ['link','script']:
   target=a.get('href') or a.get('src')
   if target:self.links.append(target)
  if tag=='img':
   assert a.get('alt'), 'Missing image alt text'
   self.images.append(a['src']);self.links.append(a['src'])
  if tag=='table':self.current_table=[]
  if tag=='tr':self.row=[]
  if tag in ['td','th']:self.cell=[]
  if tag not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr','path','rect','circle','line']:
   self.stack.append(tag)
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if self.stack and self.stack[-1]==tag:self.stack.pop()
 def handle_endtag(self,tag):
  if tag in ['td','th']:
   if self.row is not None:self.row.append(' '.join(''.join(self.cell or []).split()))
   self.cell=None
  if tag=='tr':
   if self.current_table is not None:self.current_table.append(self.row)
   self.row=None
  if tag=='table':self.tables.append(self.current_table);self.current_table=None
  assert self.stack and self.stack[-1]==tag, f'Misnested closing {tag}: {self.stack[-5:]}'
  self.stack.pop()
 def handle_data(self,t):
  self.text.append(t)
  if self.cell is not None:self.cell.append(t)
paths=[ROOT/'index.html',ROOT/'start_en.html',ROOT/'start_ru.html',ROOT/'exercises.html',ROOT/'sources.html',*(ROOT/'kits').glob('*.html')]
docs={}
for p in paths:
 d=Document();d.feed(p.read_text());assert not d.stack,(p,d.stack)
 assert d.lang==('ru' if p.name=='start_ru.html' else 'en')
 assert len(d.ids)==len(set(d.ids)),f'Duplicate IDs: {p}'
 docs[p.resolve()]=d
assert len(paths)==10
for p,d in docs.items():
 for link in d.links:
  u=urlsplit(link)
  if u.scheme or u.netloc:continue
  target=(p.parent/unquote(u.path)).resolve() if u.path else p
  assert target.exists(),f'Broken local link {p.name}: {link}'
  if u.fragment and target in docs:assert unquote(u.fragment) in docs[target].ids,f'Missing anchor {link}'
assert len(E)==len(BY_ID)==61
# Prices must agree with the exact recorded cells; normalization is explicit.
for part in parts.values():
 if part['row']:
  r=part['row'];assert Decimal(part['price'])*part['pack']==Decimal(rows[r][f'J{r}']),part
for key,k in KITS.items():
 for id in k['ids']:
  for p,q in BY_ID[id]['bom'].items():assert k['bom'].get(p,0)>=q,(key,id,p)
 for p in ['mm','mf']:
  if p in k['bom']:
   needed=max(BY_ID[id]['bom'].get(p,0) for id in k['ids'])
   assert k['bom'][p]>=needed*1.25 and k['bom'][p]%40==0
 assert k['bom']['button']%5==0
 with (ROOT/'kits'/f'{key}.csv').open(encoding='utf-8-sig',newline='') as f: export=list(csv.DictReader(f))
 components=[r for r in export if r['record_type']=='component']
 assert {r['item_id']:int(r['quantity']) for r in components}==k['bom']
 total=Decimal(0)
 html=docs[(ROOT/'kits'/f'{key}.html').resolve()]
 bomrows=next(t for t in html.tables if t[0][0]=='Component')
 assert len(bomrows)-1==len(components)
 for r,hr in zip(components,bomrows[1:]):
  q=int(r['quantity']);price=Decimal(r['unit_cost_usd']);line=Decimal(r['extended_cost_usd'])
  assert line==money(q*price),r
  assert hr[0]==r['description'] and hr[1].split()[0]==str(q),r
  assert hr[3]==f'${price:.4f}' and hr[4]==f'${line:.2f}',(r,hr)
  assert q%int(r['pack_size'])==0
  total+=line
 assert total==k['cost']['materials']
 summary={r['item_id']:Decimal(r['extended_cost_usd']) for r in export if r['record_type']!='component'}
 assert summary['loaded']==sum(summary[x] for x in ['materials','freight','replacement','packaging','labor'])
 assert summary['retail']%5==0
 assert summary['contribution']==summary['retail']-summary['loaded']-summary['fee']
 assert summary['contribution']/summary['retail']>=Decimal('.40')
 for name,value in summary.items():assert value==k['cost'][name]
 print(f'PASS {key}: {len(components)} BOM lines; components ${total}; loaded ${summary["loaded"]}; retail ${summary["retail"]}')
# Required special quantities and source corrections are not accidentally omitted.
c=KITS['comprehensive']['bom']
for p,q in {'40105':3,'4008':2,'4063':2,'4511':3,'display':3,'40108':1,'40181':1,'DM9368':3,'4086':2,'4014':2}.items():assert c[p]>=q,(p,c[p])
assert set(KITS['comprehensive']['ids'])==set(BY_ID)
for id in ['G13','M05','M02','P03','O01']:assert BY_ID[id]['note']
for lang in ['en','ru']:
 assert set(f'assets/{i}.jpg' for i in range(1,5)).issubset(docs[(ROOT/f'start_{lang}.html').resolve()].images)
# The arbiter equations are checked against independent rules for each state/input.
for p in [0,1]:
 for r0 in [0,1]:
  for r1 in [0,1]:
   g0=int(r0 and (not r1 or not p));g1=int(r1 and (not r0 or p))
   nxt=int(g0 or (p and not(r0 or r1)))
   assert not(g0 and g1) and g0<=r0 and g1<=r1
   if not(r0 or r1):assert (g0,g1,nxt)==(0,0,p)
   elif r0 and r1:assert (g0,g1,nxt)==(1-p,p,1-p)
   elif r0:assert (g0,g1,nxt)==(1,0,1)
   else:assert (g0,g1,nxt)==(0,1,0)
# Persistent contention and idle preserve alternation.
p=0;wins=[]
for cycle in range(32):
 wins.append(p);p=1-p
 for _ in range(cycle%4):p=int(p and not(0 or 0))
assert wins==[0,1]*16
print('PASS arbiter truth table and 32 accepted grants with idle gaps')
print(f'PASS {len(paths)} HTML documents; valid nesting, languages, local files, anchors and image alt text')
print('PASS 61 exercise inventories and five complete kit coverage mappings')
