#!/usr/bin/env bash

# Exercise M11: run the testbench with Verilator 5.  --binary builds
# a simulator with the testbench's delays; it needs a C++20 compiler.
# The output goes to verilator.log and the waveform to tb.vcd.

set -Eeuo pipefail

cd "$(dirname "$0")"

files=(tb.sv traffic_light.sv traffic_light_chips.sv cd4017.sv cd4071.sv cd4072.sv)

# OSS CAD Suite unpacked in the home directory has Verilator too

if ! command -v verilator > /dev/null && [ -x "$HOME/oss-cad-suite/bin/verilator" ]
then
    PATH="$HOME/oss-cad-suite/bin:$PATH"
fi

if ! command -v verilator > /dev/null
then
    printf '%s\n' "$0: verilator not found, install Verilator 5" >&2
    exit 1
fi

verilator --binary -Wall --trace --top-module tb -o tb "${files[@]}"
obj_dir/tb | tee verilator.log

grep -q '^PASS' verilator.log
