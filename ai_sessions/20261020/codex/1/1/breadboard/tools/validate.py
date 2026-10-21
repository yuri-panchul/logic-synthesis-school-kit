#!/usr/bin/env python3
"""Check offline assets, bilingual lesson structure, embedded HDL and ZIP links."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import csv
import json
import struct
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids, self.links, self.sections, self.stack = set(), [], [], []
        self.lang = None
        self.cards = 0
        self.feed(path.read_text(encoding='utf-8'))
        self.close()
        assert not self.stack, (path, self.stack)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html': self.lang = attrs['lang']
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, (self.path, 'duplicate id', attrs['id'])
            self.ids.add(attrs['id'])
        if tag == 'section': self.sections.append(attrs.get('id'))
        if tag == 'article' and attrs.get('class') == 'exercise-card': self.cards += 1
        for key in ['href', 'src']:
            if key in attrs: self.links.append(attrs[key])
        if tag == 'img': assert attrs.get('alt'), (self.path, 'missing alt')
        if tag not in VOID: self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, (self.path, 'mismatched close', tag)


def check_site(root, has_archive):
    pages = {p.resolve(): Page(p) for p in root.rglob('*.html')}
    assert len(pages) == 4, len(pages)
    checked_links = 0
    for path, page in pages.items():
        lang = 'ru' if path.stem.endswith('_ru') else 'en'
        assert page.lang == lang
        other = 'index.html' if lang == 'ru' else 'index_ru.html'
        assert other in page.links, (path, 'missing language switch')
        if path.parent.name == 'traffic_light':
            assert page.sections == [f's{i:02}' for i in range(1,16)], path
            html = path.read_text()
            for link in page.links:
                if link.endswith(('.sv', '.v')):
                    assert escape((path.parent / link).read_text()) in html, (path, 'stale code', link)
        else:
            assert page.cards == 1 and not page.sections
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc: continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            assert target.is_relative_to(root.resolve()), (path, 'outside site', link)
            assert target.is_file(), (path, 'broken link', link)
            if url.fragment and target in pages:
                assert unquote(url.fragment) in pages[target].ids, (path, 'broken anchor', link)
            checked_links += 1
    assert (root / 'traffic_light/traffic_light.zip').exists() == has_archive
    return checked_links


links = check_site(ROOT, True)
images = ROOT / 'traffic_light/images'
svgs = list(images.glob('*.svg'))
assert len(svgs) == 10
for svg in svgs:
    assert ET.parse(svg).getroot().tag.endswith('svg')
    png = svg.with_suffix('.png').read_bytes()
    assert png[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', png[16:24])
    assert width >= 900 and height >= 500, (svg, width, height)
parts = list(csv.DictReader((ROOT / 'traffic_light/parts.csv').open()))
assert len(parts) == 12
assert {p['reference']: (int(p['quantity']), int(p['lssk_row'])) for p in parts if p['reference'] in ['W','M']} == {'W': (39,70), 'M': (6,71)}
with ZipFile(ROOT / 'traffic_light/traffic_light.zip') as archive:
    assert archive.testzip() is None
    assert not any('/build/' in p or '/__pycache__/' in p for p in archive.namelist())
    with tempfile.TemporaryDirectory(prefix='lssk-site-check-') as tmp:
        archive.extractall(tmp)
        archive_links = check_site(Path(tmp) / 'breadboard', False)
report = {'date': '2026-10-20', 'status': 'PASS', 'html_pages': 4,
          'sections_per_lesson': 15, 'exercises_per_index': 1,
          'local_links_checked': links, 'archive_local_links_checked': archive_links,
          'svg_png_pairs': len(svgs), 'embedded_hdl_matches_source': True,
          'scope': 'Static HTML, local links, asset formats and archive; not browser rendering.'}
(ROOT / 'traffic_light/research/site_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
