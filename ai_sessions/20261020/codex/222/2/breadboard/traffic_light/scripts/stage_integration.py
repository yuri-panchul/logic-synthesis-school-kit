#!/usr/bin/env python3
"""Copy a selected wrapper and its HDL dependencies into a NEW directory."""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=['lab', 'hackathon', 'tinytapeout'])
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    exercise = Path(__file__).resolve().parents[1]
    wrapper = {
        'lab': 'integration/bgm_lab/lab_top.sv',
        'hackathon': 'integration/bgm_hackathon/hackathon_top.sv',
        'tinytapeout': 'integration/tinytapeout/project.v',
    }[args.target]
    source_paths = [wrapper, 'rtl/traffic_light.sv', 'rtl/traffic_light_chips.sv',
                    'models/cd4017b.sv', 'models/cd4072b.sv', 'models/cd4071b.sv']
    copies = source_paths.copy()
    if args.target == 'tinytapeout':
        copies.append('integration/tinytapeout/info_fragment.yaml')
    for relative in copies:
        if not (exercise / relative).is_file():
            parser.error(f'Missing source: {relative}')
    destination = args.destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        parser.error(f'Destination already exists; nothing overwritten: {destination}')
    try:
        destination.mkdir(parents=True, exist_ok=False)
        for relative in copies:
            shutil.copy2(exercise / relative, destination / Path(relative).name)
        (destination / 'sources.f').write_text(
            ''.join(Path(p).name + '\n' for p in source_paths), encoding='utf-8')
    except OSError as error:
        parser.exit(1, f'Could not complete staging: {error}\n')
    print(f'Staged {len(source_paths)} HDL files for {args.target}: {destination}')
    print('sources.f lists the HDL files relative to this directory.')
    print('Next: follow the lesson to select a BGM board or merge the Tiny Tapeout manifest fragment.')


if __name__ == '__main__':
    main()
