#!/usr/bin/env python3
"""Generate the separate English/Russian 40105 proposal from shared circuit data."""
import json
from decimal import Decimal
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'research/fifo_40105_proposal'
SHEET = 'https://docs.google.com/spreadsheets/d/1ULTF4ocT2YyJowGakEOEVTsIUBTxLMkqXyvZM56vlU8/edit'
PDF = 'https://www.ti.com/lit/ds/symlink/'


def link(url, label):
    return f'<a href="{esc(url, quote=True)}">{label}</a>'


def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join(
        f'<th scope="col">{h}</th>' for h in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join(f'<td>{cell}</td>' for cell in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def timing(ru):
    title = 'Один цикл при W = R = 1' if ru else 'One cycle with W = R = 1'
    description = ('Фаза 0: захват входов. Фаза 2: спад SO, чтение. Фаза 5: фронт SI, запись. '
                   'Фаза 8: обновление счётчика заполнения.' if ru else
                   'Phase 0 captures inputs. Phase 2 lowers SO to read. Phase 5 raises SI to write. Phase 8 updates occupancy.')
    svg = f'<svg viewBox="0 0 940 290" role="img" aria-labelledby="timing-title timing-desc"><title id="timing-title">{title}</title><desc id="timing-desc">{description}</desc>'
    svg += '<rect width="940" height="290" fill="#fff" rx="10"/>'
    for step in range(10):
        x=155+step*74
        svg+=f'<rect x="{x}" y="12" width="74" height="260" fill="{"#edf5f1" if step%2==0 else "#fff"}"/>'
        svg+=f'<text x="{x+28}" y="32" font-size="14" fill="#526775">{step}</text>'
    for row,(label,active,invert) in enumerate([('clk = PH0',0,False),('SO',2,True),('SI',5,False),('COUNT = PH8',8,False)]):
        baseline=83+row*56
        svg+=f'<text x="14" y="{baseline-4}" font-size="15" fill="#152c3c">{label}</text>'
        values=[int((i==active)^invert) for i in range(10)]
        path=f'M 155 {baseline-24*values[0]}'
        for step,value in enumerate(values):
            path+=f' H {155+(step+1)*74}'
            if step<9:path+=f' V {baseline-24*values[step+1]}'
        svg+=f'<path d="{path}" stroke="#087c79" stroke-width="3" fill="none"/>'
    return '<figure class="timing">'+svg+'</svg><figcaption>'+description+'</figcaption></figure>'


def document(ru=False):
    def t(en, russian):return russian if ru else en
    title=t('A 40105 implementation of the RTL FIFO','Реализация RTL FIFO на микросхемах 40105')
    partner='fifo_40105_proposal.html' if ru else 'fifo_40105_proposal_ru.html'
    index='index_ru.html' if ru else 'index.html'
    provenance=json.loads((OUT/'provenance.json').read_text())
    validation=json.loads((OUT/'validation.json').read_text())
    b=f'<p class="eyebrow">LSSK / {t("Circuit proposal · 17 October 2026", "Предложение схемы · 17 октября 2026")}</p><h1>{title}</h1>'
    b+='<p class="lead">'+t(
        'Use two CD74HC40105E chips in parallel for the original <strong>8-bit × 10-word</strong> configuration. Capture the inputs, perform a read before a write, and use an occupancy counter for the ten-word limit. The debug interface is omitted.',
        'Для исходной конфигурации <strong>8 бит × 10 слов</strong> нужны две CD74HC40105E, работающие параллельно. Входы фиксируются в регистрах, чтение выполняется перед записью, а счётчик заполнения задаёт предел в десять слов. Отладочного интерфейса нет.')+'</p>'
    b+='<div class="callout caution"><strong>'+t('Scope of equivalence. ','Границы эквивалентности. ')+'</strong>'+t(
        'This proposal matches FIFO transactions at shared sampling edges for valid requests. It uses a 10-phase clock derived from the assembled clock module; it is <strong>not a drop-in replacement driven by an arbitrary external clock</strong>. Data and flags settle during the cycle rather than immediately after its first edge. The circuit has been checked with a behavioral model, not built on a breadboard.',
        'Предложенная схема воспроизводит операции FIFO на общих фронтах выборки при допустимых запросах. Используется десятифазный цикл от готового тактового модуля; это <strong>не замена, которую можно подключить к произвольному внешнему такту без изменений</strong>. Данные и флаги устанавливаются в течение цикла, а не сразу после его первого фронта. Схема проверена поведенческим моделированием, но на макетной плате не собиралась.')+'</div>'
    b+='<div class="grid"><div class="card"><h2>8 × 10</h2><p>'+t('Original default parameters. Two FIFO chips; twelve IC packages total.','Исходные параметры по умолчанию. Две микросхемы FIFO; всего двенадцать корпусов.')+'</p></div><div class="card"><h2>4 × 16</h2><p>'+t('Compact alternative. One FIFO chip; six IC packages total. Requires changing the RTL parameters.','Компактный вариант. Одна микросхема FIFO; всего шесть корпусов. Требует изменения параметров RTL.')+'</p></div></div>'
    headings=[('contract',t('1. What must match','1. Какое поведение воспроизводим')),('sequence',t('2. Automatic timing','2. Автоматический цикл')),('logic',t('3. Control equations','3. Логические уравнения')),('connections',t('4. Connections','4. Соединения')),('parts',t('5. Components','5. Компоненты')),('compact',t('6. One-chip FIFO variant','6. Вариант с одной FIFO')),('verification',t('7. Verification and sources','7. Проверка и источники'))]
    b+='<nav aria-label="'+t('On this page','На этой странице')+'">'+' · '.join(link('#'+i,label) for i,label in headings)+'</nav>'
    b+='<h2 id="contract">'+headings[0][1]+'</h2><p>'+t('Reference file:','Исходный файл:')+'</p><pre class="source-path">'+esc(provenance['original_path'])+'</pre>'
    b+='<p>'+link('research/fifo_40105_proposal/flip_flop_fifo_empty_full_optimized_and_debug_2.sv',t('Unchanged local copy','Локальная копия без изменений'))+' · '+link('research/fifo_40105_proposal/provenance.json',t('Original path and SHA-256','Исходный путь и SHA-256'))+'</p>'
    b+='<p>'+t('The RTL uses rising-edge <code>push</code>/<code>pop</code>, asynchronous active-high <code>rst</code>, and a combinational head word on <code>read_data</code>. Its default parameters are <code>width=8, depth=10</code>. The three <code>debug_*</code> ports are observations only; removing them does not change the queue.',
        'В RTL сигналы <code>push</code>/<code>pop</code> обрабатываются по положительному фронту, <code>rst</code> — асинхронный сброс активным высоким уровнем, а <code>read_data</code> комбинационно показывает головное слово. Параметры по умолчанию: <code>width=8, depth=10</code>. Три порта <code>debug_*</code> служат только для наблюдения; их удаление не меняет работу очереди.')+'</p>'
    b+='<p><strong>'+t('Valid request contract:','Условия допустимых запросов:')+'</strong></p><pre>pop  → !empty\npush → (!full || pop)\n'+t('read_data is meaningful only when !empty','read_data имеет смысл только при !empty')+'</pre>'
    # Invalid traces cannot be matched: the source advances pointers regardless of flags.
    b+='<p>'+t('The caller enforces these rules. The RTL itself does not mask requests with <code>empty</code> or <code>full</code>. Consequently, a 40105 cannot reproduce every possible raw RTL trace: an empty pop advances the RTL pointer but does not remove a word from an empty hardware FIFO. Simultaneous push/pop on an empty queue is excluded. Values of <code>read_data</code> while empty are not part of the contract.',
        'Эти правила обеспечивает вызывающая схема. Сам RTL не блокирует запросы по <code>empty</code> или <code>full</code>. Поэтому 40105 не может воспроизвести все возможные входные последовательности исходного RTL: чтение пустой очереди продвигает указатель RTL, но не удаляет слово из пустой аппаратной FIFO. Одновременные push/pop при пустой очереди исключены. Значение <code>read_data</code> при пустой очереди не входит в условия эквивалентности.')+'</p>'
    b+=table([t('State before the edge','Состояние перед фронтом'),'push','pop',t('Required result','Требуемый результат')],[
        [t('Any valid occupancy','Любое допустимое заполнение'),'0','0',t('Hold queue','Очередь не меняется')],
        [t('Space available','Есть свободное место'),'1','0',t('Append the sampled word','Добавить захваченное слово в хвост')],
        [t('At least one word','Есть хотя бы одно слово'),'0','1',t('Consume the old head','Удалить прежнее головное слово')],
        [t('At least one word, including full','Есть хотя бы одно слово, в том числе при full'),'1','1',t('Consume old head, append new word; occupancy unchanged','Удалить прежнюю голову, добавить новое слово; заполнение не меняется')],
        ['rst = 1','—','—',t('Discard all valid words and cancel a pending transaction','Аннулировать все слова и отменить незавершённую операцию')]])
    b+='<p>'+t('A single 40105 stores sixteen 4-bit words. Two devices widen the word to eight bits; they still have sixteen physical word positions. The external count declares full at ten. Under the contract, at most ten positions are occupied; six remain unused. This is a logical capacity limit, not a reconfiguration of the chip.',
        'Одна 40105 хранит шестнадцать 4-битных слов. Две микросхемы расширяют слово до восьми бит, сохраняя шестнадцать физических позиций. Внешний счётчик выдаёт full при десяти словах. При соблюдении условий заняты не более десяти позиций; шесть остаются свободными. Это логическое ограничение ёмкости, а не перенастройка самой микросхемы.')+'</p>'

    b+='<h2 id="sequence">'+headings[1][1]+'</h2><p>'+t(
        'Connect the assembled 555 clock module to the CD4017 phase counter. Use its decoded output 0, <code>PH0</code>, as the shared FIFO clock for the input registers and surrounding synchronous logic. The CD4017 runs through all ten states without a shortened reset loop. One complete turn performs one FIFO transaction.',
        'Подключите готовый тактовый модуль на 555 к счётчику фаз CD4017. Его дешифрированный выход 0, <code>PH0</code>, служит общим тактом FIFO для входных регистров и окружающей синхронной схемы. CD4017 проходит все десять состояний без укороченного цикла через сброс. Один полный оборот выполняет одну операцию FIFO.')+'</p>'
    b+='<pre>'+t('555 module, 10 Hz → CD4017 → PH0 = shared clk, 1 Hz\n                         ├→ PH2 → read pulse (SO ↓)\n                         ├→ PH5 → write pulse (SI ↑)\n                         └→ PH8 → occupancy update\n\nwrite_data → capture registers → two 40105 FIFOs → read_data\npush/pop   → capture W/R       → pulse gates + occupancy counter',
        'Модуль 555, 10 Гц → CD4017 → PH0 = общий clk, 1 Гц\n                        ├→ PH2 → импульс чтения (SO ↓)\n                        ├→ PH5 → импульс записи (SI ↑)\n                        └→ PH8 → обновление заполнения\n\nwrite_data → входные регистры → две FIFO 40105 → read_data\npush/pop   → регистры W/R     → импульсная логика + счётчик')+'</pre>'
    b+=timing(ru)
    b+=table([t('Phase / time at 10 Hz','Фаза / время при 10 Гц'),t('Action','Действие'),t('Purpose','Назначение')],[
        ['PH0 / 0 ms',t('Capture requests and write_data; consumer samples old read_data','Захватить запросы и write_data; потребитель считывает прежнее read_data'),t('Same transaction boundary as the RTL rising edge','Та же граница операции, что и положительный фронт в RTL')],
        ['PH1 / 100 ms',t('Wait','Ожидать'),t('Captured inputs settle before any FIFO strobe','Входные регистры устанавливаются до импульсов FIFO')],
        ['PH2 / 200 ms',t('SO falls if R = 1','Спад SO при R = 1'),t('Remove the old head first','Сначала удалить прежнюю голову')],
        ['PH3 / 300 ms',t('SO returns high','SO возвращается в 1'),t('Rearm the read input','Подготовить вход чтения к следующей операции')],
        ['PH4 / 400 ms',t('Wait','Ожидать'),t('Space created by a full-queue pop propagates internally','Освободившееся место после чтения полной FIFO распространяется внутри микросхемы')],
        ['PH5 / 500 ms',t('SI rises if W = 1','Фронт SI при W = 1'),t('Append the captured word','Записать захваченное слово в хвост')],
        ['PH6 / 600 ms',t('SI returns low','SI возвращается в 0'),t('Rearm the write input','Подготовить вход записи к следующей операции')],
        ['PH7 / 700 ms',t('Wait','Ожидать'),t('Allow data and ready flags to settle','Дать данным и флагам готовности установиться')],
        ['PH8 / 800 ms',t('Update N by W − R','Изменить N на W − R'),t('Publish occupancy for the next sampling edge','Подготовить заполнение к следующему фронту выборки')],
        ['PH9 / 900 ms',t('Wait; prepare the next request','Ожидать; подготовить следующий запрос'),t('Next PH0 arrives at 1000 ms','Следующий PH0 наступает в 1000 мс')]])
    b+='<p>'+t('<strong>Sampling rule:</strong> surrounding registers use only the rising edge of PH0. After PH8 and propagation settling, the resulting flags and head word also agree with the RTL result. Between PH0 and PH8, <code>read_data</code> and the count flags may describe different intermediate states. Do not clock a consumer from PH2/PH5, or treat the public outputs as coherent throughout that interval. PH0 has a 10% duty cycle.',
        '<strong>Правило выборки:</strong> окружающие регистры работают только по положительному фронту PH0. После PH8 и установления сигналов флаги и головное слово также совпадают с результатом RTL. Между PH0 и PH8 <code>read_data</code> и флаги счётчика могут относиться к разным промежуточным состояниям. Нельзя тактировать потребителя от PH2/PH5 или считать выходы согласованными на всём этом интервале. Длительность высокого уровня PH0 составляет 10% периода.')+'</p>'
    b+='<p>'+t('The 100 ms phase is a deliberately slow demonstration setting, not a maximum operating-frequency claim. For CD74HC40105 at 4.5 V, the datasheet specifies up to 750 ns for SO-to-DIR ripple and 600 ns for SI-to-DOR ripple over its full temperature range. The long phase gaps accommodate these transfers; the complete circuit still requires setup/hold, output-edge and loading checks on the actual board. Inputs must meet the CD40174 setup/hold requirements around PH0.',
        'Фаза 100 мс выбрана для медленной демонстрации; это не заявленная предельная частота. Для CD74HC40105 при 4,5 В документация задаёт до 750 нс распространения SO→DIR и до 600 нс SI→DOR во всём температурном диапазоне. Межфазные интервалы оставляют время для этих переносов; для всей схемы на реальной плате всё равно нужно проверить setup/hold, фронты выходов и нагрузку. Входы должны соблюдать требования CD40174 к setup/hold относительно PH0.')+' '+link(PDF+'cd74hc40105.pdf',t('TI timing tables','Таблицы временных параметров TI'))+'.</p>'

    b+='<h2 id="logic">'+headings[2][1]+'</h2><p>'+t('All signals below are active high except the read strobe <code>SO</code> and register clear <code>CLR_n</code>. <code>W</code>, <code>R</code> and <code>D_hold</code> are registers, not live button signals. Subscripts L/H identify the low/high nibble FIFO.',
        'Все сигналы ниже активны высоким уровнем, кроме импульса чтения <code>SO</code> и сброса регистров <code>CLR_n</code>. <code>W</code>, <code>R</code> и <code>D_hold</code> — выходы регистров, а не текущие уровни кнопок. Индексы L/H обозначают FIFO младшей/старшей тетрады.')+'</p>'
    b+='<pre>'+esc('DIR_ALL = DIR_L & DIR_H\nDOR_ALL = DOR_L & DOR_H\nR_pre   = pop & DOR_ALL\nW_pre   = push & (DIR_ALL | R_pre)\n\nPH0 rising: {D_hold, W, R} ← {write_data, W_pre, R_pre}\nrst = 1:    {D_hold, W, R} ← 0\n\nSI       = PH5 & W\nPOP_PULSE= PH2 & R\nSO       = !POP_PULSE\nCLR_n    = !rst\n\nCOUNT_EN = W ^ R\nCARRY_IN = !COUNT_EN\nUP_DOWN  = W\nPH8 rising: if COUNT_EN, N ← (W ? N+1 : N-1)\nrst = 1: N ← 0\n\nempty = !(N3 | N2 | N1 | N0)\nfull  = N3 & N1    // N is restricted to 0..10')+'</pre>'
    b+='<p>'+t('At physical full (sixteen words in the compact variant), <code>DIR_ALL=0</code>. A valid simultaneous pop makes <code>R_pre=1</code>, so the OR term still permits a write. The read at PH2 creates space before SI rises at PH5. At logical full (ten words in the main design), the physical FIFO has spare space; the caller uses the separate <code>full</code> output to enforce the ten-word limit.',
        'При физическом заполнении (шестнадцать слов в компактном варианте) <code>DIR_ALL=0</code>. Допустимое одновременное чтение даёт <code>R_pre=1</code>, поэтому ИЛИ в уравнении разрешает запись. Чтение в PH2 освобождает место до фронта SI в PH5. При логическом заполнении (десять слов в основном варианте) физическая FIFO ещё имеет свободное место; вызывающая схема использует отдельный выход <code>full</code>, чтобы соблюдать предел десять слов.')+'</p>'
    b+='<p>'+t('The abbreviated full decoder <code>N3 &amp; N1</code> equals <code>N==10</code> for reachable states 0…10. It would also assert for some forbidden counts above ten. This design assumes the valid request contract; it does not add overflow protection to the source RTL. The counter uses binary mode, so it can represent ten; a decade counter would wrap from nine to zero.',
        'Сокращённый дешифратор <code>N3 &amp; N1</code> эквивалентен <code>N==10</code> для достижимых состояний 0…10. Он также сработал бы для некоторых запрещённых значений выше десяти. Схема предполагает соблюдение допустимых запросов и не добавляет защиты от переполнения к исходному RTL. Счётчик работает в двоичном режиме и способен представить десять; десятичный режим перевёл бы девять в ноль.')+'</p>'
    b+='<p>'+t('Do not replace this with <code>SI = clk &amp; push</code> and <code>SO = !(clk &amp; pop)</code>. A request changing during a high clock level can create another strobe. Data from a producer clocked at the same edge can also change before the gated write edge arrives. Capturing inputs and using later, separate phases removes those dependencies. Live DIR/DOR signals qualify captured requests, not the pulse duration.',
        'Нельзя заменить это на <code>SI = clk &amp; push</code> и <code>SO = !(clk &amp; pop)</code>. Изменение запроса при высоком уровне такта может создать дополнительный импульс. Данные источника, тактируемого тем же фронтом, также могут измениться раньше, чем дойдёт задержанный вентилем фронт записи. Захват входов и отдельные последующие фазы устраняют эти зависимости. Текущие DIR/DOR участвуют в захвате запросов, но не определяют длительность импульса.')+'</p>'

    b+='<h2 id="connections">'+headings[3][1]+'</h2><p>'+t('The following allocation is for the 8 × 10 circuit. Use a common 5 V supply and ground, with valid 0/5 V logic levels. All pin numbers are DIP top views. U1/U2 are the exact <strong>CD74HC40105E</strong> part linked by LSSK row 36.',
        'Следующее распределение относится к схеме 8 × 10. Используйте общие питание 5 В и землю, а также корректные логические уровни 0/5 В. Номера выводов указаны для DIP, вид сверху. U1/U2 — именно <strong>CD74HC40105E</strong>, на которую ссылается строка 36 таблицы LSSK.')+'</p>'
    b+='<h3>U1, U2 — CD74HC40105E</h3>'
    b+=table([t('Pin(s)','Выводы'),t('Signal','Сигнал'),t('Connection','Подключение')],[
        ['16 / 8','VCC / GND','+5 V / GND'],['1',t('Three-state control','Управление третьим состоянием'),'GND'],['9','MR','rst'],['3','SI',t('Common SI to both chips','Общий SI на обе микросхемы')],['15','SO',t('Common SO to both chips','Общий SO на обе микросхемы')],
        ['4, 5, 6, 7','D0, D1, D2, D3','U1: D_hold[0…3]; U2: D_hold[4…7]'],['13, 12, 11, 10','Q0, Q1, Q2, Q3','U1: read_data[0…3]; U2: read_data[4…7]'],['2','DIR','U1 → DIR_L; U2 → DIR_H'],['14','DOR','U1 → DOR_L; U2 → DOR_H']])
    b+='<p>'+t('Both nibbles always share strobes and reset; their readiness signals are ANDed. Keep pin 1 low throughout operation. The older CD40105B family has an additional interaction between output enable and SO; it is not interchangeable with HC for timing figures. Fixed-low pin 1 also avoids that output-enable transition.',
        'Обе тетрады всегда получают общие импульсы и сброс; сигналы готовности объединяются через И. Держите вывод 1 в нуле всё время работы. В старом семействе CD40105B есть дополнительная зависимость между разрешением выхода и SO; его временные параметры нельзя подменять параметрами HC. Постоянный ноль на выводе 1 также исключает это переключение разрешения выхода.')+' '+link(PDF+'cd74hc40105.pdf',t('Pinout and functional description','Назначение выводов и описание работы'))+'.</p>'
    b+='<h3>U3, U4 — CD40174</h3><p>'+t('Both: clock pin 9 = PH0, active-low clear pin 1 = CLR_n, supply pins 16/8 = +5 V/GND. Each row below is one D flip-flop.','Обе микросхемы: такт на выводе 9 = PH0, активный низкий сброс на выводе 1 = CLR_n, питание на выводах 16/8 = +5 В/GND. Каждая строка ниже — один D-триггер.')+'</p>'
    b+=table([t('D pin → Q pin','Вывод D → вывод Q'),'U3','U4'],[
        ['3 → 2','write_data[0] → D_hold[0]','write_data[6] → D_hold[6]'],['4 → 5','write_data[1] → D_hold[1]','write_data[7] → D_hold[7]'],['6 → 7','write_data[2] → D_hold[2]','W_pre → W'],['11 → 10','write_data[3] → D_hold[3]','R_pre → R'],['13 → 12','write_data[4] → D_hold[4]',t('D = GND; Q unused','D = GND; Q свободен')],['14 → 15','write_data[5] → D_hold[5]',t('D = GND; Q unused','D = GND; Q свободен')]])
    b+='<p>'+link(PDF+'cd40174b.pdf','TI CD40174B')+' · '+link('https://www.renesas.com/en/document/dst/cd40174bms-datasheet?r=521281',t('Renesas 40174 functional pin diagram','Функциональная схема выводов 40174 Renesas'))+'.</p>'
    b+='<h3>U5 — CD4017</h3>'
    b+=table([t('Pin(s)','Выводы'),t('Connection','Подключение')],[['16 / 8','+5 V / GND'],['14',t('Output of the assembled clock module','Выход готового тактового модуля')],['13','GND'],['15','rst'],['3','PH0 → clk'],['4','PH2'],['1','PH5'],['9','PH8'],['2, 7, 10, 5, 6, 11, 12',t('Unused outputs, leave open','Неиспользуемые выходы, оставить свободными')]])
    b+='<p>'+t('Use the decoded outputs directly. Their specified spike-free decoding is useful here because PH0 and PH8 clock registers. Do not feed PH8 back to reset: all ten states are part of the timing schedule.','Используйте дешифрированные выходы напрямую. Заявленное отсутствие ложных импульсов на этих выходах существенно: PH0 и PH8 тактируют регистры. Не соединяйте PH8 со сбросом: в расписании нужны все десять состояний.')+' '+link('https://www.ti.com/product/CD4017B','TI CD4017B')+'.</p>'
    b+='<h3>U6 — CD4029</h3>'
    b+=table([t('Pin(s)','Выводы'),t('Signal','Сигнал'),t('Connection','Подключение')],[['16 / 8','VDD / VSS','+5 V / GND'],['15','CLOCK','PH8'],['9','BINARY/DECADE','+5 V'],['10','UP/DOWN','W'],['5','CARRY IN','!(W ^ R)'],['1','PRESET ENABLE','rst'],['4, 12, 13, 3','JAM1…JAM4','GND'],['6, 11, 14, 2','Q1…Q4','N0, N1, N2, N3'],['7','CARRY OUT',t('Unused output','Неиспользуемый выход')]])
    b+='<p>'+t('A high preset-enable loads the four zero JAM inputs asynchronously. A low carry-in enables counting; W selects up or down. For W=R, carry-in is high and the count holds.','Высокий preset-enable асинхронно загружает четыре нулевых JAM-входа. Низкий carry-in разрешает счёт; W задаёт направление. При W=R carry-in высок, и значение сохраняется.')+' '+link(PDF+'cd4029b.pdf','TI CD4029B')+' · '+link('https://www.renesas.com/en/document/dst/cd4029bms-datasheet?r=521151',t('Renesas pin diagram and truth table','Схема выводов и таблица работы Renesas'))+'.</p>'
    b+='<h3>'+t('U7–U12 — gate allocation','U7–U12 — распределение вентилей')+'</h3>'
    gates=[['U7.A','CD4081','DIR_L & DIR_H → DIR_ALL'],['U7.B','CD4081','DOR_L & DOR_H → DOR_ALL'],['U7.C','CD4081','pop & DOR_ALL → R_pre'],['U7.D','CD4081','push & WRITE_OK → W_pre'],['U8.A','CD4081','PH5 & W → SI'],['U8.B','CD4081','PH2 & R → POP_PULSE'],['U8.C','CD4081','N3 & N1 → full'],['U9.A','CD4071','DIR_ALL | R_pre → WRITE_OK'],['U10.A','CD4069','!rst → CLR_n'],['U10.B','CD4069','!POP_PULSE → SO'],['U10.C','CD4069','!COUNT_EN → CARRY_IN'],['U11.A','CD4070','W ^ R → COUNT_EN'],['U12.A','CD4002','!(N0 | N1 | N2 | N3) → empty']]
    b+=table([t('Gate','Вентиль'),t('Device','Микросхема'),t('Inputs → output','Входы → выход')],[[a,c,'<code>'+esc(e)+'</code>'] for a,c,e in gates])
    b+='<p>'+t('For CD4081/CD4071/CD4070, gate A uses inputs 1,2 → output 3; B: 5,6 → 4; C: 8,9 → 10; D: 12,13 → 11. For CD4069, A: 1 → 2; B: 3 → 4; C: 5 → 6. CD4002 gate A: inputs 2,3,4,5 → output 1. All six gate packages use pin 14 = +5 V, pin 7 = GND. Tie unused gate inputs to GND and leave unused outputs open; leave CD4002 NC pins 6 and 8 unconnected.',
        'Для CD4081/CD4071/CD4070 вентиль A: входы 1,2 → выход 3; B: 5,6 → 4; C: 8,9 → 10; D: 12,13 → 11. Для CD4069: A: 1 → 2; B: 3 → 4; C: 5 → 6. Вентиль A CD4002: входы 2,3,4,5 → выход 1. У всех шести корпусов вентилей вывод 14 = +5 В, вывод 7 = GND. Неиспользуемые входы подключите к GND, выходы оставьте свободными; NC-выводы 6 и 8 CD4002 не подключайте.')+'</p>'
    b+='<p class="small">'+t('Gate datasheets: ','Документация на вентили: ')+', '.join(link(PDF+name+'.pdf',name.upper()) for name in ['cd4081b','cd4071b','cd4069ub','cd4070b','cd4002b'])+'.</p>'
    b+='<h3>'+t('Reset and starting a run','Сброс и начало работы')+'</h3><p>'+t('Connect rst to both FIFO MR inputs, CD4017 RESET, CD4029 PRESET ENABLE and the inverter producing CLR_n. Reset must remain asserted long enough for all devices to clear. It forces SI low and SO high, cancels captured commands and forces the phase counter to PH0. With no reset gating on SI, the cleared W register is what guarantees SI stays low during reset release. After reset release, the first useful capture occurs when the counter wraps back to PH0. Release reset away from a master-clock edge and allow its specified recovery time; do not interpret the reset-induced PH0 edge as a transaction.',
        'Подключите rst к MR обеих FIFO, RESET CD4017, PRESET ENABLE CD4029 и инвертору, формирующему CLR_n. Удерживайте сброс достаточно долго, чтобы очистились все устройства. Он устанавливает SI=0 и SO=1, отменяет захваченные команды и переводит счётчик фаз в PH0. Отдельного блокирования SI сбросом нет: нулевой регистр W гарантирует низкий SI при снятии сброса. После снятия сброса первый полезный захват происходит при возврате счётчика в PH0. Снимайте сброс вдали от фронта основного такта, соблюдая время восстановления; фронт PH0, вызванный самим сбросом, не является операцией.')+'</p>'

    b+='<h2 id="parts">'+headings[4][1]+'</h2><p>'+t('Every added IC below implements a named part of the circuit. Quantities include the FIFO chips and phase generator, but exclude the assembled 555 module, breadboards, power, input modules, indicators and wiring. The prices are the existing LSSK snapshot of 14 October 2026, not current supplier quotations.',
        'Каждая добавленная микросхема ниже выполняет определённую функцию схемы. Количества включают FIFO и генератор фаз, но не включают готовый модуль 555, макетные платы, питание, входные модули, индикаторы и провода. Цены взяты из сохранённой таблицы LSSK от 14 октября 2026 года; это не текущие предложения поставщиков.')+'</p>'
    raw=json.loads((ROOT/'research/lssk_rows.json').read_text())
    rows={int(next(iter(row)).lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ')):row for row in raw if row}
    parts=[('CD74HC40105E',36,2,1,t('Queue storage','Память очереди')),('CD40174',26,2,1,t('Capture data and W/R','Захват данных и W/R')),('CD4017',37,1,1,t('Ten automatic phases','Десять автоматических фаз')),('CD4029',4,1,0,t('Occupancy 0…10','Заполнение 0…10')),('CD4081',10,2,1,t('Ready barriers, request and pulse gates, full decode','Объединение готовности, запросы, импульсы и full')),('CD4071',20,1,1,t('Permit write after a simultaneous full-queue read','Разрешить запись после одновременного чтения полной очереди')),('CD4069',24,1,1,t('Signal polarities','Полярности сигналов')),('CD4070',2,1,0,t('Count only when W differs from R','Изменять счётчик только при W ≠ R')),('CD4002',17,1,0,t('Decode empty from the count','Дешифрация empty из счётчика'))]
    total_a=Decimal(0);total_b=Decimal(0);bom=[]
    for chip,row,qa,qb,reason in parts:
        price=Decimal(rows[row][f'J{row}']);total_a+=price*qa;total_b+=price*qb
        bom.append([chip,str(qa),str(qb),reason,link(SHEET+f'?range=LSSK!A{row}:Q{row}',str(row)),f'${price:.2f}'])
    b+=table([t('IC','Микросхема'),'8 × 10','4 × 16',t('Function','Функция'),t('LSSK row','Строка LSSK'),t('USD / IC','USD / шт.')],bom)
    b+='<p><strong>'+t(f'IC totals: 12 packages / ${total_a:.2f} for 8 × 10; 6 packages / ${total_b:.2f} for 4 × 16.',f'Итого микросхемы: 12 корпусов / ${total_a:.2f} для 8 × 10; 6 корпусов / ${total_b:.2f} для 4 × 16.')+'</strong> '+t('These are IC subtotals, not finished-kit costs or selling prices.','Это стоимость только микросхем, а не готового набора и не розничная цена.')+'</p>'

    b+='<h2 id="compact">'+headings[5][1]+'</h2><p>'+t('For the smaller teaching circuit, instantiate the reference RTL with <code>width=4, depth=16</code>. Keep one 40105, one 40174, the same 4017 phase generator, one 4081, one 4071 and one 4069. This alternative preserves word ordering and simultaneous read/write behavior, but has a different width and capacity from the original defaults.',
        'Для более компактной учебной схемы задайте в исходном RTL <code>width=4, depth=16</code>. Оставьте одну 40105, одну 40174, тот же генератор фаз 4017, одну 4081, одну 4071 и одну 4069. Этот вариант сохраняет порядок слов и одновременное чтение/запись, но отличается от исходных параметров шириной и ёмкостью.')+'</p>'
    b+='<pre>'+esc('DIR_ALL = DIR; DOR_ALL = DOR\nR_pre = pop & DOR\nW_pre = push & (DIR | R_pre)\nSI = PH5 & W\nSO = !(PH2 & R)\nempty = !DOR\nfull = !DIR')+'</pre>'
    b+='<p>'+t('Allocate the 40174 first four D/Q pairs to data[0…3], its fifth pair (13 → 12) to W, and sixth (14 → 15) to R. The four 4081 gates implement R_pre, W_pre, SI and POP_PULSE. One 4071 gate produces DIR | R_pre. Four 4069 inverters produce CLR_n, SO, empty and full. The 4029, 4070, 4002, second FIFO, second register package and second AND package are removed. PH8 is a settling milestone only; its 4017 output can be left open.',
        'Первые четыре пары D/Q микросхемы 40174 отведите данным data[0…3], пятую пару (13 → 12) — W, шестую (14 → 15) — R. Четыре вентиля 4081 формируют R_pre, W_pre, SI и POP_PULSE. Один вентиль 4071 формирует DIR | R_pre. Четыре инвертора 4069 формируют CLR_n, SO, empty и full. Микросхемы 4029, 4070, 4002, вторая FIFO, второй корпус регистров и второй корпус И удаляются. PH8 здесь служит только моментом, к которому сигналы установились; этот выход 4017 можно оставить свободным.')+'</p>'
    b+='<p class="callout">'+t('In this variant, <code>!DIR</code> and <code>!DOR</code> also reflect temporary internal activity. They are valid occupancy flags at the PH0 sampling edge after settling, not guaranteed continuous full/empty indications during a strobe. In particular, a transient !DIR does not prove sixteen stored words. The main 8 × 10 circuit avoids using those raw signals as its public count flags.',
        'В этом варианте <code>!DIR</code> и <code>!DOR</code> также отражают временные внутренние процессы. Они являются корректными флагами заполнения на фронте выборки PH0 после установления, но не гарантируют непрерывно достоверное full/empty во время импульса. В частности, кратковременная !DIR не доказывает наличие шестнадцати слов. В основной схеме 8 × 10 эти сигналы не используются напрямую как внешние флаги заполнения.')+'</p>'

    b+='<h2 id="verification">'+headings[6][1]+'</h2><p>'+t('The included regression compiles the actual reference file with its debug outputs unconnected. It compares both the proposal model and the original RTL with an independent queue, before the PH0 sampling update and after PH8 settling. The queue model for each 40105 uses its logical SI/SO behavior and deliberately different artificial settling delays for the two nibbles. It is not a manufacturer timing model.',
        'Включённая регрессия компилирует сам исходный файл с неподключёнными отладочными выходами. Модель предложения и исходный RTL сравниваются с независимой очередью перед обновлением по PH0 и после установления сигналов за PH8. Модель каждой 40105 воспроизводит логическую работу SI/SO и использует намеренно разные условные задержки установления двух тетрад. Это не временная модель производителя.')+'</p>'
    b+='<pre>'+esc('\n'.join(validation['results']))+'</pre>'
    b+='<p>'+t('Tests cover fill/drain, repeated wraparound, one-word simultaneous read/write, replacement at full, random legal traffic, raw inputs changing repeatedly after capture, exactly one strobe per accepted operation, and reset in each phase 1…9. Each configuration includes 2,000 random cycles. Read-data comparison is skipped when empty, as required by the contract.',
        'Проверки охватывают заполнение/опустошение, многократный оборот указателей, одновременное чтение/запись при одном слове, замену при full, случайные допустимые запросы, многократное изменение входов после захвата, ровно один импульс на принятую операцию и сброс в каждой фазе 1…9. В каждой конфигурации выполнены 2000 случайных циклов. При empty данные не сравниваются, как и предусмотрено условиями эквивалентности.')+'</p>'
    b+='<p>'+link('scripts/check_40105_proposal.py',t('Regression runner','Запуск регрессии'))+' · '+link('research/fifo_40105_proposal/proposal_model.sv',t('Circuit model','Модель схемы'))+' · '+link('research/fifo_40105_proposal/testbench.sv',t('Testbench','Тестовое окружение'))+' · '+link('research/fifo_40105_proposal/validation.json',t('Validation record','Результаты проверки'))+'</p><pre>python3 scripts/check_40105_proposal.py</pre>'
    b+='<h3>'+t('What remains to check on a prototype','Что проверить на опытном макете')+'</h3><ol>'
    for en,russian in [
        ('At 10 Hz master clock, verify the 1 Hz PH0 output and one SO-low / SI-high phase per enabled request. Confirm both FIFO chips receive the same strobes.', 'При основном такте 10 Гц проверьте PH0 частотой 1 Гц и ровно одну фазу низкого SO / высокого SI на разрешённый запрос. Убедитесь, что обе FIFO получают одинаковые импульсы.'),
        ('Check clock levels, edge slew, fan-out and setup/hold with the actual selected parts and wiring. A logical regression does not verify these electrical details.', 'Проверьте уровни такта, длительности фронтов, нагрузочную способность и setup/hold с выбранными деталями и проводами. Логическая регрессия не проверяет эти электрические параметры.'),
        ('Write ten distinct bytes, including A5 and 3C; confirm full at ten, then pop them in order. At full, assert push and pop together and confirm that the old head is consumed and the new byte joins the tail.', 'Запишите десять разных байтов, включая A5 и 3C; проверьте full при десяти, затем считайте слова по порядку. При full подайте push и pop одновременно: прежняя голова должна быть прочитана, а новый байт добавлен в хвост.'),
        ('Assert reset during PH2 and PH5; verify empty after reset and no unintended write on release. Compare data and count flags only at the documented observation times.', 'Подайте сброс во время PH2 и PH5; проверьте empty после сброса и отсутствие непреднамеренной записи при его снятии. Сравнивайте данные и флаги только в указанные моменты наблюдения.')]:
        b+='<li>'+t(en,russian)+'</li>'
    b+='</ol><p>'+t('This is a circuit proposal with reproducible logical validation. It does not claim transistor-level timing equivalence, continuous-waveform equivalence, or completed hardware qualification. Using an unrelated incoming clk while preserving the original port timing would require a different internally sequenced controller and a new timing analysis.',
        'Это предложение схемы с воспроизводимой логической проверкой. Оно не заявляет эквивалентность времён на транзисторном уровне, совпадение непрерывных временных диаграмм или завершённую аппаратную квалификацию. Использование постороннего входного clk с сохранением исходных временных отношений портов потребовало бы другого контроллера внутренних фаз и нового временного анализа.')+'</p>'
    b+='<p class="source">'+t('Basis: the local RTL linked above; ','Основа: исходный RTL по ссылке выше; ')+link(PDF+'cd74hc40105.pdf','TI CD74HC40105')+'; '+link(PDF+'cd4017b.pdf','TI CD4017B')+'; '+link(PDF+'cd40174b.pdf','TI CD40174B')+'; '+link(PDF+'cd4029b.pdf','TI CD4029B')+'; '+link(SHEET+'?range=LSSK!A1:Q76',t('LSSK component sheet','Таблица компонентов LSSK'))+'.</p>'
    language='ru' if ru else 'en'
    return f'''<!doctype html>
<html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · LSSK</title><link rel="stylesheet" href="assets/style.css"><style>.timing svg{{display:block;width:100%;height:auto;min-width:640px}}.timing{{overflow-x:auto}}.source-path{{white-space:pre-wrap;overflow-wrap:anywhere}}@media print{{.timing svg{{min-width:0}}}}</style></head><body>
<a class="skip" href="#main">{t('Skip to content','К содержанию')}</a><header><a class="brand" href="{index}">LSSK / 40105 FIFO</a><nav aria-label="{t('Navigation','Навигация')}"><a href="{index}">{t('Learning pack','Учебные материалы')}</a><a data-language-switch href="{partner}" lang="{'en' if ru else 'ru'}">{t('Русская версия','English version')}</a></nav></header><main id="main">{b}</main><footer>{t('Circuit proposal · 17 October 2026 · Logical simulation completed; hardware not assembled.','Предложение схемы · 17 октября 2026 · Логическое моделирование выполнено; аппаратный макет не собран.')}</footer></body></html>'''


def generate():
    for ru in [False,True]:
        name='fifo_40105_proposal'+('_ru' if ru else '')+'.html'
        (ROOT/name).write_text(document(ru),encoding='utf-8')
    print('Generated separate English/Russian 40105 FIFO proposals.')


if __name__=='__main__':
    generate()
