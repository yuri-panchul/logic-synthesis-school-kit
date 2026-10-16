# Logic Synthesis School Kit — teaching and kit-planning pack

Open [index.html](index.html) in a browser. Keep `assets/` beside the HTML files. Reading the pack needs no server or network; external sources and purchasing links need internet access.

Revised **15 October 2026** according to [20261015_review1.txt](20261015_review1.txt). Original task: [AGENTS.md](AGENTS.md). Curriculum and illustrations: Yuri Panchul / Verilog Meetup. LSSK price snapshot: **14 October 2026**.

## Deliverables

- [English starting guide](start_en.html) and [Russian starting guide](start_ru.html), using the four original illustrated sheets, direct connections to the specified 5 V indicators and an assembled 555 clock.
- [Exercise catalogue](exercises.html): 61 entries, with component, board, button, display, LED and M–M/M–F jumper counts, search and kit filters.
- Six kit inventories, each in HTML and spreadsheet-compatible UTF-8 CSV:

| Kit | HTML | CSV |
|---|---|---|
| Basics | [View](kits/basics.html) | [Download](kits/basics.csv) |
| Comprehensive | [View](kits/comprehensive.html) | [Download](kits/comprehensive.csv) |
| Automatic three-FIFO adder | [View](kits/fifo.html) | [Download](kits/fifo.csv) |
| Two-request round-robin arbiter | [View](kits/arbiter.html) | [Download](kits/arbiter.csv) |
| FSM / custom sequence recognizer | [View](kits/fsm.html) | [Download](kits/fsm.csv) |
| Single FIFO with four self-locking TTP223 switches | [View](kits/single_fifo.html) | [Download](kits/single_fifo.csv) |

The FSM page generates overlapping binary sequence tasks of length 2–4, transition tables and equations, with a downloadable student worksheet. DATA is sampled at each rising edge of the assembled clock. The fixed gate inventory supports all 28 offered patterns.

The three-FIFO design follows the supplied valid/ready RTL: pairs are consumed and their sums queued automatically when both operands and result-queue capacity are available. Three buttons control A_VALID, B_VALID and SUM_READY. The separate single-FIFO kit has two PUSH/POP buttons, four retained data switches and six assigned LED channels. Both use the assembled clock.

The requested review documents are [answers to all questions](20261015_answers_to_all_questions_1.html), [confirmed issues](issues_codex_is_confident_about.html) and [unverified Codex additions](otsebyatina_from_codex_possible_hallucinations.html). [Sources and counting assumptions](sources.html) and [validation results](research/validation.md) document provenance and the checks performed.

## Inventory and price model

A kit supports one learner or pair rebuilding one exercise at a time. Per-part maxima across its exercises determine reusable quantities. Jumpers receive 25% reserve and round up to 40-lead packs. Button modules are allocated individually from supplier lots; the single-FIFO kit contains exactly two. CSV `packs_to_buy` rounds up for a standalone purchase, while the component cost prices the units allocated to a kit from bulk stock.

All component prices come from LSSK column J except the explicitly requested TTP223 module. Its $0.25 price is an **unverified budget assumption**, not a retrieved supplier quote. The original seven-segment exercises retain their source-specified 560 Ω resistors. The additions rejected in the review have been removed from all kit quantities and costs.

CSV records distinguish `component`, `allowance` and `summary`; summary rows repeat calculated totals and should not be added to component rows. Loaded cost includes materials, 15% inbound allowance, 5% replacements, packaging and labor. Proposed retail targets 40% contribution after a 3% payment fee and rounds up to $5. Classroom USB supplies and meters, outgoing delivery and tax are excluded. Rare CD40108, CD40181 and DM9368 availability is unverified.

No circuit was assembled in this workspace. The transaction model is checked against the actual RTL at width=4, depth=16; the pin-level 40105 pulse adapter remains unverified. Gate quantities for that adapter are preliminary estimates. Its open details are in the separate uncertainty file.

## Rebuild and validate

Python 3.9+ is sufficient for generation and inventory validation. The RTL check additionally needs Icarus Verilog (`iverilog`, `vvp`):

```bash
python3 scripts/build.py
python3 scripts/validate.py
python3 scripts/check_fifo_reference.py
```

If Node.js is available:

```bash
node scripts/check_interactions.js
```

Here the interaction test ran in the tool's V8 isolate with a small DOM stub. It is a logic/interaction test, not a browser rendering check. `research/browser_check.html` supplies a separate real-browser check; the validation record states whether it could run.

The FIFO regression uses unchanged RTL snapshots in `research/reference/`, with original paths and hashes in `provenance.json`. The included sources reference `config.svh` but use no definitions from it, so the regression supplies an empty temporary include. It compares observable results before and after each clock edge against independent software queues.

## Editing and packaging

- `scripts/model.py`: part mappings, exercise quantities, kit coverage and costs.
- `research/lssk_rows.json`: recorded source spreadsheet values.
- `data/*.html`: guide, lesson and review body fragments.
- `assets/style.css`, `assets/catalog.js`, `assets/fsm.js`: offline presentation and interactions.
- `scripts/build.py`: generates 14 HTML pages, six CSVs and `data/catalog.json`. Edit the sources, then regenerate.
- `scripts/package.py`: rebuilds `lssk_learning_pack.zip` from the documented files, excluding caches and temporary previews.

`AGENTS.md` and the original RTL repository are unchanged.
