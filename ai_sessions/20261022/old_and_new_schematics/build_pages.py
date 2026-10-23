#!/usr/bin/env python3
"""Create the English/Russian readers for the six shared bilingual drawings."""
from pathlib import Path
from html import escape
import json

OUT=Path(__file__).resolve().parent
DATA=json.loads((OUT/'checks/netlists.json').read_text())
CHECKS=json.loads((OUT/'checks/connectivity.json').read_text())
CSS='''
:root{--ink:#233b49;--muted:#526978;--line:#d8e2e8;--accent:#096b67;--paper:#fff;--bg:#f0f4f6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 system-ui,sans-serif}header,main,footer{max-width:1500px;margin:auto;padding:26px}header{padding-top:42px}h1{font-size:clamp(30px,5vw,47px);line-height:1.12;max-width:28ch}h2{font-size:27px;line-height:1.3;margin-top:0}h3{font-size:20px}a{color:var(--accent);text-underline-offset:3px}.lead{font-size:21px;max-width:95ch}.meta,figcaption,.small{font-size:14px;color:var(--muted)}nav{display:flex;gap:12px 24px;flex-wrap:wrap;margin:20px 0}.section{background:white;border:1px solid var(--line);border-radius:12px;padding:26px;margin:22px 0;scroll-margin-top:15px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.grid>*{min-width:0}figure{margin:0;border:1px solid var(--line);border-radius:7px;overflow:hidden;background:#fff}figure img{width:100%;height:auto;display:block}figcaption{padding:14px 18px;border-top:1px solid var(--line)}.links{display:flex;gap:16px;flex-wrap:wrap;margin-top:8px}.note{border-left:4px solid #bb8c3e;background:#fff8eb;padding:14px 18px}.table{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:15px}td,th{border:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}th{background:#eaf1f4}code{font:0.9em ui-monospace,monospace;background:#ecf1f5;padding:2px 4px;overflow-wrap:anywhere}details{border:1px solid var(--line);padding:14px 18px;margin:14px 0;border-radius:6px}summary{font-weight:700;cursor:pointer}li{margin:8px 0}.swatch{display:inline-block;width:12px;height:12px;margin-right:5px;border-radius:50%}.checks{padding:12px 16px;background:#edf7f1;border-left:4px solid #288163}footer{padding-bottom:45px}@media(max-width:850px){.grid{grid-template-columns:1fr}header,main,footer{padding:16px}.section{padding:18px}table{min-width:620px}}@media print{body{background:white;font-size:10pt}header,main,footer{max-width:none;padding:0}nav,.lang{display:none}.section{border:0;padding:12px 0}.grid{display:block}figure{break-inside:avoid;margin-bottom:20px}figure img{max-height:235mm;object-fit:contain}h2,h3{break-after:avoid}.table{overflow:visible}table{font-size:9pt;min-width:0}tr{break-inside:avoid}a{color:inherit}}
'''

def link(url,label):return f'<a href="{escape(url,quote=True)}">{label}</a>'

def build(ru):
    def t(en,other):return other if ru else en
    lang='ru' if ru else 'en'
    title=t('Old and new getting-started schematics','Схемы старой и новой вводной инструкции')
    b=[f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header>',
       '<p class="lang">'+link('old_and_new_en.html' if ru else 'old_and_new_ru.html','English' if ru else 'Русский')+'</p>',
       '<p class="meta">LSSK · 2026-10-22</p>',f'<h1>{title}</h1>']
    def p(en,other,cls=''):b.append(f'<p class="{cls}">'+t(en,other)+'</p>')
    def section(key,en,other):b.append(f'<section class="section" id="{key}"><h2>'+t(en,other)+'</h2>')
    def end():b.append('</section>')
    def table(head,rows):
        b.append('<div class="table"><table><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in head)+'</tr></thead><tbody>')
        for row in rows:b.append('<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>')
        b.append('</tbody></table></div>')
    p('Six drawings compare the archived 14 October guide with the current guide at three levels: generic logic, numbered chip connections, and breadboard placement. Every drawing has two independent panels: A is the XOR experiment; B is the later one-bit memory experiment.',
      'Шесть рисунков сравнивают архивную инструкцию от 14 октября с текущей на трёх уровнях: общая логическая схема, соединения выводов микросхем и размещение на макетке. В каждом рисунке две независимые панели: A — опыт XOR, B — последующий опыт с памятью на один бит.','lead')
    p(link('../start_'+lang+'.html',t('Archived guide','Архивная инструкция'))+' · '+link('../../start_'+lang+'.html',t('Current guide','Текущая инструкция'))+' · '+link('../20261022_task.md',t('Original task','Исходное задание')),
      link('../start_'+lang+'.html','Архивная инструкция')+' · '+link('../../start_'+lang+'.html','Текущая инструкция')+' · '+link('../20261022_task.md','Исходное задание'))
    b.append('<nav aria-label="'+t('Contents','Содержание')+'">'+''.join(link('#'+key,t(en,r)) for key,en,r in [
        ('differences','What changed','Что изменилось'),('generic','1 · Generic','1 · Общая схема'),('chips','2 · Chips','2 · Микросхемы'),
        ('breadboard','3 · Breadboard','3 · Макетка'),('connections','Exact connections','Точные соединения'),('checks','Checks and sources','Проверки и источники')])+'</nav></header><main>')
    section('differences','What changes between editions','Что изменилось между редакциями')
    table([t('Element','Элемент'),t('Old guide · 14 October','Старая · 14 октября'),t('Current guide','Текущая')],[
        [t('XOR output','Выход XOR'),'CD4070 → SN74HCT244 → 2.2 kΩ → 5 V LED','CD4070 → 5 V LED'],
        [t('Flip-flop output','Выход триггера'),'CD4013 Q → SN74HCT244 → 2.2 kΩ → 5 V LED','CD4013 Q → 5 V LED'],
        [t('Clock path','Путь такта'),'555 OUT → HCT14 (1→2) → HCT14 (3→4) → CD4013 CLK','555 OUT → CD4013 CLK'],
        [t('External capacitors','Внешние конденсаторы'),t('100 nF per IC, plus one polarized 10 µF per build.','100 нФ у каждой ИС, плюс один полярный 10 мкФ на сборку.'),t('Not specified in this edition; none added to the drawing.','В этой редакции не заданы; в рисунок не добавлены.')],
        [t('ICs installed in A / B','Микросхем в A / B'),'2 / 3','1 / 1'],
        [t('Logical behavior','Логическое поведение'),t('XOR truth table; rising-edge D sampling; asynchronous active-high reset.','Таблица XOR; выборка D по положительному фронту; асинхронный сброс единицей.'),t('The same intended logical behavior.','То же предусмотренное логическое поведение.')],
    ])
    p('These are reconstructions of the two texts. Panel B replaces the XOR experiment; it is not wired to panel A. References such as U1 and C1 restart in each panel. The alternative AND/OR/inverter substitutions and optional /Q observation are not additional assembled circuits here.',
      'Это восстановление схем по двум текстам. Панель B заменяет опыт XOR, а не соединяется с панелью A. Обозначения U1, C1 и другие начинаются заново в каждой панели. Замены XOR на AND/OR/инвертор и необязательное наблюдение /Q здесь не являются дополнительными собранными схемами.')
    p('One indicator channel is shown. The old guide’s list provisions eight 2.2 kΩ resistors for the full observer, but its first-channel instructions use only R1; the seven unused buffer inputs are grounded and their outputs are unconnected. LED1 means the specified current-limited 5 V LED, or channel 0 of the passive common-cathode 5 V LED bar. Its existing internal current limiting is part of that component.',
      'Показан один канал индикации. В старом списке предусмотрены восемь резисторов 2,2 кОм для полного узла наблюдения, но инструкция первого канала использует только R1; семь неиспользуемых входов буфера заземлены, выходы свободны. LED1 — указанный светодиод на 5 В с ограничением тока либо канал 0 пассивной гребёнки на 5 В с общим катодом. Имеющееся внутреннее ограничение тока входит в сам компонент.','note')
    end()
    for kind,num,en,r in [('generic',1,'Generic logic','Общая логическая схема'),('chips',2,'Connections between chips','Соединения между микросхемами'),('breadboard',3,'Placement and wiring on a breadboard','Размещение и провода на макетке')]:
        section(kind,f'{num}. {en}',f'{num}. {r}')
        descriptions={
            'generic':('XOR, a positive-edge D flip-flop, asynchronous RESET, the old buffer and two Schmitt inverters are shown without chip-specific pin numbers. The old power capacitors are shown separately below the logic.','XOR, D-триггер по положительному фронту, асинхронный RESET, старый буфер и два инвертора Шмитта показаны без привязки к выводам конкретной ИС. Старые конденсаторы питания показаны отдельно под логикой.'),
            'chips':('Signal wires carry actual pin numbers. The lists under each circuit specify power, every grounded unused input and every unconnected output. Pin locations in this drawing are schematic, not a physical package view.','Сигнальные соединения подписаны настоящими номерами выводов. Списки под схемами задают питание, все заземлённые свободные входы и все неподключённые выходы. Положение выводов здесь условное, не вид корпуса.'),
            'breadboard':('Each panel is a complete separate layout with shared five-hole strips, explicit rail bridges and component pins. The connection tables below give exact holes. Open SVG for inspection at any zoom.','Каждая панель — самостоятельная сборка с объединёнными пятёрками отверстий, явными перемычками шин и выводами деталей. Таблицы ниже задают точные отверстия. Для любого увеличения откройте SVG.'),
        }
        p(*descriptions[kind])
        b.append('<div class="grid">')
        for edition,enlabel,rulabel in [('old','Old guide','Старая инструкция'),('new','Current guide','Текущая инструкция')]:
            base=f'{edition}_{kind}'
            alt=t(f'{enlabel}: {en}; panel A XOR, panel B D flip-flop.',f'{rulabel}: {r}; панель A XOR, панель B D-триггер.')
            b.append('<figure><a href="'+base+'.svg"><img src="'+base+'.png" alt="'+escape(alt,quote=True)+'" loading="lazy"></a><figcaption><strong>'+t(enlabel,rulabel)+'</strong><div class="links">'+link(base+'.svg','SVG')+' · '+link(base+'.png','PNG')+'</div></figcaption></figure>')
        b.append('</div>')
        if kind=='breadboard':
            b.append('<ul>')
            for en,r in [
                ('The DIP notch faces LEFT. Pin 1 is the lower-left pin on row f; the highest-numbered pin is directly above it on row e. Each chip straddles the trench.','Выемка DIP обращена ВЛЕВО. Вывод 1 — снизу слева, в ряду f; вывод с наибольшим номером — прямо над ним в ряду e. Каждая ИС пересекает канавку.'),
                ('a–e at one column form one contact; f–j form another. The trench separates them. TP/BP are top/bottom positive rails; TG/BG are top/bottom ground rails. Rail numbering belongs to this drawing.','a–e одного столбца образуют контакт; f–j — другой. Канавка разделяет их. TP/BP — верхняя/нижняя положительные шины, TG/BG — верхняя/нижняя земля. Нумерация шин относится к этому рисунку.'),
                ('The illustrated rail has 50 holes and a break between 25 and 26. Four short bridges join the halves; two long jumpers connect top and bottom rails. Match these to the continuity of the actual board.','На изображённой шине 50 отверстий и разрыв между 25 и 26. Четыре короткие перемычки соединяют половины; две длинные — верхние и нижние шины. Сопоставьте их с реальной связностью вашей платы.'),
                ('PWR shows the regulated 5 V output connection. Its input path is USB 5 V → 9 V boost cable → breadboard regulator set to 5 V. Only the regulated output feeds the logic.','PWR показывает подключение выхода стабилизированных 5 В. До него: USB 5 В → повышающий кабель 9 В → модуль питания макетки, установленный на 5 В. Логику питает только стабилизированный выход.'),
                ('External modules are drawn by terminal names, not a guaranteed connector pin order. Use the actual VCC, GND and OUT markings. Lines connect at endpoint dots; a crossing without a dot is not a connection.','Внешние модули показаны по именам контактов, без гарантии порядка ножек разъёма. Используйте реальные метки VCC, GND и OUT. Соединение обозначено точкой конца провода; пересечение без точки не соединяет.'),
                ('Power off while rewiring. Build either A or B, connect rails and fixed input levels, then signals, and check against the hole table before power-on.','Переподключайте при выключенном питании. Соберите A или B: сначала шины и постоянные уровни входов, затем сигналы; перед включением сверьте отверстия с таблицей.'),
            ]:b.append('<li>'+t(en,r)+'</li>')
            b.append('</ul>')
            p('<span class="swatch" style="background:#bf3148"></span>+5V · <span class="swatch" style="background:#28629f"></span>GND · <span class="swatch" style="background:#11806c"></span>data / result · <span class="swatch" style="background:#7a4bac"></span>B / RESET · <span class="swatch" style="background:#ad6c04"></span>clock',
              '<span class="swatch" style="background:#bf3148"></span>+5V · <span class="swatch" style="background:#28629f"></span>GND · <span class="swatch" style="background:#11806c"></span>данные / результат · <span class="swatch" style="background:#7a4bac"></span>B / RESET · <span class="swatch" style="background:#ad6c04"></span>такт')
        end()
    section('connections','Pin assignments and exact jumper endpoints','Назначение выводов и точные концы перемычек')
    p('The lead counts below include six rail bridges and all external-module leads, including the two PWR output leads. Component legs are not counted as jumpers. These are counts for these particular layouts, not revised kit-shopping quantities.',
      'В числа ниже входят шесть перемычек шин и все провода внешних модулей, включая два выходных провода PWR. Ножки деталей не считаются перемычками. Это количества для данных рисунков, а не новый список покупки наборов.')
    for edition in ('old','new'):
        for exp in ('xor','dff'):
            c=DATA[edition]['circuits'][exp];layout=DATA[edition]['layouts'][exp]
            title_=t('Old' if edition=='old' else 'Current','Старая' if edition=='old' else 'Текущая')+' · '+('A / XOR' if exp=='xor' else 'B / D FF')
            b.append('<details><summary>'+title_+' · '+str(len(layout['wires']))+t(' jumper leads',' проводов-перемычек')+'</summary>')
            b.append('<h3>'+t('Parts and placement','Компоненты и размещение')+'</h3>')
            rows=[]
            for ref,d in c['chips'].items():
                rows.append([ref,d['part'],t('Pin 1 at ','Вывод 1 в ')+f'<code>f{d["col"]}</code>'])
            for ref,d in c['parts'].items():
                holes=' ↔ '.join('<code>'+escape(h)+'</code>' for h in d['holes'].values())
                comment=(t(' near ',' у ')+d['near']) if 'near' in d else ''
                if ref=='C0':comment=t(' · + at b3, − at b4',' · + в b3, − в b4')
                rows.append([ref,d['value'],holes+comment])
            table([t('Reference','Позиция'),t('Part / value','Тип / номинал'),t('Placement','Размещение')],rows)
            b.append('<h3>'+t('All pins','Все выводы')+'</h3>')
            rows=[]
            for ref,d in c['chips'].items():
                for pin,(label,net,kind) in d['pins'].items():
                    ep=layout['endpoints'][f'{ref}.{pin}']
                    rows.append([f'{ref}.{pin}',escape(label),'<code>'+ep['hole']+'</code>',escape(net) if net else t('NC — leave open','NC — не подключать')])
            table([t('Pin','Вывод'),t('Function','Функция'),t('Hole','Отверстие'),t('Net','Цепь')],rows)
            b.append('<h3>'+t('Jumper list','Список перемычек')+'</h3>')
            p(link(f'checks/{edition}_{exp}_jumpers.csv','CSV'),link(f'checks/{edition}_{exp}_jumpers.csv','CSV'))
            rows=[[w['id'],'<code>'+escape(w['a'])+'</code>','<code>'+escape(w['b'])+'</code>',escape(w['net'])] for w in layout['wires']]
            table(['ID',t('End 1','Конец 1'),t('End 2','Конец 2'),t('Net','Цепь')],rows)
            b.append('</details>')
    end()
    section('checks','Checks, scope and references','Проверки, границы и источники')
    p('All four layouts passed a breadboard connectivity check: no shared occupied hole, no short between distinct nets, every required net connected across strips and rail bridges, and every unused output isolated. Active pin paths and chip orientation were also checked. Both source guides remain unchanged. This is a drawing/netlist verification; no physical build or analog timing/current measurement was performed.',
      'Все четыре сборки прошли проверку связности макетки: нет двух выводов/проводов в одном отверстии, замыканий разных цепей, пропущенных соединений через контакты и шины; каждый свободный выход изолирован. Проверены активные пути выводов и ориентация ИС. Обе исходные инструкции не изменены. Это проверка рисунков и цепей, без физической сборки и измерений задержек/токов.','checks')
    p(link('checks/connectivity.json',t('Check results and source hashes','Результаты и хеши исходников'))+' · '+link('checks/netlists.json',t('Complete pin/wiring model','Полная модель выводов и проводов'))+' · '+link('build_schematics.py',t('Drawing generator','Генератор схем'))+' · '+link('build_pages.py',t('Page generator','Генератор страниц')),
      link('checks/connectivity.json','Результаты и хеши исходников')+' · '+link('checks/netlists.json','Полная модель выводов и проводов')+' · '+link('build_schematics.py','Генератор схем')+' · '+link('build_pages.py','Генератор страниц'))
    p('Pin numbers were checked against the manufacturer pinout drawings: '+link('https://www.ti.com/lit/ds/symlink/cd4070b.pdf','CD4070B (p. 2)')+' · '+link('https://www.ti.com/lit/ds/symlink/cd4013b.pdf','CD4013B (p. 3)')+' · '+link('https://www.ti.com/lit/ds/symlink/sn74hct244.pdf','SN74HCT244 (p. 3)')+' · '+link('https://www.ti.com/lit/ds/symlink/sn74hct14.pdf','SN74HCT14 (p. 3)')+'.',
      'Номера выводов сверены с рисунками производителя: '+link('https://www.ti.com/lit/ds/symlink/cd4070b.pdf','CD4070B (стр. 2)')+' · '+link('https://www.ti.com/lit/ds/symlink/cd4013b.pdf','CD4013B (стр. 3)')+' · '+link('https://www.ti.com/lit/ds/symlink/sn74hct244.pdf','SN74HCT244 (стр. 3)')+' · '+link('https://www.ti.com/lit/ds/symlink/sn74hct14.pdf','SN74HCT14 (стр. 3)')+'.')
    p('The six vector drawings and six PNG renders are shared by both language pages. Diagram labels are bilingual; reference designators, signal names and hole coordinates are identical.',
      'Обе языковые страницы используют общие шесть векторных рисунков и шесть PNG. Подписи рисунков двуязычны; позиции, имена сигналов и координаты отверстий совпадают.')
    end()
    b.append('</main><footer>'+t('Original lessons: Yuri Panchul / Verilog Meetup. Diagrams reconstructed by Codex from the archived and current local guides.','Исходные уроки: Юрий Панчул / Verilog Meetup. Схемы восстановлены Codex по архивной и текущей локальным инструкциям.')+'</footer></body></html>')
    (OUT/f'old_and_new_{lang}.html').write_text('\n'.join(b)+'\n')
    print(OUT/f'old_and_new_{lang}.html')

if __name__=='__main__':
    build(False)
    build(True)
