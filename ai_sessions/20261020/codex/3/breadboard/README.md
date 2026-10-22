# Breadboard exercises / Упражнения на макетной плате

Open [index.html](index.html) for English or [index_ru.html](index_ru.html) for Russian. The site works offline; external sources require internet access. Each page links to its translation.

Откройте [index_ru.html](index_ru.html) на русском или [index.html](index.html) на английском. Сайт работает без интернета; подключение нужно только для внешних источников. На каждой странице есть ссылка на перевод.

The first lesson is **BB-FSM-01: Timofei Nikiforov’s traffic-light FSM**: red for four clock periods, yellow for two, green for four, then repeat. At 1 Hz the durations are 4/2/4 seconds. Its 15 sections include three schematics, pinouts, timing, a Moore state graph, a graph with one-hot RTL encodings, two equivalent HDL implementations, chip models, testbenches and BGM/Tiny Tapeout examples. All seven drawings are supplied in SVG and PNG, in both languages.

Первый урок — **BB-FSM-01: светофор Тимофея Никифорова**. Красный включён четыре такта, жёлтый два, зелёный четыре, затем цикл повторяется. При 1 Гц это 4/2/4 секунды. В 15 разделах есть три схемы, цоколёвка, временная диаграмма, граф автомата Мура, граф с one-hot кодами RTL, два эквивалентных варианта RTL, модели микросхем, тестбенчи и примеры BGM/Tiny Tapeout. Все семь изображений доступны в SVG и PNG на обоих языках.

Updated 21 October 2026: [SystemVerilog style rules](systemverilog_style.html), also in [Markdown](systemverilog_style.md), document conventions observed in BGM and systemverilog-homework. All 11 HDL files and embedded examples use four-space indentation, module-local timeunit/timeprecision declarations and aligned plain input/output net ports. Procedural outputs retain output logic. The yuri_rules_3.txt update limits wire to continuous declaration assignments, aligns assignment operators, gives each testbench an independent clock, uses SystemVerilog task bodies and counts timeouts in cycles. Necessary settling delays and the two low-clock falling-edge cases are explained in the style guide. Design behavior and public interfaces are preserved. Source paths, commits and hashes are recorded in `traffic_light/research/style_provenance.json`.

Обновлено 21 октября 2026 года: [правила стиля SystemVerilog](systemverilog_style_ru.html), также в [Markdown](systemverilog_style_ru.md), описывают соглашения, найденные в BGM и systemverilog-homework. Во всех 11 файлах HDL и примерах используются отступы в четыре пробела, локальные объявления timeunit/timeprecision и выровненные порты input/output без wire. Для процедурных выходов сохранён output logic. По yuri_rules_3.txt wire остаётся только в объявлениях с непрерывным присваиванием, знаки присваивания выровнены, каждому тестбенчу выделен независимый генератор такта, тела задач записаны в стиле SystemVerilog, тайм-ауты считаются в тактах. Необходимые задержки установления и два случая ожидания спада для проверки низкого CLOCK объяснены в руководстве. Поведение схемы и публичные интерфейсы сохранены. Пути, коммиты и хеши источников: `traffic_light/research/style_provenance.json`.

## Run simulation / Запуск симуляции

From this directory / Из этого каталога:

```bash
cd traffic_light
./scripts/run_icarus.sh
./scripts/run_questa.sh
./scripts/run_verilator.sh
```

Choose an installed simulator. Each script runs three benches, requires a PASS result and puts logs/build products under `traffic_light/build/`. Tool paths can be supplied using `IVERILOG`/`VVP`, `VLIB`/`VMAP`/`VLOG`/`VSIM`, or `VERILATOR`. See the lesson for the supported version target and tested versions.

Выберите установленный симулятор. Каждый скрипт запускает три тестбенча, требует PASS и сохраняет результаты в `traffic_light/build/`. Пути к программам задаются через `IVERILOG`/`VVP`, `VLIB`/`VMAP`/`VLOG`/`VSIM` или `VERILATOR`. Требуемые и проверенные версии указаны в уроке.

Observed on 2026-10-21: Icarus and Verilator simulations pass; both core designs pass Yosys + Slang synthesis checks. Questa 2025.2 compiles all sources without errors or warnings, but this execution environment prevents license checkout: the existing license matches a physical network adapter, while FlexNet returns an empty host ID and Questa reports Invalid host. Exact Icarus 13 was unavailable; testing used 12.0 and 14.0 devel. The evidence is in `traffic_light/research/`. No physical circuit or FPGA board was tested.

Результат на 2026-10-21: симуляция проходит в Icarus и Verilator; оба основных варианта проходят проверки синтеза Yosys + Slang. Questa 2025.2 компилирует все исходники без ошибок и предупреждений, но среда выполнения не позволяет получить лицензию: существующий файл соответствует физическому сетевому адаптеру, однако FlexNet возвращает пустой host ID, и Questa сообщает Invalid host. Icarus 13 отсутствовал; использовались 12.0 и 14.0 devel. Протоколы — в `traffic_light/research/`. Физическая схема и плата ПЛИС не проверялись.

Synthesis check: `python3 traffic_light/scripts/check_synthesis.py`. Use Yosys with the Slang frontend; `YOSYS` can select its executable. The older local Yosys 0.43 built-in reader cannot parse the modern time declarations. Configure FPGA/Tiny Tapeout flows to use a frontend supporting these declarations.

Проверка синтеза: `python3 traffic_light/scripts/check_synthesis.py`. Нужен Yosys с фронтендом Slang; путь к программе задаётся через `YOSYS`. Старый встроенный парсер локального Yosys 0.43 не принимает современные объявления времени. Для FPGA/Tiny Tapeout выберите фронтенд с их поддержкой.

## Rebuild / Пересборка

From this directory, with Python 3 and Inkscape / Из этого каталога, нужны Python 3 и Inkscape:

```bash
python3 tools/build_diagrams.py --png
python3 tools/build_site.py
python3 tools/package.py
python3 tools/validate.py
```

The optional interaction check is `node tools/check_demo.js`. It uses a DOM stub. In this workspace it passed in the tool's V8 isolate; Chromium could not start because of a sandbox socket restriction, so browser rendering remains unverified.

Дополнительная проверка кнопок: `node tools/check_demo.js`. Используется имитация DOM. Здесь проверка прошла в V8 инструмента; Chromium не запустился из-за ограничения сокетов в песочнице, поэтому отображение в браузере не проверено.

`draw_fsm.py` supplies the two state graphs and `fsm.json`; it is called by `build_diagrams.py`. `build_style.py` generates both editions of the style guide and is called by `build_site.py`.

`build_diagrams.py` holds the pin/net database and generates the structural HDL, wiring CSV, diagrams and connectivity checks. `build_site.py` embeds the actual HDL files into the bilingual pages. Edit the generators for changes to the generated files. The package excludes simulator build directories and includes all resources needed to read the site offline. Archive copies omit the link to download the archive itself.

`build_diagrams.py` хранит базу выводов и цепей, генерирует структурный RTL, CSV соединений, схемы и проверяет связность. `build_site.py` вставляет реальные исходники HDL в страницы на двух языках. Для изменения генерируемых файлов редактируйте генераторы. Архив не содержит сборочных каталогов симуляторов; всё нужное для чтения сайта включено. Из страниц внутри архива удалена ссылка на скачивание самого архива.

Curriculum: Yuri Panchul / [Verilog Meetup](https://verilog-meetup.com/). Traffic-light idea: Timofei Nikiforov. Prepared with Codex. / Программа: Юрий Панчул / Verilog Meetup. Идея светофора: Тимофей Никифоров. Подготовлено с помощью Codex.

The Questa runner finds local Quartus installations and uses `~/flexlm/license.dat` when `SALT_LICENSE_SERVER` is unset. It defaults to `-batch`; set `QUESTA_MODE=-c` for console mode. Run `./traffic_light/scripts/run_questa.sh` from a normal licensed terminal. No license contents are distributed.

Скрипт Questa находит локальную установку Quartus и использует `~/flexlm/license.dat`, если `SALT_LICENSE_SERVER` не задан. По умолчанию используется `-batch`; для консоли задайте `QUESTA_MODE=-c`. В обычном терминале с доступной лицензией запустите `./traffic_light/scripts/run_questa.sh`. Содержимое лицензии не распространяется.
