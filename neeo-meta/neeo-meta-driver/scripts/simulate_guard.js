#!/usr/bin/env node
// Simulates meta's evalwrite/evaldo logic for a driver with listeners and counts __INITIALISE / __CLEANUP calls.
// Usage: node simulate_guard.js DRIVER.json
// Commands are not executed: every command "answers" ok (buttons: "ok", action feeders: '["ok"]').
// Expected for a correct ListenerOn guard:
//   - the first gesture of a session (any visible button, slider, switch or directory action) starts the listeners once;
//   - repeated gestures and POWER OFF / POWER ON cycles (sent by the Brain at each recipe change) never start them again;
//   - with an mqtt listener, __CLEANUP is never called.
'use strict';
const fs = require('fs');

const file = process.argv[2];
if (!file) { console.log('usage: node simulate_guard.js DRIVER.json'); process.exit(2); }
const root = JSON.parse(fs.readFileSync(file, 'utf8'));
const d = root.template || root;
const buttons = d.buttons || {};
const listeners = d.listeners || {};
const hasMqtt = Object.values(listeners).some(function (l) { return l && l.type === 'mqtt'; });
let bad = 0;
let evalErrors = 0;
function check(label, ok, extra) { console.log((ok ? 'OK    ' : 'FAIL  ') + label + (extra ? '  ' + extra : '')); if (!ok) bad++; }

if (!Object.keys(listeners).length) { console.log('No listeners in this driver: nothing to simulate.'); process.exit(0); }

function initialVars() {
  const v = {};
  for (const src of [root.persistedvariables, root.variables, d.persistedvariables, d.variables]) {
    for (const k of Object.keys(src || {})) {
      const x = src[k];
      v[k] = (typeof x === 'string' && x.indexOf('DYNAMIK_INST_START') >= 0) ? 'x' : x;
    }
  }
  return v;
}

function session() {
  const v = initialVars();
  const n = { init: 0, cleanup: 0 };
  const esc = function (s) { return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/[\r\n]/g, ''); };
  const sub = function (s) {
    return String(s).replace(/\$([A-Za-z][A-Za-z0-9]*)/g, function (m, k) {
      if (!(k in v)) return m;
      if (k === 'Result') return esc(v[k]);
      return typeof v[k] === 'string' ? v[k] : JSON.stringify(v[k]);
    });
  };
  const ev = function (x) {
    if (typeof x !== 'string') return x;
    if (!x.startsWith('DYNAMIK ')) return sub(x);
    try { return eval(sub(x.slice(8))); } catch (e) { evalErrors++; return undefined; }   // eslint-disable-line no-eval
  };
  let depth = 0;
  function run(def, result) {
    v.Result = result;
    for (const w of def.evalwrite || []) v[w.variable] = ev(w.value);
    for (const e of def.evaldo || []) {
      const target = ev(e.test) ? e.then : e.or;
      if (target) press(target);
    }
  }
  function press(name) {
    if (name === '__INITIALISE') { n.init++; return; }
    if (name === '__CLEANUP') { n.cleanup++; return; }
    if (name === '__PERSIST' || name === '__WRAPUP') return;
    const b = buttons[name];
    if (!b) return;
    if (++depth > 200) { depth--; return; }   // runaway evaldo loop guard
    run(b, 'ok');
    depth--;
  }
  return { n: n, press: press, run: run };
}

const gestures = [];
for (const k of Object.keys(buttons)) if (!k.startsWith('__')) gestures.push({ label: 'button ' + k, go: function (s) { s.press(k); } });
for (const k of Object.keys(d.sliders || {})) gestures.push({ label: 'slider ' + k, go: function (s) { s.run(d.sliders[k], '50'); } });
for (const k of Object.keys(d.switches || {})) gestures.push({ label: 'switch ' + k, go: function (s) { s.run(d.switches[k], 'true'); } });
for (const dn of Object.keys(d.directories || {})) {
  const feeders = (d.directories[dn] || {}).feeders || {};
  for (const fn of Object.keys(feeders)) {
    (feeders[fn].commandset || []).forEach(function (c, i) {
      if (!Object.keys(c).some(function (k) { return k.startsWith('item'); })) {
        gestures.push({ label: 'action ' + dn + '/' + fn + '[' + i + ']', go: function (s) { s.run(c, '["ok"]'); } });
      }
    });
  }
}

// 1. each gesture, as the first one of a fresh session (e.g. right after a meta restart, recipe already on)
const silent = gestures.filter(function (g) { const s = session(); g.go(s); return s.n.init !== 1; });
check('each visible control starts the listeners when it is the first gesture of a session', silent.length === 0,
  silent.length ? silent.length + ' do not: ' + silent.map(function (g) { return g.label; }).slice(0, 10).join(', ') : '');

// 2. a whole session of gestures
let s = session();
for (let r = 0; r < 3; r++) gestures.forEach(function (g) { g.go(s); });
check('3 rounds of every gesture: listeners started once', s.n.init === 1, 'starts=' + s.n.init);

// 3. recipe changes: the Brain sends POWER OFF then POWER ON, then the user presses keys
s = session();
gestures.slice(0, 1).forEach(function (g) { g.go(s); });
for (let i = 0; i < 30; i++) { s.press('POWER OFF'); s.press('POWER ON'); gestures.forEach(function (g) { g.go(s); }); }
check('30 POWER OFF / POWER ON cycles: listeners still started once', s.n.init === 1, 'starts=' + s.n.init);
if (hasMqtt) check('mqtt listener: __CLEANUP never called', s.n.cleanup === 0, 'cleanups=' + s.n.cleanup);

if (evalErrors) console.log('note: ' + evalErrors + ' DYNAMIK expression(s) threw with the dummy "ok" results (normal for JSON.parse of real data)');
console.log(bad === 0 ? 'Guard OK.' : bad + ' failure(s)');
process.exit(bad ? 1 : 0);
