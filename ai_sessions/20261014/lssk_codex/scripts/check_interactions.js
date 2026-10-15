/* Run with Node: node scripts/check_interactions.js
   In this session it is also runnable in the tool's V8 isolate by supplying
   globalThis.LSSK_TEST_INPUT = {fsm: source, catalog: source, exercises: [...]}. */
const fixture = typeof LSSK_TEST_INPUT !== 'undefined' ? LSSK_TEST_INPUT : (() => {
  const fs = require('fs'); const path = require('path');
  const root = path.resolve(__dirname, '..');
  return {fsm: fs.readFileSync(path.join(root, 'assets/fsm.js'), 'utf8'),
    catalog: fs.readFileSync(path.join(root, 'assets/catalog.js'), 'utf8'),
    exercises: JSON.parse(fs.readFileSync(path.join(root, 'data/catalog.json'), 'utf8')).exercises};
})();
function assert(ok, message) {if (!ok) throw new Error(message);}
const elements = new Map();
function element(selector) {
  if (!elements.has(selector)) elements.set(selector, {
    value: selector === '#pattern' ? '1011' : '', textContent: '', innerHTML: '', events: {},
    addEventListener(type, fn) {this.events[type] = fn;},
    replaceChildren() {this.innerHTML = '';}
  });
  return elements.get(selector);
}
const doc = {querySelector: element};
const app = new Function('document', fixture.fsm + '\nreturn {transition, taskText, renderFSM};')(doc);
let streams = 0, samples = 0;
for (let length = 2; length <= 4; length++) {
  for (let code = 0; code < 2 ** length; code++) {
    const pattern = code.toString(2).padStart(length, '0');
    element('#pattern').value = pattern;
    assert(app.renderFSM(), 'Valid pattern rejected');
    assert((element('#fsm-output').innerHTML.match(/<tr>/g) || []).length === 9, 'Expected 8 truth-table rows');
    for (let invalid = length; invalid < 4; invalid++) for (const bit of ['0', '1']) {
      const t = app.transition(pattern, invalid, bit); assert(t.next === 0 && t.match === 0, 'Invalid-state recovery');
    }
    for (let n = 0; n <= 10; n++) {
      for (let word = 0; word < 2 ** n; word++) {
        const input = n ? word.toString(2).padStart(n, '0') : '';
        let state = 0, history = '';
        for (const bit of input) {
          history += bit; const t = app.transition(pattern, state, bit); state = t.next;
          assert(t.match === Number(history.endsWith(pattern)), `FSM mismatch: ${pattern}/${history}`);
          assert(state >= 0 && state < length, 'Out-of-range state'); samples++;
        }
        streams++;
      }
    }
    const worksheet = app.taskText(pattern);
    assert(worksheet.includes(`Pattern: ${pattern}`) && !worksheet.includes('m7') && !worksheet.includes('D1 ='), 'Student worksheet leaks answer or misses pattern');
  }
}
for (const invalid of ['', '0', '10101', '12', '<svg>']) {
  element('#pattern').value = invalid;assert(!app.renderFSM(), 'Invalid pattern accepted');
  assert(element('#fsm-output').innerHTML === '', 'Stale answer after invalid input');
}
element('#pattern').value = '1011'; element('#pattern').events.keydown({key: 'Enter'});
assert(element('#fsm-output').innerHTML.includes('m2 OR m5 OR m6'), '1011 D1 expression');
assert(element('#fsm-output').innerHTML.includes('m1 OR m3 OR m5 OR m7'), '1011 D0 expression');
const kitIds = {basics: ['B01','B02','B03','B04','B05','B06','B07','B08','B09','B10','B11','B12','A01','A02','A03'], fifo: ['C11','P03'], arbiter: ['P04'], fsm: ['P05','P06']};
const cards = fixture.exercises.map(e => ({
  id: e.id, hidden: false, textContent: `${e.title} ${e.goal} ${Object.keys(e.bom).join(' ')}`,
  dataset: {kits: ['comprehensive', ...Object.keys(kitIds).filter(k => kitIds[k].includes(e.id))].join(' ')},
  classList: {contains: c => c === 'exercise'}, scrollIntoView() {this.scrolled = true;}
}));
const events = {}, locationMock = {hash: ''};
const catalogDoc = {querySelector: element, querySelectorAll: () => cards, getElementById: id => cards.find(c => c.id === id)};
const catalogApp = new Function('document', 'window', 'location', fixture.catalog + '\nreturn {applyFilter};')(catalogDoc, {addEventListener: (k, fn) => {events[k] = fn;}}, locationMock);
assert(cards.filter(c => !c.hidden).length === 61, 'Initial catalog count');
element('#search').value = 'fifo'; catalogApp.applyFilter();
assert(cards.filter(c => !c.hidden).length === 2, 'FIFO search');
element('#search').value = '';element('#kit-filter').value = 'basics';catalogApp.applyFilter();
assert(cards.filter(c => !c.hidden).length === 15, 'Basics kit filter');
element('#search').value = 'no-such-exercise';catalogApp.applyFilter();
assert(cards.every(c => c.hidden), 'Empty search result');
locationMock.hash = '#P03'; events.hashchange();
assert(cards.every(c => !c.hidden) && cards.find(c => c.id === 'P03').scrolled, 'Anchor must reveal filtered exercise');
const message = `PASS actual FSM JavaScript: 28 patterns, ${streams} streams, ${samples} sampled bits; invalid inputs, teacher table and task text. PASS actual catalog JavaScript: search, kit filter, empty results and anchor reveal. DOM is a test stub, not a browser render.`;
if (typeof text === 'function') text(message); else console.log(message);
