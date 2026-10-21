#!/usr/bin/env bash

# Exercise M11: run the testbench with Questa, for example the free
# Questa Starter Edition that comes with Quartus Prime Lite.
# The output goes to questa.log and the waveform to tb.vcd.

set -Eeuo pipefail

cd "$(dirname "$0")"

files=(tb.sv traffic_light.sv traffic_light_chips.sv cd4017.sv cd4071.sv cd4072.sv)

# When vsim is not in PATH, look for it where Quartus installs it

if ! command -v vsim > /dev/null
then
    for dir in "$HOME"/intelFPGA_lite/*/questa_fse/bin  \
               "$HOME"/altera_lite/*/questa_fse/bin     \
               /opt/intelFPGA_lite/*/questa_fse/bin     \
               /opt/altera_lite/*/questa_fse/bin
    do
        if [ -x "$dir/vsim" ]
        then
            PATH="$dir:$PATH"
            break
        fi
    done
fi

if ! command -v vsim > /dev/null
then
    printf '%s\n' "$0: vsim not found, install Questa or add it to PATH" >&2
    exit 1
fi

# The Starter Edition needs a free license file from the Intel
# licensing site; Quartus keeps it in ~/flexlm/license.dat

license="$HOME/flexlm/license.dat"

# ${SALT_LICENSE_SERVER-} is empty when the variable is not set,
# where a plain $SALT_LICENSE_SERVER would stop the script (set -u)
salt_license="${SALT_LICENSE_SERVER-}"

if [ -z "$salt_license" ] && [ -f "$license" ]
then
    export SALT_LICENSE_SERVER="$license"
fi

# Older Questa versions read LM_LICENSE_FILE; ${LM_LICENSE_FILE-}
# is empty when the variable is not set
lm_license="${LM_LICENSE_FILE-}"

if [ -z "$lm_license" ] && [ -f "$license" ]
then
    export LM_LICENSE_FILE="$license"
fi

rm -rf work
vlib work > /dev/null
vlog -sv -lint "${files[@]}"
vsim -c tb -do "run -all; quit -f" | tee questa.log

grep -q 'PASS' questa.log
