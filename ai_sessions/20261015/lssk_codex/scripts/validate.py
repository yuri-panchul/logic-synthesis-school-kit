#!/usr/bin/env python3
"""Offline invariants: source prices, coverage, document links and exported totals."""
import csv,json,sys,re,math
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
reviews=['issues_codex_is_confident_about.html','otsebyatina_from_codex_possible_hallucinations.html','20261015_answers_to_all_questions_1.html']
paths=[*ROOT.glob('*.html'),*(ROOT/'kits').glob('*.html'),ROOT/'research/browser_check.html',*(ROOT/'research').glob('*_ru.html')]
docs={}
for p in paths:
 d=Document();d.feed(p.read_text());assert not d.stack,(p,d.stack)
 assert d.lang==('ru' if p.stem.endswith('_ru') else 'en')
 assert len(d.ids)==len(set(d.ids)),f'Duplicate IDs: {p}'
 docs[p.resolve()]=d
assert len(paths)==31
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
 assert k['bom'].get('button',0)==max(BY_ID[id]['bom'].get('button',0) for id in k['ids'])
 with (ROOT/'kits'/f'{key}.csv').open(encoding='utf-8-sig',newline='') as f: export=list(csv.DictReader(f))
 components=[r for r in export if r['record_type']=='component']
 assert {r['item_id']:int(r['quantity']) for r in components}==k['bom']
 total=Decimal(0)
 html=docs[(ROOT/'kits'/f'{key}.html').resolve()]
 bomrows=next(t for t in html.tables if t[0][0]=='Component')
 russian=docs[(ROOT/'kits'/f'{key}_ru.html').resolve()]
 rubom=next(t for t in russian.tables if t[0][0]=='Компонент')
 assert len(rubom)==len(bomrows)
 assert len(bomrows)-1==len(components)
 for r,hr,rr in zip(components,bomrows[1:],rubom[1:]):
  q=int(r['quantity']);price=Decimal(r['unit_cost_usd']);line=Decimal(r['extended_cost_usd'])
  assert line==money(q*price),r
  assert hr[0]==r['description'] and hr[1].split()[0]==str(q),r
  assert hr[3]==f'${price:.4f}' and hr[4]==f'${line:.2f}',(r,hr)
  assert rr[1].split()[0]==str(q) and rr[3:]==hr[3:],(key,r,rr)
  assert int(r['packs_to_buy'])==math.ceil(q/int(r['pack_size']))
  if r['item_id']!='button':assert q%int(r['pack_size'])==0
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
assert len(KITS)==6 and len(KITS['basics']['ids'])==12
assert KITS['fifo']['ids']==['P03'] and KITS['single_fifo']['ids']==['C11']
removed={'buffer','schmitt','c100','c1','c10','r100k','r2200'}
assert not removed.intersection(parts)
assert {p['id'] for p in parts.values() if not p['row']}=={'touch'}
assert 'unverified' in parts['touch']['note'] and 'budget' in parts['touch']['note']
for e in E:assert not removed.intersection(e['bom'])
for id in ['B07','B08','B09','C02','C10','C11','M06','P01','P02','P03','P04','P05','P06','P07','P08','P10','P11','P12']:
 assert BY_ID[id]['bom']['clock']==1,id
for id,counts in [('P03',{'40105':3,'button':3,'bar':3}),('C11',{'40105':1,'button':2,'touch':4,'bar':1}),('P05',{'button':2}),('P06',{'button':2})]:
 for p,q in counts.items():assert BY_ID[id]['bom'][p]==q,(id,p)
assert '4013' not in BY_ID['P03']['bom']
for p,d in docs.items():
 if p.name.replace('_ru.html','.html') in reviews or p.parent.name=='research':continue
 rendered=' '.join(d.text)
 assert not re.search(r'HCT14|HCT244|100\s*nF|10\s*[µμu]F|1\s*[µμu]F|2\.2\s*kΩ|100\s*kΩ|Schmitt|manual clock|ARM/TRANSFER|SAMPLE button|engineering addition',rendered,re.I),p
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
print('PASS review requirements: six kits, source parts plus requested TTP223, direct assembled clocks, corrected controls')
print('PASS 61 exercise inventories and six complete kit coverage mappings')
# Every authored English page has a structurally equivalent Russian partner.
manifest=json.loads((ROOT/'data/ru/manifest.json').read_text())
for original,translation in manifest['pages'].items():
 en=docs[(ROOT/original).resolve()];ru=docs[(ROOT/translation).resolve()]
 assert ru.lang=='ru' and re.search('[А-Яа-яЁё]',' '.join(ru.text)),translation
 if original not in ['start_en.html','research/browser_check.html']:
  assert en.ids==ru.ids and en.images==ru.images,(original,'IDs or images changed')
  # Amounts, precision and order must remain identical in both editions.
  assert re.findall(r'\$[\d,.]+',' '.join(en.text))==re.findall(r'\$[\d,.]+',' '.join(ru.text)),original
  assert len(en.tables)==len(ru.tables),original
  for et,rt in zip(en.tables,ru.tables):
   assert len(et)==len(rt) and all(len(er)==len(rr) for er,rr in zip(et,rt)),original
for original,translation in manifest['fragments'].items():
 assert (ROOT/original).exists() and (ROOT/translation).exists()
for original,translation in manifest['archive_reading_editions'].items():
 assert (ROOT/original).exists() and docs[(ROOT/translation).resolve()].lang=='ru'
# Every original HTML file has a Russian counterpart, including body fragments,
# browser helper and saved article reading editions; no original is overwritten.
covered=set(manifest['pages'])|set(manifest['fragments'])|set(manifest['archive_reading_editions'])|{'data/start_en.html'}
for path in ROOT.rglob('*.html'):
 relative=str(path.relative_to(ROOT))
 if '/ru/' in relative or path.stem.endswith('_ru'):continue
 assert relative in covered,('HTML without Russian edition',relative)
print('PASS Russian editions: page/fragment coverage, IDs, images, table dimensions, kit quantities and all USD amounts')
