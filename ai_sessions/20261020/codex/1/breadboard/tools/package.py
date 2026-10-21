#!/usr/bin/env python3
"""Package the bilingual site and exercise sources, without simulator builds."""
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'traffic_light/traffic_light.zip'
DOWNLOAD = re.compile(r'<p class="download"><a href="traffic_light\.zip">[^<]*</a></p>')

with ZipFile(DEST, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
    for source in sorted(ROOT.rglob('*')):
        if not source.is_file() or source == DEST:
            continue
        if {'build', '__pycache__'} & set(source.relative_to(ROOT).parts):
            continue
        data = source.read_bytes()
        if source.parent.name == 'traffic_light' and source.suffix == '.html':
            html, count = DOWNLOAD.subn('', data.decode('utf-8'))
            assert count == 1, f'Archive-download link changed in {source}'
            data = html.encode('utf-8')
        info = ZipInfo.from_file(source, arcname=str(Path('breadboard') / source.relative_to(ROOT)))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, data)
print(f'Created {DEST} ({DEST.stat().st_size:,} bytes)')
