'use strict';
// Synthetic pure function calls; do not invoke the installed hook's run().
const assert = require('node:assert/strict');
const path = require('node:path');
const monitor = require(path.join(path.resolve(process.argv[2]), 'scripts/hooks/ecc-context-monitor.js'));
const checks = [];
function check(name, fn) { fn(); checks.push({ name, passed: true }); }
const repeat = count => Array.from({ length: count }, () => ({ tool: 'synthetic-read', hash: 'same' }));
check('four repeats do not warn', () => assert.equal(monitor.detectLoop(repeat(4)).detected, false));
check('five identical calls warn', () => assert.equal(monitor.detectLoop(repeat(5)).detected, true));
check('same tool with different arguments does not warn', () => {
  const mixed = repeat(5).map((entry, i) => ({ ...entry, hash: String(i) }));
  assert.equal(monitor.detectLoop(mixed).detected, false);
});
check('no recent tool data does not warn', () => assert.equal(monitor.detectLoop(null).detected, false));
check('35 percent context triggers warning', () => {
  assert.ok(monitor.evaluateConditions({ context_remaining_pct: 35 }).some(w => w.type === 'context' && w.severity === 2));
});
check('25 percent context triggers critical warning', () => {
  assert.ok(monitor.evaluateConditions({ context_remaining_pct: 25 }).some(w => w.type === 'context' && w.severity === 3));
});
check('disabling API cost estimates preserves loop detection', () => {
  const warnings = monitor.evaluateConditions({ total_cost_usd: 100, recent_tools: repeat(5) }, { costWarnings: false });
  assert.ok(warnings.some(w => w.type === 'loop'));
  assert.ok(!warnings.some(w => w.type === 'cost'));
});
process.stdout.write(JSON.stringify({ status: 'passed', checks,
  boundary: 'Synthetic pure-function thresholds only; no live tool-event bridge, hook installation, automatic recovery or Codex integration.' }) + '\n');
