# SystemVerilog style rules

Practical rules inferred from the inspected teaching sources in Basics-Graphics-Music and systemverilog-homework. This is an analysis of examples, not an official common standard from their authors. breadboard/ uses a consistent four-space variant as requested by the user. Updated 21 October 2026.

## 1. Four spaces; no tabs

Indent each nested block by four spaces. Use spaces for alignment and remove trailing whitespace. Four spaces are an explicit user requirement for breadboard/. The repositories contain both two- and four-space examples; this is not a claim that every upstream file uses four.

## 2. Module and block layout

Put the module name, parameter list introduced by # (, and port list on separate lines. Put begin and end on their own lines; write else on a separate line after end. A single conditional assignment may omit begin/end. Keep short case arms readable and align case labels with case, following the BGM FSM and homework formula examples.

## 3. Whitespace around syntax

Write if (condition), case (state), always_ff @ (posedge clk), function_name (arg), state [i], width' (value), and for (int i = 0; i < n; i ++). Put spaces around binary operators and after unary operators: a | b, ~ a, | state. Use spaced concatenations such as { state [8:0], state [9] }. Do not split multi-character operators such as <= or !==.

## 4. Descriptive names

Use lower_snake_case for modules and signals. Retain established interface names such as clk, rst, w_led and arg_vld. Named FSM states may be S0/S1, STATE_START, or st_idle; all occur in the inspected examples. Choose one scheme per module. Likewise use one next-state convention, next_state, new_state or d_state. This lesson uses next_state; existing wrapper parameters keep their public names.

## 5. Readable declarations and ports

Use ANSI port declarations. Group clock/reset, data, controls and outputs with blank lines or short comments. Align related directions, types, ranges and names. Use one port connection per line in this lesson. Nearby simple declarations may share a line, but avoid compressed declarations and statements that obscure the hardware.

## 6. logic for variables; wire for nets

Use logic for values assigned in procedural blocks, including registered outputs and testbench stimulus. Use wire for explicit connections and continuously driven expressions. The repositories also omit wire on net ports; breadboard/ spells it out to work consistently with default_nettype none. A wire declaration with = is a continuous assignment; logic x = expression is variable initialization and must not replace combinational logic.

## 7. State updates use always_ff and <=

Use always_ff for synthesizable edge-triggered state and nonblocking assignments (<=) inside it. Each state variable has one writer. An ordinary always remains appropriate for a testbench clock generator. Use logic rather than legacy reg in new SystemVerilog.

## 8. Combinational logic uses assign or always_comb

Use assign or a wire initializer for a simple equation. Use always_comb with blocking assignments (=) for a decision tree or decoder. Supply defaults or cover every branch for every assigned output. For an FSM, next_state = state expresses a hold default. It prevents a latch; it does not recover an illegal state automatically.

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

Do not copy configuration includes, lint suppressions or synthesis hints without their purpose. Explain any suppression and keep its scope narrow. BGM uses config.svh for its infrastructure; these standalone cores do not require that include. breadboard/ keeps default_nettype none and an explicit timescale, restoring the net default after each module. These are local portability choices, not universal upstream rules.

## Applied example from this lesson

```systemverilog
`timescale 1ns / 1ps
`default_nettype none

// Synthesizable generic FSM. The state output uses one-hot encoding.
// Reset is asynchronous and active high; it selects S0.

module traffic_light
(
    input  wire       clk,
    input  wire       rst,

    output wire       red,
    output wire       yellow,
    output wire       green,
    output logic [9:0] state
);

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

`default_nettype wire
```

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
