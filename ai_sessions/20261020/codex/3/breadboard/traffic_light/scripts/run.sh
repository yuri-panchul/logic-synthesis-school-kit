#!/usr/bin/env bash
set -euo pipefail
exercise_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
simulator=${1:-icarus}
case "$simulator" in icarus|questa|verilator) ;; *) echo "Usage: $0 {icarus|questa|verilator}" >&2; exit 2;; esac
build_dir="$exercise_dir/build/$simulator"
mkdir -p "$build_dir"
cd "$build_dir"
core=("$exercise_dir/rtl/traffic_light.sv" "$exercise_dir/rtl/traffic_light_chips.sv" "$exercise_dir/models/cd4017b.sv" "$exercise_dir/models/cd4072b.sv" "$exercise_dir/models/cd4071b.sv")
wrappers=("$exercise_dir/integration/bgm_lab/lab_top.sv" "$exercise_dir/integration/bgm_hackathon/hackathon_top.sv" "$exercise_dir/integration/tinytapeout/project.v")
for top in ${TEST_TOP:-tb_cmos tb_traffic_light tb_integrations}; do
    case "$top" in tb_cmos|tb_traffic_light|tb_integrations) ;; *) echo "Unknown test: $top" >&2; exit 2;; esac
    sources=("${core[@]}" "$exercise_dir/tb/$top.sv")
    if [[ "$top" == tb_integrations ]]; then sources+=("${wrappers[@]}"); fi
    case "$simulator" in
        icarus)
            "${IVERILOG:-iverilog}" -g2012 -Wall -s "$top" -o "$top.vvp" "${sources[@]}" 2>&1 | tee "$top.compile.log"
            "${VVP:-vvp}" "$top.vvp" 2>&1 | tee "$top.log"
            ;;
        questa)
            [[ -f modelsim.ini ]] || "${VMAP:-vmap}" -c > /dev/null
            [[ -d work ]] || "${VLIB:-vlib}" work
            "${VLOG:-vlog}" -sv -work work "${sources[@]}" 2>&1 | tee "$top.compile.log"
            # $fatal/onbreak returns failure; normal $finish exits successfully.
            "${VSIM:-vsim}" "${QUESTA_MODE:--batch}" -onfinish exit "work.$top" -do "onerror {quit -code 1}; onbreak {quit -code 1}; run -all; quit -code 0" 2>&1 | tee "$top.log"
            ;;
        verilator)
            "${VERILATOR:-verilator}" --binary --timing --trace --top-module "$top" --Mdir "obj_$top" \
                -Wno-PINCONNECTEMPTY -Wno-DECLFILENAME -j 2 "${sources[@]}" > "$top.compile.log" 2>&1 || { cat "$top.compile.log"; exit 1; }
            "./obj_$top/V$top" 2>&1 | tee "$top.log"
            ;;
    esac
    grep -q 'PASS ' "$top.log" || { echo "Missing PASS from $top" >&2; exit 1; }
done
