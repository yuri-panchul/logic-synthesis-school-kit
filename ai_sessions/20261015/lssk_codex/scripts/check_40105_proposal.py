#!/usr/bin/env python3
"""Compare the phased 40105 proposal with the requested, unchanged RTL.

Tests logical ordering at PH0 and after PH8; not a vendor timing simulation.
"""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/fifo_40105_proposal'
REFERENCE = SOURCE / 'flip_flop_fifo_empty_full_optimized_and_debug_2.sv'


def main():
    provenance = json.loads((SOURCE/'provenance.json').read_text())
    assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest() == provenance['sha256']
    original = Path(provenance['original_path'])
    if original.exists():
        assert original.read_bytes() == REFERENCE.read_bytes(), 'Original RTL changed; review reference'
    logs = []
    with tempfile.TemporaryDirectory(prefix='lssk-40105-') as tmp:
        temp = Path(tmp)
        (temp/'config.svh').write_text('// No macros are used by this reference.\n')
        for width, depth in [(8,10),(4,16)]:
            executable = temp/'simulation'
            subprocess.run(['iverilog','-g2012','-s','tb','-I',str(temp),
                f'-Ptb.WIDTH={width}',f'-Ptb.DEPTH={depth}','-o',str(executable),
                str(REFERENCE),str(SOURCE/'proposal_model.sv'),str(SOURCE/'testbench.sv')],check=True)
            result = subprocess.run(['vvp',str(executable)],text=True,capture_output=True)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            line = next(line for line in result.stdout.splitlines() if line.startswith('PASS '))
            logs.append(line)
            print(line)
    report = {'reference_sha256':provenance['sha256'], 'results':logs,
              'scope':'Abstract queue model and explicit glue equations; actual RTL debug ports unconnected. Compares pre-PH0 and post-PH8 observations, legal input traces only. Not electrical or propagation-delay validation.'}
    (SOURCE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
