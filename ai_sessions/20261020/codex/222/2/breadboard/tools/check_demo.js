'use strict';
// A DOM-stub interaction check; it does not measure browser layout.
function checkDemo(source) {
  const assert = (ok, message) => { if (!ok) throw new Error(message); };
  function element() {
    const classes = new Set();
    return {
      children: [], textContent: '', attrs: {}, events: {},
      classList: { toggle(name, on) { on ? classes.add(name) : classes.delete(name); }, contains(name) { return classes.has(name); } },
      append(child) { this.children.push(child); },
      setAttribute(name, value) { this.attrs[name] = value; },
      addEventListener(name, callback) { this.events[name] = callback; },
      click() { this.events.click(); }
    };
  }
  const results = {};
  for (const lang of ['en', 'ru']) {
    const selectors = Object.fromEntries(['run','label','states','step','reset'].map(k => [`[data-${k}]`, element()]));
    const lamps = [element(), element(), element()];
    for (const lamp of lamps) { lamp.level = element(); lamp.querySelector = () => lamp.level; }
    const demo = {querySelector: s => selectors[s], querySelectorAll: () => lamps};
    const document = {documentElement: {lang}, querySelector: () => demo, createElement: element};
    let callback = null;
    new Function('document', 'setInterval', 'clearInterval', source)(document,
      (fn, ms) => { assert(ms === 1000, 'Wrong interval'); callback = fn; return 1; },
      () => { callback = null; });
    const run = selectors['[data-run]'], step = selectors['[data-step]'], reset = selectors['[data-reset]'];
    function state(expected) {
      const states = selectors['[data-states]'].children;
      assert(states.length === 10, 'State marker count');
      assert(states.filter(e => e.classList.contains('active')).length === 1, 'State marker one-hot');
      assert(states[expected].classList.contains('active'), `Expected S${expected}`);
      const expectedLamp = expected < 4 ? 0 : expected < 6 ? 1 : 2;
      lamps.forEach((lamp,i) => {
        assert(lamp.classList.contains('on') === (i === expectedLamp), 'Lamp color');
        assert(lamp.level.textContent === (i === expectedLamp ? '1' : '0'), 'Accessible lamp value');
      });
      assert(selectors['[data-label]'].textContent.startsWith(lang === 'ru' ? 'Состояние' : 'State'), 'Localized state label');
    }
    state(0);
    const slots = [0,0,0];
    for (let i=0;i<30;i++) {
      const s = i % 10; state(s); slots[s<4 ? 0 : s<6 ? 1 : 2]++; step.click();
    }
    assert(slots.join(',') === '12,6,12', '4/2/4 durations'); state(0);
    run.click(); assert(run.attrs['aria-pressed'] === 'true' && callback, 'Run starts timer');
    for (let i=1;i<=3;i++) { callback(); state(i); }
    run.click(); assert(callback === null && run.attrs['aria-pressed'] === 'false', 'Pause stops timer'); state(3);
    run.click(); step.click(); assert(callback === null, 'Manual step pauses timer'); state(4);
    run.click(); reset.click(); assert(callback === null && run.attrs['aria-pressed'] === 'false', 'Reset stops timer'); state(0);
    results[lang] = 'PASS: 3 full cycles, 4/2/4 lamps, run/pause/step/reset and localized labels';
  }
  new Function('document', source)({querySelector: () => null});
  return results;
}
if (typeof module !== 'undefined' && require.main === module) {
  const fs = require('fs'), path = require('path');
  console.log(JSON.stringify(checkDemo(fs.readFileSync(path.join(__dirname, '../demo.js'), 'utf8')), null, 2));
}
