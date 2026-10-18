#!/usr/bin/env python3
"""Build Russian editions from reviewed translations, preserving document structure.

Text is translated by exact node/attribute matching, never by replacing HTML or
JavaScript source strings. Missing prose translations stop the build.
Original external article snapshots in research/ are preserved. Separate Russian
reading editions reproduce their saved article text with author attribution.
"""
import json
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / 'data/ru'
REVIEWS = ['issues_codex_is_confident_about', 'otsebyatina_from_codex_possible_hallucinations',
           '20261015_answers_to_all_questions_1']
KITS = ['basics', 'comprehensive', 'fifo', 'arbiter', 'fsm', 'single_fifo']
PAGES = ['index.html', 'exercises.html', 'sources.html',
         *(p+'.html' for p in REVIEWS), *('kits/'+p+'.html' for p in KITS)]
PAIRS = {p: p[:-5]+'_ru.html' for p in PAGES}
PAIRS['start_en.html'] = 'start_ru.html'
PAIRS['research/browser_check.html'] = 'research/browser_check_ru.html'
# This separate proposal has a shared bilingual generator and circuit tables.
PAIRS['fifo_40105_proposal.html'] = 'fifo_40105_proposal_ru.html'
TRANSLATIONS = json.loads((RU/'translations.json').read_text())
TECHNICAL = set(json.loads((RU/'technical_strings.json').read_text()))


def translated(text):
    core = text.strip()
    if core in TRANSLATIONS:
        return text[:len(text)-len(text.lstrip())] + TRANSLATIONS[core] + text[len(text.rstrip()):]
    if core in TECHNICAL or not re.search('[a-zA-Z]', core):
        return text
    raise ValueError('Missing Russian translation: '+repr(core))


def local_link(value, context):
    url = urlsplit(value)
    if url.scheme or url.netloc or not url.path:
        return value
    target = (ROOT/context).parent.joinpath(url.path).resolve()
    try:
        relative = str(target.relative_to(ROOT))
    except ValueError:
        return value
    if relative not in PAIRS:
        return value
    # All translated partners remain in the same folder as their English page.
    new_name = Path(PAIRS[relative]).name
    path = str(Path(url.path).with_name(new_name))
    return urlunsplit(('', '', path, url.query, url.fragment))


class RussianHTML(HTMLParser):
    def __init__(self, context, text_translation=True):
        super().__init__(convert_charrefs=True)
        self.context = context
        self.text_translation = text_translation
        self.output = []
        self.raw = None
        self.language_link = False

    def handle_decl(self, value):
        self.output.append('<!'+value+'>')

    def handle_comment(self, value):
        self.output.append('<!--'+value+'-->')

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        is_language_link = tag == 'a' and 'data-language-switch' in values
        if is_language_link:
            self.language_link = True
        result = []
        for key, value in attrs:
            if value is not None:
                if tag == 'html' and key == 'lang':
                    value = 'ru'
                elif is_language_link and key == 'href':
                    value = Path(self.context).name
                elif is_language_link and key == 'lang':
                    value = 'en'
                elif key == 'href' and not (tag == 'a' and values.get('lang') == 'en'):
                    value = local_link(value, self.context)
                elif key in ['alt', 'title', 'placeholder', 'aria-label'] or (
                        tag == 'meta' and values.get('name') == 'description' and key == 'content'):
                    if self.text_translation:
                        value = translated(value)
            result.append(key if value is None else key+'="'+escape(value, quote=True)+'"')
        self.output.append('<'+tag+(' '+' '.join(result) if result else '')+'>')
        if tag in ['script', 'style']:
            self.raw = tag

    def handle_endtag(self, tag):
        self.output.append('</'+tag+'>')
        if tag == 'a':
            self.language_link = False
        if tag == self.raw:
            self.raw = None

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.output[-1] = self.output[-1][:-1]+'/>'

    def handle_data(self, text):
        if self.raw:
            self.output.append(text)
        elif self.language_link:
            self.output.append('English version')
        else:
            self.output.append(escape(translated(text) if self.text_translation else text, quote=False))


def convert(content, context, translate=True):
    parser = RussianHTML(context, translate)
    parser.feed(content)
    parser.close()
    return ''.join(parser.output)


def generate_articles():
    from model import SOURCES
    translations = json.loads((RU/'article_translations.json').read_text())
    titles = {
        'prequel': 'Введение в ПЛИС и ASIC через микросхемы малой степени интеграции',
        'improved': 'Улучшенный способ обучения школьников цифровой электронике',
        'course': 'От цифровой логики к процессору через ПЛИС',
    }
    headings = {'Basics', 'Building blocks', 'Mini-projects for review', 'Projects', 'A list of components'}
    pairs = {}
    for name, title in titles.items():
        body = '<h1>'+escape(title)+'</h1><p>Автор: Юрий Панчул / Verilog Meetup. Русская версия сохранённого текста статьи. '
        body += ('Текст Habr уже написан по-русски; переведены английские названия ссылок и описания элементов. ' if name=='course' else 'Перевод исходного английского текста. ')
        body += 'Исходные утверждения автора сохранены; исправления каталога приведены отдельно в <a href="../issues_codex_is_confident_about_ru.html">подтверждённых вопросах</a>.</p>'
        body += f'<p><a href="{name}.html">Исходный HTML с иллюстрациями и оформлением</a> · <a href="{name}.txt">Сохранённый текст</a> · <a href="{escape(SOURCES[name][1],quote=True)}">Статья на сайте автора</a></p>'
        for raw in (ROOT/'research'/f'{name}.txt').read_text().splitlines():
            line = raw.strip()
            if not line:
                continue
            if name == 'course':
                text = translations.get(line, translations.get(' '.join(line.split()), line))
            else:
                text = translations[line]  # Complete text coverage is mandatory.
            tag = 'h2' if line in headings else 'p'
            body += f'<{tag}>{escape(text)}</{tag}>\n'
        if name == 'prequel':
            body += '<h2>Исходные иллюстрации</h2>'
            for image in ['mat_gate2.jpg', '20260719_143140.jpg', '1.jpg', '2.jpg', '3.jpg', '4.jpg']:
                body += f'<figure><img src="../assets/{image}" alt="Иллюстрация Юрия Панчула: {image}" loading="lazy"><figcaption>Юрий Панчул / Verilog Meetup.</figcaption></figure>'
        html = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        html += f'<title>{escape(title)} · LSSK</title><link rel="stylesheet" href="../assets/style.css"></head><body><header><nav aria-label="Навигация"><a href="../index_ru.html">Обзор</a><a href="../sources_ru.html">Источники</a></nav></header><main id="main">{body}</main><footer>Русская версия для чтения · 16 октября 2026 года. Авторство исходного материала: Юрий Панчул / Verilog Meetup.</footer></body></html>'
        target = f'research/{name}_ru.html'
        (ROOT/target).write_text(html)
        pairs[f'research/{name}.html'] = target
    return pairs


def generate():
    for original in PAGES:
        (ROOT/PAIRS[original]).write_text(convert((ROOT/original).read_text(), original))
    archives = generate_articles()
    sources = ROOT/'sources_ru.html'
    reading_links = '<h2>Исходные статьи по-русски</h2><ul>'+''.join(
        f'<li><a href="{target}">{label}</a></li>' for target,label in [
            ('research/prequel_ru.html','Вводные заметки от 23 июля'),
            ('research/improved_ru.html','Методика и упражнения от 31 июля'),
            ('research/course_ru.html','Годовая программа курса')])+'</ul>'
    sources.write_text(sources.read_text().replace('</main>',reading_links+'</main>'))
    # The existing Russian starter has its own reviewed translation.
    start = ROOT/'start_ru.html'
    start.write_text(convert(start.read_text(), 'start_en.html', translate=False))
    # The optional browser helper is an authored HTML page too. Its shared
    # JavaScript selects its log language from html[lang].
    browser = (ROOT/'research/browser_check.html').read_text()
    browser_strings = {
        'LSSK browser checks': 'Проверка страниц LSSK в браузере',
        'Open locally in a browser that permits same-origin file access, or serve the repository with':
            'Откройте локально в браузере, разрешающем доступ между локальными файлами, либо запустите сервер в папке проекта командой',
        'and open this page. A cross-origin error means the check could not inspect the page.':
            'и откройте эту страницу. Ошибка междоменного доступа означает, что проверка не смогла прочитать страницу.',
        'Run checks': 'Запустить проверки', 'Not run.': 'Проверки ещё не запускались.',
    }
    TRANSLATIONS.update(browser_strings)
    TECHNICAL.add('python3 -m http.server')
    (ROOT/'research/browser_check_ru.html').write_text(convert(browser, 'research/browser_check.html'))
    fragments = {}
    for path in sorted((ROOT/'data').glob('*.html')):
        if path.name in ['start_en.html', 'start_ru.html']:
            continue
        context = 'kits/'+path.name.replace('_notes', '') if path.name.endswith('_notes.html') else path.name
        (RU/path.name).write_text(convert(path.read_text(), context))
        fragments[str(path.relative_to(ROOT))] = str((RU/path.name).relative_to(ROOT))
    manifest = {'pages': PAIRS, 'fragments': fragments,
                'existing_russian_fragment': 'data/start_ru.html',
                'archive_reading_editions': archives}
    (RU/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(f'Generated {len(PAGES)} Russian page editions and {len(fragments)} translated source fragments; Russian starter retained.')


if __name__ == '__main__':
    generate()
