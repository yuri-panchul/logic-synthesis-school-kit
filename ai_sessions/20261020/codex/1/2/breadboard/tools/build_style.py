#!/usr/bin/env python3
"""Publish the observed repository conventions and the chosen breadboard style."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
BGM = 'https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/'
HW = 'https://github.com/yuri-panchul/systemverilog-homework/blob/10258b2f0127495db989296dfd3f7cd0bbc77496/'
SOURCES = [
    ('BGM · Moore FSM', BGM + 'labs/1_basics/1_10_snail_fsm/snail_moore_fsm.sv'),
    ('BGM · Mealy FSM', BGM + 'labs/1_basics/1_10_snail_fsm/snail_mealy_fsm.sv'),
    ('BGM · Counter', BGM + 'labs/1_basics/1_06_binary_counter/lab_top.sv'),
    ('BGM · One-hot FSM', BGM + 'labs/2_graphics/2_6_game_2x_variant_2/game_master_fsm_2_special_style_one_hot.sv'),
    ('BGM · FIFO', BGM + 'labs/4_microarchitecture/4_2_fifo/4_2_5_optimized_ff_fifo_view_2_data_layout/flip_flop_fifo_empty_full_optimized_and_debug_2.sv'),
    ('Homework · Sequence FSM', HW + '05_finite_state_machines/05_01_detect_sequence_using_fsm/05_01_detect_sequence_using_fsm.sv'),
    ('Homework · Formula FSM', HW + '05_finite_state_machines/05_04_05_sqrt_formula_fsms/formula_1_impl_1_fsm.sv'),
    ('Homework · Alternative FSM style', HW + '05_finite_state_machines/05_04_05_sqrt_formula_fsms/formula_1_impl_1_fsm_style_2.sv'),
    ('Homework · Fibonacci', HW + '02_sequential_basics/02_02_single_and_double_rate_fibonacci/02_02_single_and_double_rate_fibonacci.sv'),
    ('Homework · Self-checking testbench', HW + '05_finite_state_machines/05_01_detect_sequence_using_fsm/testbench.sv'),
]

# Each entry states a practical rule, its observed basis and any local choice.
RULES = [
    ('Four spaces; no tabs', 'Четыре пробела; без табуляции',
     'Indent each nested block by four spaces. Use spaces for alignment and remove trailing whitespace. Four spaces are an explicit user requirement for breadboard/. The repositories contain both two- and four-space examples; this is not a claim that every upstream file uses four.',
     'Каждый вложенный блок сдвигайте на четыре пробела. Для выравнивания используйте пробелы; удаляйте пробелы в конце строки. Четыре пробела — явное требование пользователя для breadboard/. В исходных репозиториях встречаются отступы и в два, и в четыре пробела.'),
    ('Module and block layout', 'Оформление модулей и блоков',
     'Put the module name, parameter list introduced by # (, and port list on separate lines. Put begin and end on their own lines; write else on a separate line after end. A single conditional assignment may omit begin/end. Keep short case arms readable and align case labels with case, following the BGM FSM and homework formula examples.',
     'Имя модуля, список параметров с # ( и список портов начинайте с отдельных строк. begin и end пишите на отдельных строках; else — с новой строки после end. Для одного присваивания begin/end можно опустить. Короткие ветви case оставляйте компактными; метки выравнивайте с case, как в примерах автоматов BGM и формул Homework.'),
    ('Whitespace around syntax', 'Пробелы в выражениях',
     'Write if (condition), case (state), always_ff @ (posedge clk), function_name (arg), state [i], width\' (value), and for (int i = 0; i < n; i ++). Put spaces around binary operators and after unary operators: a | b, ~ a, | state. Use spaced concatenations such as { state [8:0], state [9] }. Do not split multi-character operators such as <= or !==.',
     'Пишите if (condition), case (state), always_ff @ (posedge clk), function_name (arg), state [i], width\' (value) и for (int i = 0; i < n; i ++). Отделяйте пробелами двоичные операции и операнд унарной операции: a | b, ~ a, | state. Конкатенации: { state [8:0], state [9] }. Не разделяйте символы операций <= и !==.'),
    ('Descriptive names', 'Содержательные имена',
     'Use lower_snake_case for modules and signals. Retain established interface names such as clk, rst, w_led and arg_vld. Named FSM states may be S0/S1, STATE_START, or st_idle; all occur in the inspected examples. Choose one scheme per module. Likewise use one next-state convention, next_state, new_state or d_state. This lesson uses next_state; existing wrapper parameters keep their public names.',
     'Для модулей и сигналов используйте lower_snake_case. Сохраняйте принятые имена интерфейсов: clk, rst, w_led, arg_vld. В изученных примерах состояния называются S0/S1, STATE_START и st_idle; выбирайте одну систему внутри модуля. Аналогично выбирайте next_state, new_state или d_state. В этом уроке используется next_state; публичные параметры оболочек сохраняют свои имена.'),
    ('Readable declarations and ports', 'Читаемые объявления и порты',
     'Use ANSI port declarations. Group clock/reset, data, controls and outputs with blank lines or short comments. Align related directions, types, ranges and names. Use one port connection per line in this lesson. Nearby simple declarations may share a line, but avoid compressed declarations and statements that obscure the hardware.',
     'Используйте объявления портов ANSI. Разделяйте такт/сброс, данные, управление и выходы пустыми строками или короткими комментариями. Выравнивайте направления, типы, диапазоны и имена. В этом уроке каждое подключение порта занимает отдельную строку. Простые связанные объявления можно объединять; не уплотняйте код в ущерб пониманию схемы.'),
    ('logic for variables; wire for nets', 'logic для переменных; wire для цепей',
     'Use logic for values assigned in procedural blocks, including registered outputs and testbench stimulus. Use wire for explicit connections and continuously driven expressions. The repositories also omit wire on net ports; breadboard/ spells it out to work consistently with default_nettype none. A wire declaration with = is a continuous assignment; logic x = expression is variable initialization and must not replace combinational logic.',
     'Используйте logic для значений, присваиваемых процедурно, включая регистровые выходы и стимулы тестбенча. wire обозначает соединения и непрерывно вычисляемые выражения. В репозиториях wire у портов часто опущен; в breadboard/ он указан явно для согласованной работы с default_nettype none. Объявление wire с = означает непрерывное присваивание; logic x = expression — инициализацию переменной, а не комбинационную схему.'),
    ('State updates use always_ff and <=', 'Обновление состояния: always_ff и <=',
     'Use always_ff for synthesizable edge-triggered state and nonblocking assignments (<=) inside it. Each state variable has one writer. An ordinary always remains appropriate for a testbench clock generator. Use logic rather than legacy reg in new SystemVerilog.',
     'Для синтезируемого состояния, меняющегося по фронту, используйте always_ff и неблокирующие присваивания (<=). У каждой переменной состояния должен быть один источник записи. Обычный always допустим для генератора такта в тестбенче. В новом SystemVerilog используйте logic вместо устаревшего reg.'),
    ('Combinational logic uses assign or always_comb', 'Комбинационная логика: assign или always_comb',
     'Use assign or a wire initializer for a simple equation. Use always_comb with blocking assignments (=) for a decision tree or decoder. Supply defaults or cover every branch for every assigned output. For an FSM, next_state = state expresses a hold default. It prevents a latch; it does not recover an illegal state automatically.',
     'Для простого уравнения используйте assign или инициализатор wire. Для дерева решений или дешифратора — always_comb с блокирующими присваиваниями (=). Задавайте значения по умолчанию или охватывайте все ветви для каждого выхода. next_state = state задаёт удержание состояния. Это предотвращает защёлку, но не восстанавливает автоматически недопустимое состояние.'),
    ('Reset follows the hardware contract', 'Сброс соответствует контракту схемы',
     'Do not change reset semantics to satisfy formatting. The BGM snail/counter examples use asynchronous active-high reset; the inspected Homework FSM/Fibonacci examples use synchronous active-high reset. This exercise keeps asynchronous active-high rst because it models CD4017 RESET. Tiny Tapeout rst_n is inverted at the wrapper boundary. No reset style is universal across the two repositories.',
     'Не меняйте семантику сброса ради оформления. В примерах улитки и счётчика BGM сброс асинхронный, активный единицей; в изученных FSM/Fibonacci Homework — синхронный, тоже активный единицей. Здесь rst остаётся асинхронным и активным единицей, как RESET CD4017. rst_n Tiny Tapeout инвертируется на границе оболочки. Единого вида сброса для двух репозиториев нет.'),
    ('Make the FSM structure explicit', 'Явно показывайте структуру автомата',
     'Distinguish the state register, next-state logic and output logic with short comments and spacing. Both enum-based and localparam/one-hot examples are present upstream. For a simple cyclic one-hot machine, a rotation equation is clearer than ten identical case arms. Keep the state diagram, reset, transition conditions and output decode consistent. In this Moore machine, output values belong inside state nodes.',
     'Разделяйте регистр состояния, логику следующего состояния и выходную логику комментариями и пустыми строками. В исходниках есть enum и варианты с localparam/one-hot. Для простого циклического унитарного автомата уравнение вращения яснее десяти однотипных ветвей case. Согласуйте граф, сброс, условия переходов и дешифрацию. У этого автомата Мура значения выходов указываются внутри вершин.'),
    ('Preserve encoding and observable behavior', 'Сохраняйте кодирование и поведение',
     'Named states, physical chip pins and encoded bit vectors are different concepts. Do not replace the public ten-bit one-hot state output with a binary enum while calling it a style-only change. Some upstream enums use bit and others logic; use four-state logic for this lesson so unknown state is visible in simulation. No illegal-state recovery is added by this style update.',
     'Имена состояний, физические выводы и кодовые векторы — разные понятия. Не заменяйте внешний десятибитный one-hot выход двоичным enum под видом изменения стиля. В исходниках встречаются enum с bit и с logic; здесь используется четырёхзначный logic, чтобы неопределённое состояние было видно в симуляции. Изменение стиля не добавляет восстановление из недопустимых состояний.'),
    ('Make widths intentional', 'Осознанно задавайте разрядности',
     'Use explicit ranges and sized literals when width matters; use \u00270 and \u00271 to fill a destination. Use parameters, $clog2 and explicit casts where appropriate. Follow the visible width-cast style, for example 8\u0027 (i). Keep signedness intentional. Upstream teaching examples sometimes use unsized constants; do not turn that into a requirement to rely on implicit extension.',
     'Когда важна разрядность, задавайте диапазоны и размерные литералы; для заполнения приёмника используйте \u00270 и \u00271. По необходимости применяйте параметры, $clog2 и явные приведения, например 8\u0027 (i). Учитывайте знаковость. В учебных исходниках встречаются безразмерные константы; это не требование полагаться на неявное расширение.'),
    ('Connect modules by name', 'Подключайте модули по именам портов',
     'Use explicit .port (signal) connections and align them. Both repositories also use shorthand and .* where names match. For this lesson, explicit connections make physical pin models and board wrappers easier to audit; replace the previous positional DUT calls. Give generate blocks descriptive names.',
     'Используйте явные выровненные подключения .port (signal). В обоих репозиториях встречаются сокращённые подключения и .* при совпадении имён. В этом уроке явные подключения помогают проверять модели выводов и оболочки плат; прежние позиционные вызовы заменены. Блокам generate давайте содержательные имена.'),
    ('Separate statements and explain intent', 'Разделяйте действия и поясняйте замысел',
     'Keep one procedural action per line, except a short case arm or loop header. Use blank lines between declarations, instances, combinational logic, registers and checks. Comments explain hardware intent or a non-obvious choice; long modules may use the repositories\u0027 dashed separators. Keep shared HDL comments in English and translate the surrounding lesson into Russian.',
     'Пишите по одному процедурному действию на строке, кроме короткой ветви case или заголовка цикла. Разделяйте объявления, экземпляры, комбинационную логику, регистры и проверки пустыми строками. Комментарии поясняют аппаратный смысл или неочевидное решение; в длинных модулях допустимы разделители из дефисов. Общие комментарии HDL — на английском; текст урока переведён на русский.'),
    ('Testbenches remain readable and self-checking', 'Тестбенчи читаемы и проверяют результат',
     'Use logic, int, named DUT connections, procedural stimulus and an independent expected result. Keep delays and system tasks in simulation code. Compare four-state results with !== when unknowns must fail. Print PASS only after every check. Homework demonstrates this self-checking approach; breadboard/ additionally uses $fatal (1, ...) for failures so shell runners return an error.',
     'Используйте logic, int, именованные подключения DUT, процедурные стимулы и независимо рассчитанный ожидаемый результат. Задержки и системные задачи оставляйте в симуляционном коде. Когда неопределённость должна означать ошибку, сравнивайте через !==. Печатайте PASS после всех проверок. Homework показывает такой подход; в breadboard/ ошибки дополнительно завершаются через $fatal (1, ...), чтобы скрипт получил ненулевой код.'),
    ('Keep tool conventions local and justified', 'Обосновывайте особенности инструментов',
     'Do not copy configuration includes, lint suppressions or synthesis hints without their purpose. Explain any suppression and keep its scope narrow. BGM uses config.svh for its infrastructure; these standalone cores do not require that include. breadboard/ keeps default_nettype none and an explicit timescale, restoring the net default after each module. These are local portability choices, not universal upstream rules.',
     'Не копируйте include конфигурации, подавление предупреждений или подсказки синтезатору без понимания цели. Объясняйте подавления и ограничивайте область действия. BGM использует config.svh для своей инфраструктуры; автономным модулям урока он не нужен. В breadboard/ сохранены default_nettype none и явный timescale; после модуля тип цепей по умолчанию восстанавливается. Это локальные решения совместимости, а не общие правила исходных репозиториев.'),
]


def build():
    for lang in ['en', 'ru']:
        ru = lang == 'ru'
        name = 'systemverilog_style_ru' if ru else 'systemverilog_style'
        other = 'systemverilog_style.html' if ru else 'systemverilog_style_ru.html'
        index = 'index_ru.html' if ru else 'index.html'
        title = 'Правила стиля SystemVerilog' if ru else 'SystemVerilog style rules'
        intro = (
            'Практические правила по изученным учебным исходникам Basics-Graphics-Music и systemverilog-homework. '
            'Это анализ примеров, а не официальный единый стандарт их авторов. Для breadboard/ выбран согласованный '
            'вариант с отступом в четыре пробела по требованию пользователя. Обновлено 21 октября 2026 года.' if ru else
            'Practical rules inferred from the inspected teaching sources in Basics-Graphics-Music and '
            'systemverilog-homework. This is an analysis of examples, not an official common standard from their authors. '
            'breadboard/ uses a consistent four-space variant as requested by the user. Updated 21 October 2026.'
        )
        body = [f'<header><div class="topbar"><a href="{index}">LSSK · Breadboard</a>'
                f'<a href="{other}">{"English" if ru else "Русский"}</a></div><h1>{title}</h1>'
                f'<p class="intro">{intro}</p></header><main class="index-main">'
                f'<p><a href="{name}.md" download>Markdown</a></p>']
        md = [f'# {title}', '', intro, '']
        for n, rule in enumerate(RULES, 1):
            heading, paragraph = rule[1 if ru else 0], rule[3 if ru else 2]
            body.append(f'<section id="rule{n:02d}"><h2>{n}. {heading}</h2><p>{escape(paragraph)}</p></section>')
            md += [f'## {n}. {heading}', '', paragraph, '']
        heading = 'Пример из этого урока' if ru else 'Applied example from this lesson'
        source = (ROOT / 'traffic_light/rtl/traffic_light.sv').read_text()
        body.append(f'<section id="example"><h2>{heading}</h2><pre><code>{escape(source)}</code></pre></section>')
        md += [f'## {heading}', '', '```systemverilog', source.rstrip(), '```', '']
        heading = 'Изученные исходники' if ru else 'Inspected sources'
        body.append(f'<section id="sources"><h2>{heading}</h2><ul>')
        md += [f'## {heading}', '']
        for label, url in SOURCES:
            body.append(f'<li><a href="{url}">{label}</a></li>')
            md.append(f'- [{label}]({url})')
        body.append('</ul><p><a href="traffic_light/research/style_provenance.json">SHA-256 / provenance</a></p></section></main>')
        html = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · LSSK</title>'
                '<link rel="stylesheet" href="style.css"></head><body>' + ''.join(body) + '</body></html>')
        (ROOT / f'{name}.html').write_text(html + '\n')
        (ROOT / f'{name}.md').write_text('\n'.join(md) + '\n')


if __name__ == '__main__':
    build()
