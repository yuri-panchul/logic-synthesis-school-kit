#!/usr/bin/env python3
"""Publish the observed repository conventions and the chosen breadboard style."""
from pathlib import Path
from html import escape
import re

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
    ('BGM · FIFO testbench', BGM + 'labs/4_microarchitecture/4_2_fifo/4_2_4_flip_flop_fifo_with_counter_view_1_functional/tb.sv'),
    ('BGM · Pipeline testbench', BGM + 'labs/4_microarchitecture/4_3_pipelines_2/4_3_4_pow_5_pipelined_with_credit_counter/tb.sv'),
    ('Microarchitecture challenge · Testbench', 'https://github.com/verilog-meetup/systemverilog-microarchitecture-challenge-for-ai-2/blob/main/testbench.sv'),
    ('User requirements · yuri_rules_3.txt', 'traffic_light/research/yuri_rules_3.txt'),
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
     'Use ANSI port declarations. For net ports write input or output without wire; retain output logic for procedural outputs. Group clock/reset, data, controls and outputs with blank lines or short comments. Align directions, types and ranges into columns, with every port name in the same column. Use spaces, not tabs, and one port per line. The applied example below follows the exact layout requested by the user.',
     'Используйте объявления портов ANSI. Для портов-цепей пишите input или output без wire; для процедурных выходов сохраняйте output logic. Разделяйте такт/сброс, данные, управление и выходы пустыми строками или короткими комментариями. Выравнивайте направления, типы и диапазоны по столбцам, а все имена портов начинайте в одном столбце. Используйте пробелы, не табуляцию; каждый порт — на отдельной строке. Пример ниже соответствует оформлению, заданному пользователем.'),
    ('wire only with a continuous declaration assignment', 'wire — только с непрерывным присваиванием в объявлении',
     'Use wire if and only if the declaration includes a continuous assignment: wire a = expression;. Otherwise use logic for internal signals, module connections and testbench signals, including DUT outputs. Preserve the separately requested plain input/output net ports and output logic for procedural outputs. A wire declaration with = tracks its expression continuously; logic a = expression is one-time variable initialization and must not replace a combinational equation. This explicit user rule supersedes bare wire declarations found in some upstream examples.',
     'Используйте wire тогда и только тогда, когда объявление содержит непрерывное присваивание: wire a = expression;. В остальных объявлениях внутренних сигналов, соединений модулей и сигналов тестбенча, включая выходы DUT, используйте logic. Сохраняйте отдельно заданное оформление портов: input/output без wire и output logic для процедурных выходов. wire с = непрерывно вычисляет выражение; logic a = expression — однократная инициализация переменной, которая не заменяет комбинационное уравнение. Это явное правило пользователя имеет приоритет над объявлениями wire без присваивания из некоторых исходных примеров.'),
    ('State updates use always_ff and <=', 'Обновление состояния: always_ff и <=',
     'Use always_ff for synthesizable edge-triggered state and nonblocking assignments (<=) inside it. Each state variable has one writer. An ordinary always remains appropriate for a testbench clock generator. Use logic rather than legacy reg in new SystemVerilog.',
     'Для синтезируемого состояния, меняющегося по фронту, используйте always_ff и неблокирующие присваивания (<=). У каждой переменной состояния должен быть один источник записи. Обычный always допустим для генератора такта в тестбенче. В новом SystemVerilog используйте logic вместо устаревшего reg.'),
    ('Combinational logic uses assign or always_comb', 'Комбинационная логика: assign или always_comb',
     'Use assign or a wire declaration with a continuous assignment for a simple equation. Use always_comb with blocking assignments (=) for a decision tree or decoder. Supply defaults or cover every branch for every assigned output. For an FSM, next_state = state expresses a hold default. It prevents a latch; it does not recover an illegal state automatically.',
     'Для простого уравнения используйте assign или объявление wire с непрерывным присваиванием. Для дерева решений или дешифратора — always_comb с блокирующими присваиваниями (=). Задавайте значения по умолчанию или охватывайте все ветви для каждого выхода. next_state = state задаёт удержание состояния. Это предотвращает защёлку, но не восстанавливает автоматически недопустимое состояние.'),
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
     'Do not copy configuration includes, lint suppressions or synthesis hints without their purpose. Explain any suppression and keep its scope narrow. BGM uses config.svh for its infrastructure; these standalone cores do not require that include. Keep the normal net-type default for plain input/output ports. Do not apply default_nettype none to these headers: Questa rejects their implicit net types. The standalone files therefore omit that directive and declare internal nets explicitly.',
     'Не копируйте include конфигурации, подавление предупреждений или подсказки синтезатору без понимания цели. Объясняйте подавления и ограничивайте область действия. BGM использует config.svh для своей инфраструктуры; автономным модулям урока он не нужен. Для обычных портов input/output сохраняйте стандартный тип цепей по умолчанию. Не применяйте default_nettype none к этим заголовкам: Questa отвергает их неявные типы цепей. Поэтому автономные файлы не содержат эту директиву, а внутренние цепи объявлены явно.'),
    ('Declare simulation time inside each module', 'Объявляйте единицы времени внутри каждого модуля',
     'Use modern SystemVerilog declarations: timeunit 1ns; followed by timeprecision 1ps;. Put them immediately after the module header, before other module items, with four-space indentation. Apply this to RTL, chip models, wrappers and testbenches. Do not use the legacy backtick timescale directive. This is an explicit user requirement for breadboard/, not a claim about every upstream file. It keeps the previous nanosecond delay units and picosecond precision while making the time settings local to each module; it does not set the circuit clock frequency.',
     'Используйте современные объявления SystemVerilog: timeunit 1ns; и затем timeprecision 1ps;. Размещайте их сразу после заголовка модуля, перед остальными элементами, с отступом в четыре пробела. Это относится к RTL, моделям микросхем, оболочкам и тестбенчам. Не используйте устаревшую директиву timescale с обратной кавычкой. Это явное требование пользователя для breadboard/, а не утверждение обо всех исходных файлах репозиториев. Сохраняются единица задержек в наносекунду и точность в пикосекунду; параметры времени теперь локальны для каждого модуля. Частоту такта эти объявления не задают.'),
    ('Align assignment operators', 'Выравнивайте знаки присваивания',
     'Align = vertically in each sequence of assignments, including declaration assignments, parameters and expected-value calculations. Align <= similarly in related register updates or stimulus. Use spaces and keep one assignment per line; do not force unrelated blocks into a single wide column.',
     'Выравнивайте = по вертикали в каждой последовательности присваиваний, включая присваивания в объявлениях, параметры и расчёт ожидаемых значений. Аналогично выравнивайте <= в связанных обновлениях регистров или стимулах. Используйте пробелы и одно присваивание на строку; не объединяйте несвязанные блоки в один широкий столбец.'),
    ('Give the testbench clock its own generator', 'Выделяйте генератор такта тестбенча',
     'Initialize logic clk = 1\'b0; and generate the clock with always # (period / 2) clk = ~ clk;. Define period in the module time units. This generator is the only procedural writer of clk. Never toggle the clock with blocking assignments in the middle of an initial stimulus block or in a stimulus task. The user-requested generator takes precedence over older initial/forever generators in the reference repositories.',
     'Объявляйте logic clk = 1\'b0; и формируйте такт через always # (period / 2) clk = ~ clk;. Задавайте period в единицах времени модуля. Этот генератор — единственный процедурный источник clk. Не переключайте такт блокирующими присваиваниями внутри initial со стимулами или внутри задачи стимулов. Заданный пользователем генератор имеет приоритет над прежними вариантами initial/forever из исходных репозиториев.'),
    ('Synchronize with events; justify each delay and falling edge', 'Синхронизируйтесь по событиям; обосновывайте задержки и спады',
     'Normally use @ (posedge clk). Add # 1 only when needed to observe register updates and combinational settling, or to check a genuinely asynchronous input before the next clock. Do not replace clock-event waits with arbitrary delays. Never drive or sample on negedge unless the behavior being tested requires it. Avoid stimulus/DUT races: use nonblocking stimulus at a clock edge or change inputs after the post-edge settling/check phase. These benches use the latter approach. The timing notes below explain every special case. If a requirement cannot be followed, write need_to_deviate_from_style.html with the affected code, reason and alternatives.',
     'Обычно используйте @ (posedge clk). Добавляйте # 1 только при необходимости увидеть обновление регистров и установление комбинационных выходов либо проверить асинхронный вход до следующего такта. Не заменяйте ожидание тактового события произвольной задержкой. Не задавайте и не считывайте сигналы по negedge, если проверяемое поведение этого не требует. Избегайте гонок тестбенча с DUT: задавайте стимулы неблокирующими присваиваниями по фронту либо меняйте входы после установления и проверки выходов. Здесь выбран второй вариант. Все особые случаи объяснены ниже. Если требование невозможно выполнить, создайте need_to_deviate_from_style.html с указанием кода, причины и альтернатив.'),
    ('Use SystemVerilog task bodies', 'Используйте тела задач SystemVerilog',
     'Write task declarations followed directly by their local declarations and statements, then endtask. Do not wrap the entire body in the redundant Verilog-95 begin/end pair. Keep begin/end where required inside a loop, conditional or other nested block. Use automatic lifetime when calls may overlap; the tasks in these benches are called serially.',
     'После объявления task пишите непосредственно локальные объявления и операторы, затем endtask. Не оборачивайте всё тело в избыточную пару begin/end в стиле Verilog-95. Сохраняйте begin/end там, где они нужны внутри цикла, условия или другого вложенного блока. Для перекрывающихся вызовов используйте automatic; здесь задачи вызываются последовательно.'),
    ('Count timeout limits in clock cycles', 'Задавайте тайм-ауты в тактах',
     'Use a separate initial block with repeat (timeout_cycles) @ (posedge clk); followed by $fatal (1, ...). Choose a bound longer than the intended test sequence. Do not use an absolute # delay as a watchdog. Every bench has a cycle timeout: 500 clocks for the core and CMOS tests, 200 for the wrapper tests.',
     'Используйте отдельный initial с repeat (timeout_cycles) @ (posedge clk);, после которого вызывается $fatal (1, ...). Предел должен превышать длину штатного сценария. Не задавайте сторожевой тайм-аут абсолютной задержкой #. Во всех тестбенчах есть тайм-аут в тактах: 500 для основного теста и CMOS, 200 для оболочек.'),
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
            'вариант с отступом в четыре пробела и дополнительными требованиями yuri_rules_3.txt. '
            'Явные требования пользователя имеют приоритет над исходными примерами. Обновлено 21 октября 2026 года.' if ru else
            'Practical rules inferred from the inspected teaching sources in Basics-Graphics-Music and '
            'systemverilog-homework. This is an analysis of examples, not an official common standard from their authors. '
            'breadboard/ uses four-space indentation and the additional requirements in yuri_rules_3.txt. '
            'Explicit user requirements take precedence over the reference examples. Updated 21 October 2026.'
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
        heading = 'Фрагменты тестбенча' if ru else 'Testbench excerpts'
        tb = (ROOT / 'traffic_light/tb/tb_traffic_light.sv').read_text()
        excerpt = tb[tb.index('    timeunit'):tb.index('    logic red_generic')].rstrip()
        excerpt += '\n\n' + re.search(r'    task tick;.*?    endtask', tb, re.S).group()
        excerpt += '\n\n' + tb[tb.rindex('    initial'):tb.index('\nendmodule')].rstrip()
        note = ('Фрагменты из основного тестбенча; DUT, расчёт ожидаемого результата и остальные проверки находятся в полном исходнике.' if ru else
                'Excerpts from the main testbench; see the full source for the DUT, expected-value model and remaining checks.')
        body.append(f'<section id="testbench"><h2>{heading}</h2><p>{note} '
                    '<a href="traffic_light/tb/tb_traffic_light.sv">tb_traffic_light.sv</a></p>'
                    f'<pre><code>{escape(excerpt)}</code></pre></section>')
        md += [f'## {heading}', '', note, '', '```systemverilog', excerpt, '```', '']
        heading = 'Почему остаются отдельные # 1 и negedge' if ru else 'Why specific # 1 and negedge uses remain'
        notes = [
            ('The core test resets every state with CLOCK high and low. Its low-phase branch waits for negedge, checks falling-edge stability after # 1, then checks asynchronous reset before another rising edge. A posedge-only reset check would not establish this behavior.',
             'Основной тест проверяет сброс из каждого состояния при высоком и низком CLOCK. Ветвь низкого уровня ждёт negedge, через # 1 проверяет отсутствие изменения по спаду, затем проверяет асинхронный сброс до следующего фронта. Проверка сброса только по posedge не доказывала бы это поведение.'),
            ('The CMOS test releases INHIBIT with CLOCK low after negedge and requires no count. It separately releases INHIBIT with CLOCK high and requires a count. These are distinct CD4017 clocking conditions; limiting all stimulus to rising CLOCK edges would omit the low-level case.',
             'Тест CMOS снимает INHIBIT при низком CLOCK после negedge и требует отсутствия счёта. Отдельно он снимает INHIBIT при высоком CLOCK и требует инкремента. Это разные условия тактирования CD4017; стимулы только по фронтам CLOCK исключили бы проверку низкого уровня.'),
            ('Other # 1 delays allow NBA register updates and combinational decoders to settle, place initial reset after a clock event without a race, or sample asynchronous reset/inhibit and output-enable changes before the next clock. Inputs are then changed between rising edges. The period is 20 ns and the longest within-high-phase sequence ends before its 10 ns half-period. These delays are simulation scheduling, not modeled IC propagation delays.',
             'Остальные # 1 дают завершиться неблокирующим обновлениям регистров и дешифрации, размещают начальный сброс после тактового события без гонки либо позволяют проверить асинхронные reset/inhibit и разрешение выходов до следующего такта. Затем входы меняются между фронтами. Период равен 20 нс; самая длинная последовательность при высоком CLOCK завершается до конца полупериода в 10 нс. Эти задержки управляют порядком событий симуляции и не моделируют задержки микросхем.'),
            ('These are the necessary cases expressly allowed by yuri_rules_3.txt. No requirement had to be abandoned, so no deviation report is needed. There are no manually driven clock pulses, arbitrary stimulus delays or absolute-time watchdogs.',
             'Это необходимые случаи, прямо разрешённые оговорками yuri_rules_3.txt. Отказываться от требований не потребовалось, поэтому отчёт об отклонениях не нужен. Нет ручного формирования тактовых импульсов, произвольных задержек стимулов и тайм-аутов в абсолютном времени.'),
        ]
        body.append(f'<section id="timing-notes"><h2>{heading}</h2>')
        md += [f'## {heading}', '']
        for note_pair in notes:
            note = note_pair[1 if ru else 0]
            body.append(f'<p>{escape(note)}</p>')
            md += [note, '']
        body.append('</section>')
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
