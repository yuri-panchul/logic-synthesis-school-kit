# Breadboard exercises / Упражнения на макетной плате

Open [index.html](index.html) for English or [index_ru.html](index_ru.html) for Russian. The site works offline; external sources require internet access. Each page links to its translation.

Откройте [index_ru.html](index_ru.html) на русском или [index.html](index.html) на английском. Сайт работает без интернета; подключение нужно только для внешних источников. На каждой странице есть ссылка на перевод.

The first lesson is **BB-FSM-01: Timofei Nikiforov’s traffic-light FSM**: red for four clock periods, yellow for two, green for four, then repeat. At 1 Hz the durations are 4/2/4 seconds. Its 15 sections include three schematics, pinouts, a timing diagram, two equivalent HDL implementations, chip models, testbenches and BGM/Tiny Tapeout examples. All five diagrams are supplied in SVG and PNG, in both languages.

Первый урок — **BB-FSM-01: светофор Тимофея Никифорова**. Красный включён четыре такта, жёлтый два, зелёный четыре, затем цикл повторяется. При 1 Гц это 4/2/4 секунды. В 15 разделах есть три схемы, цоколёвка, временная диаграмма, два эквивалентных варианта RTL, модели микросхем, тестбенчи и примеры BGM/Tiny Tapeout. Все пять изображений доступны в SVG и PNG на обоих языках.

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

Observed on 2026-10-20: Icarus and Verilator simulations pass; both core designs pass Yosys synthesis checks. Questa 2025.2 compiles all sources without errors or warnings, but simulation could not start without a configured license. Exact Icarus 13 was unavailable; testing used 12.0 and 14.0 devel. The evidence is in `traffic_light/research/`. No physical circuit or FPGA board was tested.

Результат на 2026-10-20: симуляция проходит в Icarus и Verilator; оба основных варианта проходят проверки синтеза Yosys. Questa 2025.2 компилирует все исходники без ошибок и предупреждений, но для симуляции не настроена лицензия. Icarus 13 отсутствовал; использовались 12.0 и 14.0 devel. Протоколы — в `traffic_light/research/`. Физическая схема и плата ПЛИС не проверялись.

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

`build_diagrams.py` holds the pin/net database and generates the structural HDL, wiring CSV, diagrams and connectivity checks. `build_site.py` embeds the actual HDL files into the bilingual pages. Edit the generators for changes to the generated files. The package excludes simulator build directories and includes all resources needed to read the site offline. Archive copies omit the link to download the archive itself.

`build_diagrams.py` хранит базу выводов и цепей, генерирует структурный RTL, CSV соединений, схемы и проверяет связность. `build_site.py` вставляет реальные исходники HDL в страницы на двух языках. Для изменения генерируемых файлов редактируйте генераторы. Архив не содержит сборочных каталогов симуляторов; всё нужное для чтения сайта включено. Из страниц внутри архива удалена ссылка на скачивание самого архива.

Curriculum: Yuri Panchul / [Verilog Meetup](https://verilog-meetup.com/). Traffic-light idea: Timofei Nikiforov. Prepared with Codex. / Программа: Юрий Панчул / Verilog Meetup. Идея светофора: Тимофей Никифоров. Подготовлено с помощью Codex.
