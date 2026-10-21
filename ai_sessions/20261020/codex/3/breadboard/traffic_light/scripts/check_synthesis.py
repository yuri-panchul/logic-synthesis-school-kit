#!/usr/bin/env python3
"""Check both cores using Yosys with the Slang SystemVerilog frontend."""
import os
from pathlib import Path
import subprocess


def main():
    exercise = Path(__file__).resolve().parents[1]
    build = exercise / 'build/synthesis'
    build.mkdir(parents=True, exist_ok=True)
    sources = sorted((exercise / 'rtl').glob('*.sv'))
    sources += sorted((exercise / 'models').glob('*.sv'))
    # Fixed relative source names also work when the exercise directory has spaces.
    filenames = ' '.join(p.relative_to(exercise).as_posix() for p in sources)
    yosys = os.environ.get('YOSYS', 'yosys')

    for top in ['traffic_light', 'traffic_light_chips']:
        commands = (f'read_slang --top {top} {filenames}; '
                    f'synth -top {top} -flatten; check -assert; stat')
        log = build / f'{top}.log'
        with log.open('w') as output:
            result = subprocess.run([yosys, '-Q', '-m', 'slang', '-p', commands],
                                    cwd=exercise, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text())
            raise SystemExit(result.returncode)
        print(f'PASS synthesis: {top} (Yosys + Slang); {log}')


if __name__ == '__main__':
    main()
