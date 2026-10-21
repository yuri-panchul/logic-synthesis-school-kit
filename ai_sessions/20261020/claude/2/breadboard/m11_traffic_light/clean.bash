#!/usr/bin/env bash

# Exercise M11: remove the files that the simulation scripts make

set -Eeuo pipefail

cd "$(dirname "$0")"

rm -rf tb.vvp obj_dir work transcript tb.vcd icarus.log verilator.log questa.log
