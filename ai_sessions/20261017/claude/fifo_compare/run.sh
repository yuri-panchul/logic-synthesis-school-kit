#!/bin/bash
# Reruns every check quoted in ../fifo_proposals_compared.html (about 2 minutes).
# Needs Icarus Verilog 12 (/usr/bin/iverilog): ../fifo_sync_proposal.sv does not
# compile with the Icarus 14 of oss-cad-suite (declarations after use).

set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
BGM=/home/verilog/projects/basics-graphics-music
RTL=$BGM/labs/4_microarchitecture/4_2_fifo/4_2_5_optimized_ff_fifo_view_2_data_layout/flip_flop_fifo_empty_full_optimized_and_debug_2.sv
CODEX=/home/verilog/lssk_codex/research/fifo_40105_proposal
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
IV="/usr/bin/iverilog -g2012 -I $BGM/labs/common -I $BGM/peripherals"
VVP="/usr/bin/vvp -n"

echo "== 1. Codex's own testbench, three SI/SO delay orders"
for d in "40 80" "120 40" "40 40"; do
    set -- $d
    $IV -s tb -Ptb.SI_DELAY=$1 -Ptb.SO_DELAY=$2 -o $OUT/t1 $RTL $CODEX/proposal_model.sv $CODEX/testbench.sv
    $VVP $OUT/t1 | grep -E 'PASS|FATAL'
done

echo "== 2. Push and pop together on an empty FIFO, Codex's model"
for d in "40 80" "120 40" "40 40"; do
    set -- $d
    $IV -s tb_empty -Ptb_empty.SI_DELAY=$1 -Ptb_empty.SO_DELAY=$2 -o $OUT/t2 $RTL $CODEX/proposal_model.sv $HERE/tb_empty.sv
    $VVP $OUT/t2 | grep SI_delay
done

echo "== 3. The six-cycle scenario on both circuits and the RTL"
$IV -s tb_six -o $OUT/t3 $ROOT/fifo_breadboard.sv $ROOT/fifo_sync_proposal.sv $RTL $CODEX/proposal_model.sv $HERE/tb_six.sv
$VVP $OUT/t3 | grep -E '^(cycle|drain)'

# 4-6: the chip-level harness of fifo_sync_proposal.sv, with the BB8 netlist swapped
harness () {
    sed "s/^    bb8_sync # (.t_gate/    $1 # (.t_gate/" $ROOT/fifo_sync_proposal.sv > $OUT/h_$1.sv
    $IV -s tb_sync_proposal -o $OUT/h_$1 $ROOT/fifo_breadboard.sv $OUT/h_$1.sv \
        $HERE/codex_bb8.sv $HERE/hybrid_bb8.sv $RTL
    $VVP $OUT/h_$1 | grep -E '^[A-Za-z ,]+: +bb8:|violations|^(PASS|FAIL)$' | sed 's/;  p3:.*//'
}
echo "== 4. Chip-level harness: my BB8 (variant B)";      harness bb8_sync
echo "== 5. Chip-level harness: Codex's 4 x 16 netlist";  harness bb8_codex
echo "== 6. Chip-level harness: the four-chip hybrid";    harness bb8_hybrid
