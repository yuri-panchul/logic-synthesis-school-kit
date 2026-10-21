# SystemVerilog style rules

Practical rules inferred from the inspected teaching sources in Basics-Graphics-Music and systemverilog-homework. This is an analysis of examples, not an official common standard from their authors. breadboard/ uses four-space indentation and the additional requirements in yuri_rules_3.txt. Explicit user requirements take precedence over the reference examples. Updated 21 October 2026.

## 1. Four spaces; no tabs

Indent each nested block by four spaces. Use spaces for alignment and remove trailing whitespace. Four spaces are an explicit user requirement for breadboard/. The repositories contain both two- and four-space examples; this is not a claim that every upstream file uses four.

## 2. Module and block layout

Put the module name, parameter list introduced by # (, and port list on separate lines. Put begin and end on their own lines; write else on a separate line after end. A single conditional assignment may omit begin/end. Keep short case arms readable and align case labels with case, following the BGM FSM and homework formula examples.

## 3. Whitespace around syntax

Write if (condition), case (state), always_ff @ (posedge clk), function_name (arg), state [i], width' (value), and for (int i = 0; i < n; i ++). Put spaces around binary operators and after unary operators: a | b, ~ a, | state. Use spaced concatenations such as { state [8:0], state [9] }. Do not split multi-character operators such as <= or !==.

## 4. Descriptive names

Use lower_snake_case for modules and signals. Retain established interface names such as clk, rst, w_led and arg_vld. Named FSM states may be S0/S1, STATE_START, or st_idle; all occur in the inspected examples. Choose one scheme per module. Likewise use one next-state convention, next_state, new_state or d_state. This lesson uses next_state; existing wrapper parameters keep their public names.

## 5. Readable declarations and ports

Use ANSI port declarations. For net ports write input or output without wire; retain output logic for procedural outputs. Group clock/reset, data, controls and outputs with blank lines or short comments. Align directions, types and ranges into columns, with every port name in the same column. Use spaces, not tabs, and one port per line. The applied example below follows the exact layout requested by the user.

## 6. wire only with a continuous declaration assignment

Use wire if and only if the declaration includes a continuous assignment: wire a = expression;. Otherwise use logic for internal signals, module connections and testbench signals, including DUT outputs. Preserve the separately requested plain input/output net ports and output logic for procedural outputs. A wire declaration with = tracks its expression continuously; logic a = expression is one-time variable initialization and must not replace a combinational equation. This explicit user rule supersedes bare wire declarations found in some upstream examples.

## 7. State updates use always_ff and <=

Use always_ff for synthesizable edge-triggered state and nonblocking assignments (<=) inside it. Each state variable has one writer. An ordinary always remains appropriate for a testbench clock generator. Use logic rather than legacy reg in new SystemVerilog.

## 8. Combinational logic uses assign or always_comb

Use assign or a wire declaration with a continuous assignment for a simple equation. Use always_comb with blocking assignments (=) for a decision tree or decoder. Supply defaults or cover every branch for every assigned output. For an FSM, next_state = state expresses a hold default. It prevents a latch; it does not recover an illegal state automatically.

## 9. Reset follows the hardware contract

Do not change reset semantics to satisfy formatting. The BGM snail/counter examples use asynchronous active-high reset; the inspected Homework FSM/Fibonacci examples use synchronous active-high reset. This exercise keeps asynchronous active-high rst because it models CD4017 RESET. Tiny Tapeout rst_n is inverted at the wrapper boundary. No reset style is universal across the two repositories.

## 10. Make the FSM structure explicit

Distinguish the state register, next-state logic and output logic with short comments and spacing. Both enum-based and localparam/one-hot examples are present upstream. For a simple cyclic one-hot machine, a rotation equation is clearer than ten identical case arms. Keep the state diagram, reset, transition conditions and output decode consistent. In this Moore machine, output values belong inside state nodes.

## 11. Preserve encoding and observable behavior

Named states, physical chip pins and encoded bit vectors are different concepts. Do not replace the public ten-bit one-hot state output with a binary enum while calling it a style-only change. Some upstream enums use bit and others logic; use four-state logic for this lesson so unknown state is visible in simulation. No illegal-state recovery is added by this style update.

## 12. Make widths intentional

Use explicit ranges and sized literals when width matters; use '0 and '1 to fill a destination. Use parameters, $clog2 and explicit casts where appropriate. Follow the visible width-cast style, for example 8' (i). Keep signedness intentional. Upstream teaching examples sometimes use unsized constants; do not turn that into a requirement to rely on implicit extension.

## 13. Connect modules by name

Use explicit .port (signal) connections and align them. Both repositories also use shorthand and .* where names match. For this lesson, explicit connections make physical pin models and board wrappers easier to audit; replace the previous positional DUT calls. Give generate blocks descriptive names.

## 14. Separate statements and explain intent

Keep one procedural action per line, except a short case arm or loop header. Use blank lines between declarations, instances, combinational logic, registers and checks. Comments explain hardware intent or a non-obvious choice; long modules may use the repositories' dashed separators. Keep shared HDL comments in English and translate the surrounding lesson into Russian.

## 15. Testbenches remain readable and self-checking

Use logic, int, named DUT connections, procedural stimulus and an independent expected result. Keep delays and system tasks in simulation code. Compare four-state results with !== when unknowns must fail. Print PASS only after every check. Homework demonstrates this self-checking approach; breadboard/ additionally uses $fatal (1, ...) for failures so shell runners return an error.

## 16. Keep tool conventions local and justified

Do not copy configuration includes, lint suppressions or synthesis hints without their purpose. Explain any suppression and keep its scope narrow. BGM uses config.svh for its infrastructure; these standalone cores do not require that include. Keep the normal net-type default for plain input/output ports. Do not apply default_nettype none to these headers: Questa rejects their implicit net types. The standalone files therefore omit that directive and declare internal nets explicitly.

## 17. Declare simulation time inside each module

Use modern SystemVerilog declarations: timeunit 1ns; followed by timeprecision 1ps;. Put them immediately after the module header, before other module items, with four-space indentation. Apply this to RTL, chip models, wrappers and testbenches. Do not use the legacy backtick timescale directive. This is an explicit user requirement for breadboard/, not a claim about every upstream file. It keeps the previous nanosecond delay units and picosecond precision while making the time settings local to each module; it does not set the circuit clock frequency.

## 18. Align assignment operators

Align = vertically in each sequence of assignments, including declaration assignments, parameters and expected-value calculations. Align <= similarly in related register updates or stimulus. Use spaces and keep one assignment per line; do not force unrelated blocks into a single wide column.

## 19. Give the testbench clock its own generator

Initialize logic clk = 1'b0; and generate the clock with always # (period / 2) clk = ~ clk;. Define period in the module time units. This generator is the only procedural writer of clk. Never toggle the clock with blocking assignments in the middle of an initial stimulus block or in a stimulus task. The user-requested generator takes precedence over older initial/forever generators in the reference repositories.

## 20. Synchronize with events; justify each delay and falling edge

Normally use @ (posedge clk). Add # 1 only when needed to observe register updates and combinational settling, or to check a genuinely asynchronous input before the next clock. Do not replace clock-event waits with arbitrary delays. Never drive or sample on negedge unless the behavior being tested requires it. Avoid stimulus/DUT races: use nonblocking stimulus at a clock edge or change inputs after the post-edge settling/check phase. These benches use the latter approach. The timing notes below explain every special case. If a requirement cannot be followed, write need_to_deviate_from_style.html with the affected code, reason and alternatives.

## 21. Use SystemVerilog task bodies

Write task declarations followed directly by their local declarations and statements, then endtask. Do not wrap the entire body in the redundant Verilog-95 begin/end pair. Keep begin/end where required inside a loop, conditional or other nested block. Use automatic lifetime when calls may overlap; the tasks in these benches are called serially.

## 22. Count timeout limits in clock cycles

Use a separate initial block with repeat (timeout_cycles) @ (posedge clk); followed by $fatal (1, ...). Choose a bound longer than the intended test sequence. Do not use an absolute # delay as a watchdog. Every bench has a cycle timeout: 500 clocks for the core and CMOS tests, 200 for the wrapper tests.

## Applied example from this lesson

```systemverilog
// Synthesizable generic FSM. The state output uses one-hot encoding.
// Reset is asynchronous and active high; it selects S0.

module traffic_light
(
    input              clk,
    input              rst,

    output             red,
    output             yellow,
    output             green,
    output logic [9:0] state
);

    timeunit 1ns;
    timeprecision 1ps;

    wire [9:0] next_state = { state [8:0], state [9] };

    // State register

    always_ff @ (posedge clk or posedge rst)
        if (rst)
            state <= 10'b00_0000_0001;
        else
            state <= next_state;

    // Moore outputs depend only on the current state.

    assign red    = | state [3:0];
    assign yellow = | state [5:4];
    assign green  = | state [9:6];

endmodule
```

## Testbench excerpts

Excerpts from the main testbench; see the full source for the DUT, expected-value model and remaining checks.

```systemverilog
    timeunit 1ns;
    timeprecision 1ps;

    localparam period         = 20;
    localparam timeout_cycles = 500;

    logic clk = 1'b0;
    logic rst = 1'b0;

    always # (period / 2) clk = ~ clk;

    task tick;
        @ (posedge clk);
        expected = rst ? 0 : (expected + 1) % 10;
        # 1;  // Let register updates and lamp decoding settle before sampling.
        check_state ();
    endtask

    initial
    begin
        repeat (timeout_cycles) @ (posedge clk);
        $fatal (1, "Timeout after %0d clock cycles", timeout_cycles);
    end
```

## Why specific # 1 and negedge uses remain

The core test resets every state with CLOCK high and low. Its low-phase branch waits for negedge, checks falling-edge stability after # 1, then checks asynchronous reset before another rising edge. A posedge-only reset check would not establish this behavior.

The CMOS test releases INHIBIT with CLOCK low after negedge and requires no count. It separately releases INHIBIT with CLOCK high and requires a count. These are distinct CD4017 clocking conditions; limiting all stimulus to rising CLOCK edges would omit the low-level case.

Other # 1 delays allow NBA register updates and combinational decoders to settle, place initial reset after a clock event without a race, or sample asynchronous reset/inhibit and output-enable changes before the next clock. Inputs are then changed between rising edges. The period is 20 ns and the longest within-high-phase sequence ends before its 10 ns half-period. These delays are simulation scheduling, not modeled IC propagation delays.

These are the necessary cases expressly allowed by yuri_rules_3.txt. No requirement had to be abandoned, so no deviation report is needed. There are no manually driven clock pulses, arbitrary stimulus delays or absolute-time watchdogs.

## Inspected sources

- [BGM · Moore FSM](https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/labs/1_basics/1_10_snail_fsm/snail_moore_fsm.sv)
- [BGM · Mealy FSM](https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/labs/1_basics/1_10_snail_fsm/snail_mealy_fsm.sv)
- [BGM · Counter](https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/labs/1_basics/1_06_binary_counter/lab_top.sv)
- [BGM · One-hot FSM](https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/labs/2_graphics/2_6_game_2x_variant_2/game_master_fsm_2_special_style_one_hot.sv)
- [BGM · FIFO](https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/labs/4_microarchitecture/4_2_fifo/4_2_5_optimized_ff_fifo_view_2_data_layout/flip_flop_fifo_empty_full_optimized_and_debug_2.sv)
- [Homework · Sequence FSM](https://github.com/yuri-panchul/systemverilog-homework/blob/10258b2f0127495db989296dfd3f7cd0bbc77496/05_finite_state_machines/05_01_detect_sequence_using_fsm/05_01_detect_sequence_using_fsm.sv)
- [Homework · Formula FSM](https://github.com/yuri-panchul/systemverilog-homework/blob/10258b2f0127495db989296dfd3f7cd0bbc77496/05_finite_state_machines/05_04_05_sqrt_formula_fsms/formula_1_impl_1_fsm.sv)
- [Homework · Alternative FSM style](https://github.com/yuri-panchul/systemverilog-homework/blob/10258b2f0127495db989296dfd3f7cd0bbc77496/05_finite_state_machines/05_04_05_sqrt_formula_fsms/formula_1_impl_1_fsm_style_2.sv)
- [Homework · Fibonacci](https://github.com/yuri-panchul/systemverilog-homework/blob/10258b2f0127495db989296dfd3f7cd0bbc77496/02_sequential_basics/02_02_single_and_double_rate_fibonacci/02_02_single_and_double_rate_fibonacci.sv)
- [Homework · Self-checking testbench](https://github.com/yuri-panchul/systemverilog-homework/blob/10258b2f0127495db989296dfd3f7cd0bbc77496/05_finite_state_machines/05_01_detect_sequence_using_fsm/testbench.sv)
- [BGM · FIFO testbench](https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/labs/4_microarchitecture/4_2_fifo/4_2_4_flip_flop_fifo_with_counter_view_1_functional/tb.sv)
- [BGM · Pipeline testbench](https://github.com/yuri-panchul/basics-graphics-music/blob/3b18fdbaa29c39e24b8e83d362b26b57bd722471/labs/4_microarchitecture/4_3_pipelines_2/4_3_4_pow_5_pipelined_with_credit_counter/tb.sv)
- [Microarchitecture challenge · Testbench](https://github.com/verilog-meetup/systemverilog-microarchitecture-challenge-for-ai-2/blob/main/testbench.sv)
- [User requirements · yuri_rules_3.txt](traffic_light/research/yuri_rules_3.txt)
