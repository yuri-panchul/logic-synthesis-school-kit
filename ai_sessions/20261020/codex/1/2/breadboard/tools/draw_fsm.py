#!/usr/bin/env python3
"""Draw the ten-state Moore machine and its RTL one-hot encoding."""
from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parents[1] / 'traffic_light'
PALETTE = [('red', '#b92c43', '#fff0f3'), ('yellow', '#8e6400', '#fff7d9'),
           ('green', '#087a55', '#e8f8ef')]


def draw():
    states = []
    for i in range(10):
        color = 0 if i < 4 else 1 if i < 6 else 2
        states.append({'name': f'S{i}', 'next': f'S{(i + 1) % 10}',
                       'one_hot': format(1 << i, '010b'),
                       'outputs': [int(j == color) for j in range(3)]})
    graph = {'kind': 'Moore', 'reset': {'condition': 'rst = 1', 'target': 'S0',
             'from': 'any state, including S0', 'asynchronous': True},
             'normal_transition': 'posedge clk when rst = 0',
             'output_order': ['red', 'yellow', 'green'], 'states': states}
    (ROOT / 'fsm.json').write_text(json.dumps(graph, indent=2) + '\n')

    for lang in ['en', 'ru']:
        t = lambda en, ru: ru if lang == 'ru' else en
        for encoded in [False, True]:
            title = (t('The same FSM in one-hot RTL', 'Тот же автомат в one-hot RTL') if encoded
                     else t('Traffic-light FSM · a Moore machine', 'Конечный автомат светофора · автомат Мура'))
            width, height = 1460, 910
            top, bottom, radius = 280, 620, 88 if encoded else 70
            positions = [(200 + 265 * i, top) for i in range(5)]
            positions += [(200 + 265 * (9 - i), bottom) for i in range(5, 10)]
            svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
                   'role="img" aria-labelledby="title desc">', f'<title id="title">{escape(title)}</title>',
                   '<desc id="desc">S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → S9 → S0. '
                   + escape(t('Asynchronous reset from any state to S0. Outputs: red in S0–S3, yellow in S4–S5, green in S6–S9.',
                              'Асинхронный сброс из любого состояния в S0. Выходы: красный в S0–S3, жёлтый в S4–S5, зелёный в S6–S9.')) + '</desc>',
                   '<rect width="100%" height="100%" fill="white"/>',
                   '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
                   'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
                   '<path d="M 0 0 L 10 5 L 0 10 Z" fill="#34596c"/></marker></defs>']

            def text(x, y, value, size=21, fill='#193244', anchor='start'):
                svg.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans,sans-serif" '
                           f'font-size="{size}" fill="{fill}" text-anchor="{anchor}">{escape(value)}</text>')

            def arrow(d, attrs=''):
                svg.append(f'<path d="{d}" fill="none" stroke="#34596c" stroke-width="2.5" '
                           f'marker-end="url(#arrow)" {attrs}/>')

            text(40, 55, title, 31)
            text(40, 100, t('Every normal arrow: rising clk edge with rst = 0.',
                            'Каждая обычная стрелка: положительный фронт clk при rst = 0.'), 23)
            text(40, 140, t('Reset: rst = 1, from any state (including S0), without waiting for a clock edge.',
                            'Сброс: rst = 1, из любого состояния (включая S0), без ожидания фронта.'), 21)
            arrow(f'M 200 155 V {top - radius - 5}', 'data-reset="any-to-S0"')

            for i, state in enumerate(states):
                x, y = positions[i]
                nx, ny = positions[(i + 1) % 10]
                if y == ny:
                    direction = 1 if nx > x else -1
                    arrow(f'M {x + direction * (radius + 5)} {y} H {nx - direction * (radius + 5)}',
                          f'data-from="S{i}" data-to="{state["next"]}" data-event="posedge clk; rst=0"')
                    text((x + nx) / 2, y - 17, 'clk ↑', 19, anchor='middle')
                else:
                    direction = 1 if ny > y else -1
                    arrow(f'M {x} {y + direction * (radius + 5)} V {ny - direction * (radius + 5)}',
                          f'data-from="S{i}" data-to="{state["next"]}" data-event="posedge clk; rst=0"')
                    text(x + 26, (y + ny) / 2 + 7, 'clk ↑', 19)
                color = next(j for j, value in enumerate(state['outputs']) if value)
                _, stroke, fill = PALETTE[color]
                svg.append(f'<g id="state-S{i}" data-bits="{state["one_hot"]}" '
                           f'data-outputs="{"".join(map(str, state["outputs"]))}">'
                           f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
                text(x, y - 17, state['name'], 29, stroke, 'middle')
                text(x, y + 16, state['one_hot'] if encoded else ''.join(map(str, state['outputs'])),
                     20 if encoded else 26, stroke, 'middle')
                svg.append('</g>')

            text(730, 423, t('One state = one clock period', 'Одно состояние = один период такта'), 25, anchor='middle')
            text(730, 464, t('4 red → 2 yellow → 4 green → repeat', '4 красных → 2 жёлтых → 4 зелёных → повтор'), 22, anchor='middle')
            if encoded:
                text(40, 780, 'next_state = { state [8:0], state [9] };', 27)
                text(40, 824, t('Inside each node: state [9:0]. The 1 moves left; bit 9 wraps to bit 0.',
                                'Внутри вершины: state [9:0]. Единица сдвигается влево; бит 9 возвращается в бит 0.'), 21)
                text(40, 868, t('These are generic RTL encodings, not the internal Johnson-counter bits of a physical 4017.',
                                'Это кодирование обобщённого RTL, а не внутренние биты счётчика Джонсона физической 4017.'), 20)
            else:
                text(40, 780, t('Node outputs: { red, yellow, green } — 100 / 010 / 001.',
                                'Выходы внутри вершины: { red, yellow, green } — 100 / 010 / 001.'), 24)
                text(40, 824, t('Outputs depend only on the current state. While rst = 1, S0 stays selected.',
                                'Выходы зависят только от текущего состояния. Пока rst = 1, выбран S0.'), 22)
                text(40, 868, t('No counting edge: hold the current state. At 1 Hz, a complete cycle lasts 10 seconds.',
                                'Без счётного фронта состояние сохраняется. При 1 Гц полный цикл длится 10 секунд.'), 21)
            svg.append('</svg>')
            name = 'fsm_encoding' if encoded else 'fsm'
            (ROOT / 'images' / f'{name}_{lang}.svg').write_text('\n'.join(svg) + '\n')


if __name__ == '__main__':
    draw()
