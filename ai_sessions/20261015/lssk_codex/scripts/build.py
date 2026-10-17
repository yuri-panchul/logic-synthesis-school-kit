#!/usr/bin/env python3
"""Generate all deliverables offline from the reviewed model and HTML fragments."""
import csv,json,sys,math
from html import escape as esc
from pathlib import Path
from urllib.parse import quote
from model import *
def a(url,label):return f'<a href="{esc(url,quote=True)}">{esc(str(label))}</a>'
def src(keys):return ' · '.join(a(SOURCES[k][1],SOURCES[k][0]) for k in keys.split(','))
def sheetrow(n):return SHEET+'?range='+quote(f'LSSK!A{n}:Q{n}',safe='!')
def page(path,title,body,lang='en',script=''):
 prefix='../' if '/' in path else ''
 ru=lang=='ru'
 nav=[('index.html','Обзор' if ru else 'Overview'),('start_ru.html' if ru else 'start_en.html','Начало работы' if ru else 'Getting started'),('exercises.html','Упражнения' if ru else 'Exercises'),('sources.html','Источники и допущения' if ru else 'Sources & assumptions')]
 # A corresponding language edition is available for every authored page.
 partner='start_en.html' if path=='start_ru.html' else 'start_ru.html' if path=='start_en.html' else Path(path).stem+'_ru.html'
 switch=f'<a data-language-switch href="{partner}" lang="{"en" if ru else "ru"}">{"English version" if ru else "Русская версия"}</a>'
 html=f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Logic Synthesis School Kit: illustrated breadboard guides, exercise inventory and kit estimates."><title>{esc(title)} · LSSK</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body><a class="skip" href="#main">{'К содержанию' if ru else 'Skip to content'}</a><header><a class="brand" href="{prefix}index.html">LSSK / LOGIC SYNTHESIS SCHOOL KIT</a><nav aria-label="{'Навигация' if ru else 'Main navigation'}">{''.join(a(prefix+p,t) for p,t in nav)}</nav></header><main id="main">{body}</main><footer>{'Учебные материалы на основе программы Юрия Панчула' if ru else 'Teaching materials adapted from Yuri Panchul’s curriculum'} · {a('https://verilog-meetup.com/','Verilog Meetup')} · {DATE}. {'Расчётные комплектации; аппаратные схемы не проверены на макете.' if ru else 'Estimated inventories; hardware builds have not been bench-tested.'}</footer>{script}</body></html>'''
 html=html.replace('</nav>',switch+'</nav>')
 if ru:
  html=html.replace('LSSK / LOGIC SYNTHESIS SCHOOL KIT','LSSK / ШКОЛЬНЫЙ НАБОР ПО СИНТЕЗУ ЛОГИЧЕСКИХ СХЕМ').replace('Logic Synthesis School Kit: illustrated breadboard guides, exercise inventory and kit estimates.','Logic Synthesis School Kit: иллюстрированные инструкции, каталог упражнений и расчёт комплектации наборов.')
 (ROOT/path).write_text(html,encoding='utf-8')
def table(headers,rows):
 return '<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in r)+'</tr>' for r in rows)+'</tbody></table></div>'
def bomtable(bom,prices=False):
 rows=[]
 for p,q in bom.items():
  t=parts[p];source=a(sheetrow(t['row']),f'LSSK row {t["row"]}') if t['row'] else 'Requested in review1; budget price'
  if t['url']:source+=' · '+a(t['url'],'Part / supplier')
  qty=str(q)
  if t['pack']>1:qty+=f'<br><small>{q//t["pack"]} full packs × {t["pack"]}</small>' if q%t['pack']==0 else f'<br><small>Allocated from supplier lots of {t["pack"]}</small>'
  row=[esc(t['name']),qty,source]
  if prices:row += [f'${Decimal(t["price"]):.4f}',f'${money(Decimal(t["price"])*q):.2f}']
  rows.append(row)
 return table(['Component','Quantity (pieces)','Source']+(['USD / piece','Line USD'] if prices else []),rows)
def links(ids,prefix=''):
 return ', '.join(a(prefix+'exercises.html#'+id,id) for id in ids)

def generate_catalog():
 body=f'<p class="eyebrow">Teaching inventory / {len(E)} entries</p><h1>From the first gate<br>to microarchitecture.</h1><p class="lead">The union of the July exercise list and breadboard lessons 1.1–1.7 of the annual course. Duplicates are merged; distinct variants stay visible.</p><p class="source">{src("improved,course")}</p>'
 body+='''<div class="callout"><strong>How to use the counts.</strong> Each entry is a complete, estimated setup for one student or pair. Reuse parts between exercises. M–M and M–F counts are working allowances, including rails, fixed-input patch leads and signal wiring; kits add 25% and round up to 40-lead packs. Each LED bar contains eight current-limited LEDs. Button counts mean individual resistor-equipped modules. Classroom USB power and a multimeter are shared equipment.</div><p>The kit uses the specified 5 V LEDs, resistor-equipped buttons and assembled clock modules. The new single-FIFO variant adds the four TTP223 switches requested in the review. Counts are estimates for the named circuits; see <a href="sources.html">sources and counting assumptions</a>.</p>'''
 body+='''<div class="filter screen-only"><div><label for="search">Find an exercise, IC or topic</label><input id="search" type="search" placeholder="FIFO, 4013, comparator…"></div><div><label for="kit-filter">Kit coverage</label><select id="kit-filter"><option value="">All exercises</option>'''+''.join(f'<option value="{k}">{esc(v["title"])}</option>' for k,v in KITS.items())+'''</select></div><button type="button" onclick="window.print()">Print catalogue</button><p id="result-count" role="status"></p></div>'''
 body+='<ul class="jump-links">'+''.join('<li>'+a('#'+e['id'],e['id']+' · '+e['title'])+'</li>' for e in E)+'</ul>'
 for e in E:
  kits=[k for k,v in KITS.items() if e['id'] in v['ids']]
  body+=f'<article class="exercise" id="{e["id"]}" data-kits="{" ".join(kits)}"><p class="eyebrow">{e["id"]} / {esc(e["lesson"])}</p><h2>{esc(e["title"])}</h2><p>{esc(e["goal"])}</p><p><span class="tag">{esc(e["status"])}</span>'+''.join(a('kits/'+k+'.html',KITS[k]['title'])+' ' for k in kits)+'</p>'
  if e['note']:body+=f'<p class="callout">{esc(e["note"])}</p>'
  body+=bomtable(e['bom'])+f'<p class="source">Source occurrence: {src(e["src"])} · {esc(e["lesson"])}</p></article>'
 script='<script src="assets/catalog.js"></script>'
 page('exercises.html','Breadboard exercises',body,script=script)

def generate_kits():
 for key,k in KITS.items():
  c=k['cost'];b=k['bom']
  actions=f'<a class="button" href="{key}.csv">Download CSV</a><a class="button secondary" href="../exercises.html">Exercise catalogue</a><button onclick="window.print()">Print</button>'
  body=f'<p class="eyebrow">Kit {list(KITS).index(key)+1} / {len(KITS)} · one learner or pair</p><h1>{esc(k["title"])}</h1><p class="lead">{esc(k["description"])}</p><div class="actions">{actions}</div>' 
  body+='<div class="grid">'+''.join(f'<div class="card"><div class="metric">${c[x]:.2f}<small>{label}</small></div></div>' for x,label in [('materials','estimated component cost'),('loaded','cost with packing, labor and allowances'),('retail','suggested direct-sale price, before tax / delivery')])+'</div>'
  body+=f'<p><strong>Coverage:</strong> {links(k["ids"],"../")}. One exercise is assembled at a time; the inventory is the maximum quantity of each component across those exercises, not the sum of all exercises.</p>'
  body+=f'<p><strong>In the box:</strong> {b.get("board",0)} full-size boards, {b.get("button",0)} button modules, {b.get("touch",0)} self-locking touch switches, {b.get("clock",0)} assembled clock generator, {b.get("bar",0)} LED bars ({8*b.get("bar",0)} LEDs), {b.get("display",0)} seven-segment displays, {b.get("mm",0)} M–M and {b.get("mf",0)} M–F jumpers. Other indicators and tools are itemized below.</p>'
  if key=='comprehensive':body+='''<div class="callout caution"><strong>Includes the rare parts.</strong> CD40108 and CD40181 are budgeted at the spreadsheet’s historical $28.84 and $19.78 each, even though its quantity cells are zero. Availability is unverified. This is a complete curriculum inventory proposal, not a claim that a ready-to-ship kit is currently procurable. Custom FSM coverage is bounded to 2–4 input bits; open-ended CPU projects are outside the defined breadboard list.</div>'''
  if key=='basics':body+='''<div class="callout">This reusable inventory covers the article’s Basics list and the first-lesson De Morgan comparison. That list explicitly shows both operands and the result at once, so this kit has three 4511s, three displays and three boards. A single-display economy version would omit that exact exercise.</div>'''
  body+='<h2>Component inventory</h2>'+bomtable(b,True)
  body+='<h2>Cost and selling-price estimate</h2>'+table(['Item','USD / kit','Basis'],[
   ['Components',f'${c["materials"]:.2f}','Sum of rounded line extensions below / in CSV'],
   ['Inbound freight and procurement allowance',f'${c["freight"]:.2f}','15% of components'],
   ['Loss / replacement allowance',f'${c["replacement"]:.2f}','5% of components'],
   ['Packaging, labels and printed insert',f'${c["packaging"]:.2f}','Planning allowance'],
   ['Picking, packing and QA labor',f'${c["labor"]:.2f}',f'{k["minutes"]} minutes at $20/hour; validate on a pilot batch'],
   ['Loaded cost',f'${c["loaded"]:.2f}','Components + all above allowances'],
   ['Suggested direct-sale price',f'${c["retail"]:.2f}','ceil((loaded cost / (1 − 0.40 − 0.03)) / 5) × $5'],
   ['Payment fee at suggested price',f'${c["fee"]:.2f}','3% of retail'],
   ['Contribution after fee and loaded cost',f'${c["contribution"]:.2f}',f'{c["margin"]:.2f}% of retail; before fixed business overhead'],
   ['Loaded cost sensitivity',f'${c["low"]:.2f}–${c["high"]:.2f}','Component prices −25% to +50%; same labor and packaging'],
  ])
  body+='''<p class="small">USD planning model, source snapshot 14 October 2026. Spreadsheet prices are not live quotes; several are bulk/lot prices. CSV and HTML use the same Decimal calculations. Per-piece normalization preserves four decimals; line extensions round to cents before summation. Prices exclude customer delivery, sales tax, marketplace commissions above the assumed 3%, curriculum-development costs, insurance and fixed business overhead. A USB 5 V source and multimeter are supplied by the classroom. For a standalone retail bundle, add quotes for those before repricing.</p>'''
  if (ROOT/'data'/f'{key}_notes.html').exists():body+=(ROOT/'data'/f'{key}_notes.html').read_text()
  body+='<h2>Quantity and sourcing assumptions</h2><p>'+a('../sources.html','Source register, quantities and pricing assumptions')+'. '+src('sheet')+'</p>'
  page('kits/'+key+'.html',k['title']+' kit',body,script='<script src="../assets/fsm.js"></script>' if key=='fsm' else '')
  # Every CSV is independently useful: line items plus clearly typed costing records.
  headers=['record_type','kit','item_id','description','quantity','unit','pack_size','packs_to_buy','unit_cost_usd','extended_cost_usd','source_row','source_url','price_basis','notes']
  with (ROOT/'kits'/f'{key}.csv').open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=headers);w.writeheader()
   for p,q in b.items():
    t=parts[p];w.writerow(dict(record_type='component',kit=key,item_id=p,description=t['name'],quantity=q,unit='piece',pack_size=t['pack'],packs_to_buy=math.ceil(q/t['pack']),unit_cost_usd=f'{Decimal(t["price"]):.4f}',extended_cost_usd=f'{c["lines"][p]:.2f}',source_row=t['row'] or '',source_url=sheetrow(t['row']) if t['row'] else t['url'],price_basis='LSSK column J snapshot '+PRICE_DATE if t['row'] else 'User-requested TTP223; unverified budget price '+DATE,notes=t['note']))
   labels={'materials':'Component subtotal (do not add to component rows again)','freight':'Inbound allowance: 15% of components','replacement':'Replacement allowance: 5% of components','packaging':'Packaging allowance','labor':f'Labor: {k["minutes"]} minutes at USD 20/hour','loaded':'Loaded cost','retail':'Suggested direct-sale price; excludes tax and delivery','fee':'Payment fee: 3% of retail','contribution':'Contribution after fee and loaded cost','low':'Loaded cost with components -25%','high':'Loaded cost with components +50%'}
   for id,label in labels.items():w.writerow(dict(record_type='summary' if id in ['materials','loaded','retail','contribution','low','high'] else 'allowance',kit=key,item_id=id,description=label,extended_cost_usd=f'{c[id]:.2f}',price_basis='Estimate '+DATE,notes='Shared classroom USB source and multimeter excluded. Components reused between exercises.'))

def generate_index():
 body='''<p class="eyebrow">A practical bridge to chip design</p><h1>Build the logic.<br>See the state.</h1><p class="lead">Start with a gate on a breadboard. Move through registers, arbiters and queues—then carry those ideas into SystemVerilog and FPGA design.</p><div class="actions"><a class="button" href="start_en.html">Start in English →</a><a class="button secondary" href="start_ru.html" lang="ru">Начать по-русски →</a></div><figure><img src="assets/mat_gate2.jpg" width="1200" alt="A student’s breadboard project from Yuri Panchul’s introductory article"><figcaption>From the original July 23 illustrated notes. Photo: Yuri Panchul / Verilog Meetup.</figcaption></figure>'''
 body+=f'<div class="grid"><div class="card"><p class="eyebrow">01 / Learn</p><h2>Two illustrated guides</h2><p>The original hand-drawn notes, explained step by step in Russian and English, with verified DIP pin connections and first experiments.</p>{a("start_en.html","English guide")} · {a("start_ru.html","Русская инструкция")}</div><div class="card"><p class="eyebrow">02 / Teach</p><h2>{len(E)} exercise entries</h2><p>A merged curriculum with explicit quantities for logic chips, breadboards, buttons, indicators and both types of jumper.</p>{a("exercises.html","Browse the catalogue →")}</div></div><h2>Six kits. One clear cost model.</h2>'
 body+=table(['Kit','Coverage','Parts','Loaded cost','Suggested retail','Files'],[[a('kits/'+key+'.html',k['title']),str(len(k['ids']))+' entries',f'${k["cost"]["materials"]:.2f}',f'${k["cost"]["loaded"]:.2f}',f'${k["cost"]["retail"]:.2f}',a('kits/'+key+'.html','HTML')+' · '+a('kits/'+key+'.csv','CSV')] for key,k in KITS.items()])
 body+='''<div class="callout"><strong>Planning basis.</strong> One learner or pair builds one exercise at a time. All estimates are in USD, using the LSSK sheet snapshot of 14 October 2026 plus the separately labelled budget price for the user-requested TTP223 switches. Suggested retail includes a 40% target contribution margin after a 3% payment fee. Shared USB sources and meters are excluded.</div><p>These documents are available offline: keep this folder and its <code>assets</code> directory together. Images, styling, search and the custom FSM generator do not require a server. Supplier links and source articles require internet access.</p><p>Curriculum and original images: Yuri Panchul / <a href="https://verilog-meetup.com/">Verilog Meetup</a>. This adaptation adds inventory and price estimates. It is not a report of tested classroom hardware.</p><div class="actions"><a class="button secondary" href="sources.html">Sources, corrections and assumptions</a></div>'''
 body+='<h2>October 15 review documents</h2><ul><li>'+a('20261015_answers_to_all_questions_1.html','Answers to every review question')+'</li><li>'+a('issues_codex_is_confident_about.html','Confirmed issues')+'</li><li>'+a('otsebyatina_from_codex_possible_hallucinations.html','Unverified Codex additions')+'</li></ul>'
 page('index.html','Learning pack',body)

def main():
 generate_catalog();generate_kits();generate_index()
 for lang in ['en','ru']:page(f'start_{lang}.html','Начало работы' if lang=='ru' else 'Getting started',(ROOT/'data'/f'start_{lang}.html').read_text(),lang)
 page('sources.html','Sources and assumptions',(ROOT/'data/sources.html').read_text())
 for name,title in [('issues_codex_is_confident_about','Issues Codex is confident about'),('otsebyatina_from_codex_possible_hallucinations','Unverified Codex additions'),('20261015_answers_to_all_questions_1','Answers to review1')]:
  page(name+'.html',title,(ROOT/'data'/(name+'.html')).read_text())
 payload={'date':DATE,'price_snapshot_date':PRICE_DATE,'parts':parts,'exercises':E,'kits':KITS}
 (ROOT/'data/catalog.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str))
 from translate_ru import generate as generate_russian
 generate_russian()
 print(f'Generated 26 teaching HTML files, 6 CSVs and data/catalog.json; {len(E)} exercise entries.')
 for key,k in KITS.items():print(key,'components',k['cost']['materials'],'loaded',k['cost']['loaded'],'retail',k['cost']['retail'])
if __name__=='__main__':main()
