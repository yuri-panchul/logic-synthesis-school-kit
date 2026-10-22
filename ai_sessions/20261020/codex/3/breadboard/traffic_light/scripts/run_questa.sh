#!/usr/bin/env bash
set -euo pipefail

# Preserve explicit tool choices; otherwise find a local Quartus installation.
questa_bin=${QUESTA_BIN:-}
if [[ -z "$questa_bin" ]]; then
    if command -v "${VSIM:-vsim}" > /dev/null 2>&1; then
        questa_bin=$(dirname -- "$(command -v "${VSIM:-vsim}")")
    else
        for candidate in "$HOME"/altera_lite/*/questa_fse/bin \
                         "$HOME"/intelFPGA_lite/*/questa_fse/bin \
                         /opt/altera_lite/*/questa_fse/bin \
                         /opt/intelFPGA_lite/*/questa_fse/bin; do
            if [[ -x "$candidate/vsim" ]]; then
                questa_bin=$candidate
                break
            fi
        done
    fi
fi
if [[ -n "$questa_bin" ]]; then
    export VLIB=${VLIB:-$questa_bin/vlib}
    export VMAP=${VMAP:-$questa_bin/vmap}
    export VLOG=${VLOG:-$questa_bin/vlog}
    export VSIM=${VSIM:-$questa_bin/vsim}
fi

# Read the user's existing license; never copy it into the project or archive.
if [[ -z "${SALT_LICENSE_SERVER:-}" && -f "$HOME/flexlm/license.dat" ]]; then
    export SALT_LICENSE_SERVER="$HOME/flexlm/license.dat"
fi

exec "$(dirname -- "${BASH_SOURCE[0]}")/run.sh" questa
