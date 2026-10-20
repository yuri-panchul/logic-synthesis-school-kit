# Logic Synthesis School Kit — teaching and kit-planning pack

Open [index.html](index.html) directly in a browser. No server, build step, network connection or external font is needed to read the pack. Keep `assets/` beside the HTML files. External sources and purchasing links need internet access.

Created from the task in [AGENTS.md](AGENTS.md). Curriculum and original illustrations: Yuri Panchul / Verilog Meetup. Source snapshot: **14 October 2026**.

## Deliverables

- [English starting guide](start_en.html) and [Russian starting guide](start_ru.html): all four original illustrated sheets, component selection, exact first-gate wiring, truth tables, D-flip-flop experiment and troubleshooting.
- [Exercise catalogue](exercises.html): **61 entries**, merging the July article and Habr breadboard lessons, with explicit component, board, button, display, LED and M–M/M–F jumper counts. Includes search and kit filters.
- Five kit inventories, each in HTML and spreadsheet-compatible UTF-8 CSV:

| Kit | HTML | CSV |
|---|---|---|
| Basics | [View](kits/basics.html) | [Download](kits/basics.csv) |
| Comprehensive | [View](kits/comprehensive.html) | [Download](kits/comprehensive.csv) |
| FIFO | [View](kits/fifo.html) | [Download](kits/fifo.csv) |
| Two-request round-robin arbiter | [View](kits/arbiter.html) | [Download](kits/arbiter.csv) |
| FSM / custom sequence recognizer | [View](kits/fsm.html) | [Download](kits/fsm.csv) |

The FSM page generates overlapping binary sequence tasks of length 2–4, transition tables and minterm equations, with a downloadable student worksheet that omits the answer. The bounded gate inventory supports every pattern offered by the generator.

[Sources and assumptions](sources.html) explains source corrections, price provenance, sourcing constraints, power alternatives and engineering additions. [Validation results](research/validation.md) records what was and was not checked.

## Inventory and price model

A kit supports one learner or pair rebuilding **one exercise at a time**. Per-part maxima across its exercises determine reusable quantities. Jumper allowances get 25% spare and round up to 40-lead packs. Button modules round to packs of five. Decoupling capacitors get 20% spare. The comprehensive kit includes the rare CD40108, CD40181 and DM9368 devices; their availability is unverified.

All prices are USD estimates from LSSK column J or visibly marked engineering allowances, not current quotations. CSV records distinguish `component`, `allowance` and `summary`; do not sum every numeric row, because summary rows repeat calculated totals. Individual pack units and normalized prices are explicit. Loaded cost includes materials, 15% inbound allowance, 5% replacements, packaging and labor. Proposed retail targets 40% contribution after a 3% payment fee and rounds up to $5. Shared classroom USB sources and meters, outgoing delivery and tax are excluded.

No breadboard circuit was physically assembled in this workspace. FIFO/serial timing, rare parts, actual LED/button variants, jumper estimates and assembly labor need a pilot build. The FIFO kit describes a manually staged transfer protocol, not a complete automatic controller.

## Rebuild and validate

Python 3.9+; the build and Python validation use only the standard library:

```bash
python3 scripts/build.py
python3 scripts/validate.py
```

If Node.js is available, check the actual interaction scripts with a minimal DOM stub:

```bash
node scripts/check_interactions.js
```

Node was not installed here; the same JavaScript test was executed in the tool's V8 isolate. Chromium was present but could not start under the sandbox's socket restrictions. Rendering and print layout therefore remain unverified.

`research/browser_check.html` is an optional real-browser check page. Open it in an unrestricted browser to exercise document loading, image loading, mobile-width overflow, catalogue filtering and FSM generation. This helper was prepared but could not be run here.

## Editing

- `scripts/model.py`: reviewed part mappings, per-exercise quantities, kit coverage and cost formulas.
- `research/lssk_rows.json`: original LSSK cell values, extracted from the saved workbook; do not edit this to change estimates.
- `data/start_en.html`, `data/start_ru.html`: guide body fragments.
- `data/*_notes.html`: kit-specific lesson details.
- `data/sources.html`: provenance and engineering notes.
- `assets/style.css`, `assets/catalog.js`, `assets/fsm.js`: offline presentation and interactions.
- `scripts/build.py`: creates all 10 HTML pages, five CSVs and the machine-readable `data/catalog.json`. Edit source files, then regenerate; direct edits to generated HTML will be overwritten.

The original `AGENTS.md` was left unchanged. The workspace has no usable Git repository, so no commit was created.
