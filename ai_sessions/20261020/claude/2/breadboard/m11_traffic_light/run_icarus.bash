#!/usr/bin/env bash

# Exercise M11: run the testbench with Icarus Verilog 12 or later.
# The output goes to icarus.log and the waveform to tb.vcd,
# for GTKWave or Surfer.

set -Eeuo pipefail

cd "$(dirname "$0")"

files=(tb.sv traffic_light.sv traffic_light_chips.sv cd4017.sv cd4071.sv cd4072.sv)

if ! command -v iverilog > /dev/null
then
    printf '%s\n' "$0: iverilog not found, install Icarus Verilog 12 or later" >&2
    exit 1
fi

iverilog -g2012 -o tb.vvp "${files[@]}"
vvp -n tb.vvp | tee icarus.log

grep -q '^PASS' icarus.log
