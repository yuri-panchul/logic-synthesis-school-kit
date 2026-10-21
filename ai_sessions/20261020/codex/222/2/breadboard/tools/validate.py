#!/usr/bin/env python3
"""Check offline assets, bilingual lesson structure, embedded HDL and ZIP links."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import csv
import json
import re
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
    assert len(pages) == 6, len(pages)
    checked_links = 0
    for path, page in pages.items():
        lang = 'ru' if path.stem.endswith('_ru') else 'en'
        assert page.lang == lang
        base = 'systemverilog_style' if path.stem.startswith('systemverilog_style') else 'index'
        other = base + ('.html' if lang == 'ru' else '_ru.html')
        assert other in page.links, (path, 'missing language switch')
        if path.parent.name == 'traffic_light':
            assert page.sections == [f's{i:02}' for i in range(1,16)], path
            html = path.read_text()
            for link in page.links:
                if link.endswith(('.sv', '.v')):
                    assert escape((path.parent / link).read_text()) in html, (path, 'stale code', link)
            for name in ['fsm', 'fsm_encoding']:
                assert f'images/{name}_{lang}.svg' in page.links, (path, 'missing state diagram')
        elif base == 'systemverilog_style':
            assert page.sections == [f'rule{i:02}' for i in range(1,17)] + ['example', 'sources']
            assert escape((root / 'traffic_light/rtl/traffic_light.sv').read_text()) in path.read_text()
            assert path.with_suffix('.md').is_file()
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
assert len(svgs) == 14
for svg in svgs:
    assert ET.parse(svg).getroot().tag.endswith('svg')
    png = svg.with_suffix('.png').read_bytes()
    assert png[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', png[16:24])
    assert width >= 900 and height >= 500, (svg, width, height)

# Check graph labels and directed edges independently of drawing geometry.
fsm = json.loads((ROOT / 'traffic_light/fsm.json').read_text())
assert len(fsm['states']) == 10 and fsm['kind'] == 'Moore'
assert fsm['reset']['target'] == 'S0' and fsm['reset']['asynchronous']
for i, state in enumerate(fsm['states']):
    assert state == {'name': f'S{i}', 'next': f'S{(i + 1) % 10}',
                     'one_hot': format(1 << i, '010b'),
                     'outputs': [int(i < 4), int(4 <= i < 6), int(i >= 6)]}
for lang in ['en', 'ru']:
    for name in ['fsm', 'fsm_encoding']:
        elements = list(ET.parse(images / f'{name}_{lang}.svg').iter())
        edges = [(e.get('data-from'), e.get('data-to')) for e in elements if e.get('data-from')]
        assert edges == [(f'S{i}', f'S{(i + 1) % 10}') for i in range(10)]
        nodes = [e for e in elements if e.get('id', '').startswith('state-S')]
        assert len(nodes) == 10
        for i, node in enumerate(nodes):
            assert node.get('data-bits') == fsm['states'][i]['one_hot']
            assert node.get('data-outputs') == ''.join(map(str, fsm['states'][i]['outputs']))

# Check the explicitly requested indentation in all authored HDL, not build output.
hdl_files = [p for p in (ROOT / 'traffic_light').rglob('*')
             if p.suffix in ['.sv', '.v'] and 'build' not in p.relative_to(ROOT).parts]
assert len(hdl_files) == 11
for source in hdl_files:
    contents = source.read_text()
    for number, line in enumerate(contents.splitlines(), 1):
        assert '\t' not in line and line == line.rstrip(), (source, number, 'whitespace')
        assert (len(line) - len(line.lstrip(' '))) % 4 == 0, (source, number, 'indentation')
    code = re.sub(r'//[^\n]*', '', contents)
    assert not re.search(r'\breg\b', code), (source, 'legacy reg')
    assert not re.search(r'\balways\s*@', code), (source, 'use always_ff/always_comb')
parts = list(csv.DictReader((ROOT / 'traffic_light/parts.csv').open()))
assert len(parts) == 12
assert {p['reference']: (int(p['quantity']), int(p['lssk_row'])) for p in parts if p['reference'] in ['W','M']} == {'W': (39,70), 'M': (6,71)}
with ZipFile(ROOT / 'traffic_light/traffic_light.zip') as archive:
    assert archive.testzip() is None
    assert not any('/build/' in p or '/__pycache__/' in p for p in archive.namelist())
    with tempfile.TemporaryDirectory(prefix='lssk-site-check-') as tmp:
        archive.extractall(tmp)
        archive_links = check_site(Path(tmp) / 'breadboard', False)
report = {'date': '2026-10-21', 'status': 'PASS', 'html_pages': 6,
          'sections_per_lesson': 15, 'exercises_per_index': 1,
          'local_links_checked': links, 'archive_local_links_checked': archive_links,
          'svg_png_pairs': len(svgs), 'embedded_hdl_matches_source': True,
          'fsm_state_graphs_checked': 4, 'hdl_files_with_four_space_indentation': len(hdl_files),
          'scope': 'Static HTML, local links, asset formats and archive; not browser rendering.'}
(ROOT / 'traffic_light/research/site_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
