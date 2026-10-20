#!/usr/bin/env python3
"""Package the generated documents together with editable sources and evidence."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT / 'lssk_learning_pack.zip'
files = list(ROOT.glob('*.html')) + [ROOT/'AGENTS.md', ROOT/'20261015_review1.txt', ROOT/'README.md']
for folder in ['assets', 'data', 'kits', 'scripts', 'research']:
    for path in (ROOT/folder).rglob('*'):
        if (path.is_file() and '__pycache__' not in path.parts
                and not path.name.startswith(('preview_', 'browser_check_result'))
                and path.name != 'interaction_fixture.json'):
            files.append(path)
files = sorted(set(files))
with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
    for path in files:
        z.write(path, path.relative_to(ROOT))
with ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(files)
    for path in files:
        assert z.read(str(path.relative_to(ROOT))) == path.read_bytes()
print(f'PASS {archive.name}: {len(files)} files; integrity and source byte comparison checked')
