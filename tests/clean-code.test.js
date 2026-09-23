// Zero-dependency. Run from the repository root: `node --test`
// Kept out of `.opencode/plugins/`: OpenCode loads every file there as a plugin.
import assert from 'node:assert/strict';
import test from 'node:test';

import plugin from '../.opencode/plugins/clean-code.js';

// Stands in for the host: records each session hook the plugin registers.
const setUp = async () => {
  const hooks = new Map();
  const ctx = { session: { hook: async (name, callback) => hooks.set(name, callback) } };
  await plugin.setup(ctx);
  return hooks;
};

const contextEvent = (system = []) => ({ system, messages: [], tools: {}, options: {} });

test('registers the agent-loop context hook and nothing else', async () => {
  const hooks = await setUp();

  assert.deepEqual([...hooks.keys()], ['context']);
});

test('appends the gateway as a system part', async () => {
  const event = contextEvent();

  (await setUp()).get('context')(event);

  assert.equal(event.system.length, 1);
  assert.equal(event.system[0].type, 'text');
  assert.match(event.system[0].text, /clean-code-typescript/, 'dispatch table present');
});

test('keeps the system parts it was given, in order', async () => {
  const existing = { type: 'text', text: 'You are a coding agent.' };
  const event = contextEvent([existing]);

  (await setUp()).get('context')(event);

  assert.equal(event.system.length, 2);
  assert.equal(event.system[0], existing, 'host instructions stay first');
});

test('leaves messages untouched', async () => {
  const event = contextEvent();
  event.messages.push({ role: 'user', content: 'refactor this' });

  (await setUp()).get('context')(event);

  assert.deepEqual(event.messages, [{ role: 'user', content: 'refactor this' }]);
});
