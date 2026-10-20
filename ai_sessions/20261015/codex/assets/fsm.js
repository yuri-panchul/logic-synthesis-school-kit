'use strict';
const russian = document.documentElement?.lang === 'ru';
// Pure prefix automaton; used by the offline worksheet generator and browser checks.
function transition(pattern, state, bit) {
  if (state >= pattern.length) return {next: 0, match: 0};
  const candidate = pattern.slice(0, state) + bit;
  const match = Number(candidate.endsWith(pattern));
  for (let length = pattern.length - 1; length >= 0; length--) {
    if (candidate.endsWith(pattern.slice(0, length))) return {next: length, match};
  }
  return {next: 0, match};
}
function taskText(pattern) {
  if (russian) return `Индивидуальное задание LSSK: конечный автомат
Последовательность: ${pattern}

Используйте DATA (нажата=1, отпущена=0), RESET и готовый генератор 555
с частотой около 0,5–1 Гц. Подключите OUT напрямую к тактовым входам регистров.
Каждый положительный фронт записывает один бит DATA. При удержании DATA
этот бит повторяется на последовательных фронтах. Учитывайте перекрытия.
Сбросьте состояние и MATCH в ноль. MATCH показывает, завершилась ли
заданная последовательность на последнем фронте.

Сдайте диаграмму префиксных состояний, кодировку, полную таблицу переходов,
уравнения D1/D0/Dmatch, план соединений выводов и результаты тестовых потоков.
Используйте не более двух битов состояния и одного бита MATCH.
Проверьте правильное совпадение, ошибочный бит, перекрытия, сброс в середине
последовательности и повтор битов при удержании DATA несколько тактов.

Компоненты: CD40174, 3× CD4073, 3× CD4072, CD4071, CD4069;
готовый генератор, два кнопочных модуля и светодиодная гребёнка на 5 В.
Таблица ответов намеренно не включена в это задание для ученика.
`;
  return `LSSK custom FSM task\nPattern: ${pattern}\n\nUse DATA (pressed=1, released=0), RESET and an assembled 555 clock\nat approximately 0.5–1 Hz. Connect clock OUT directly to the registers.\nEach rising clock edge records one DATA bit. Holding DATA repeats\nthat bit on successive edges. Recognize overlapping occurrences.\nReset state and MATCH to zero. MATCH reports whether the last clock\nedge completed the pattern.\n\nHand in a prefix-state diagram, state encoding, full transition table,\nD1/D0/Dmatch equations, pin-level wiring plan and test stream results.\nUse at most two state bits and one MATCH bit.\nTest: correct match, wrong bit, overlaps, reset mid-pattern, and\nrepeated bits when DATA is held across multiple clock edges.\n\nHardware: CD40174, 3x CD4073, 3x CD4072, CD4071, CD4069;\nassembled clock, two button modules and a 5 V LED bar.\nThe answer table is intentionally omitted from this student worksheet.\n`;
}
function renderFSM() {
  const pattern = document.querySelector('#pattern').value.trim();
  const status = document.querySelector('#fsm-status');
  const output = document.querySelector('#fsm-output');
  if (!/^[01]{2,4}$/.test(pattern)) {
    status.textContent = russian ? 'Введите от 2 до 4 двоичных цифр (0 или 1).' : 'Enter exactly 2–4 binary digits (0 or 1).';
    output.replaceChildren(); return false;
  }
  const minterms = [[], [], []]; let rows = '';
  for (let state = 0; state < 4; state++) {
    for (let bit = 0; bit < 2; bit++) {
      const {next, match} = transition(pattern, state, String(bit));
      const m = 2 * state + bit;
      [(next >> 1) & 1, next & 1, match].forEach((v, i) => { if (v) minterms[i].push(`m${m}`); });
      rows += `<tr><td>S${state} (${state.toString(2).padStart(2, '0')})${state >= pattern.length ? (russian ? ' · не используется' : ' · unused') : ''}</td><td>${bit}</td><td>S${next} (${next.toString(2).padStart(2, '0')})</td><td>${match}</td><td>m${m}</td></tr>`;
    }
  }
  status.textContent = `Pattern ${pattern}: ${pattern.length} prefix states; overlaps enabled. Two state bits + one MATCH flip-flop fit the kit.`;
  output.innerHTML = `<h3>Teacher answer table: ${pattern}</h3><p>S0 means no prefix; Sk means the first k bits of the pattern have been matched. Invalid states recover to S0.</p><div class="table-wrap"><table><thead><tr><th scope="col">Current state Q1Q0</th><th scope="col">X</th><th scope="col">Next state</th><th scope="col">Next MATCH</th><th scope="col">Minterm</th></tr></thead><tbody>${rows}</tbody></table></div><pre>${['D1', 'D0', 'Dmatch'].map((n, i) => `${n} = ${minterms[i].join(' OR ') || '0'}`).join('\n')}\nMinterm index = 4Q1 + 2Q0 + X</pre>`;
  if (russian) {
    status.textContent = `Последовательность ${pattern}: префиксных состояний — ${pattern.length}; перекрытия учитываются. Для набора достаточно двух битов состояния и одного триггера MATCH.`;
    output.innerHTML = `<h3>Таблица ответов для преподавателя: ${pattern}</h3><p>S0 означает отсутствие префикса; Sk — совпадение первых k битов последовательности. Неиспользуемые состояния возвращаются в S0.</p><div class="table-wrap"><table><thead><tr><th scope="col">Текущее состояние Q1Q0</th><th scope="col">X</th><th scope="col">Следующее состояние</th><th scope="col">Следующий MATCH</th><th scope="col">Минтерм</th></tr></thead><tbody>${rows}</tbody></table></div><pre>${['D1', 'D0', 'Dmatch'].map((n, i) => `${n} = ${minterms[i].join(' OR ') || '0'}`).join('\n')}\nИндекс минтерма = 4Q1 + 2Q0 + X</pre>`;
  }
  return true;
}
document.querySelector('#generate-fsm').addEventListener('click', renderFSM);
document.querySelector('#pattern').addEventListener('keydown', e => {if (e.key === 'Enter') renderFSM();});
document.querySelector('#download-task').addEventListener('click', () => {
  if (!renderFSM()) return;
  const pattern = document.querySelector('#pattern').value.trim();
  const url = URL.createObjectURL(new Blob([taskText(pattern)], {type: 'text/plain;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = `fsm-task-${pattern}${russian ? '-ru' : ''}.txt`;
  document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
renderFSM();
