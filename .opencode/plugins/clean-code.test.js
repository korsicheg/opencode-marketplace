// Zero-dependency. Run: `node --test .opencode/plugins/clean-code.test.js`
// Node's test runner skips hidden directories, so the containing dir cannot be
// passed as a glob target -- name the file.
import assert from 'node:assert/strict';
import test from 'node:test';

import { CleanCodeGatewayPlugin } from './clean-code.js';

const MARKER = 'EXTREMELY_IMPORTANT';

const transformOf = async () => {
  const plugin = await CleanCodeGatewayPlugin({});
  return plugin['experimental.chat.messages.transform'];
};

const userMessage = (text) => ({
  info: { role: 'user' },
  parts: [{ type: 'text', text }],
});

const textParts = (message) =>
  message.parts.filter((part) => part.type === 'text').map((part) => part.text);

test('prepends the gateway to the first user message', async () => {
  const output = { messages: [userMessage('refactor this')] };

  await (await transformOf())({}, output);

  const parts = textParts(output.messages[0]);
  assert.equal(parts.length, 2, 'one part added');
  assert.match(parts[0], new RegExp(MARKER), 'gateway is first');
  assert.match(parts[0], /clean-code-typescript/, 'dispatch table present');
  assert.equal(parts[1], 'refactor this', 'original text untouched');
});

test('does not inject twice when the same array is passed through again', async () => {
  const transform = await transformOf();
  const output = { messages: [userMessage('refactor this')] };

  await transform({}, output);
  await transform({}, output);

  assert.equal(textParts(output.messages[0]).length, 2, 'still only one added');
});

test('targets the user message, not a leading assistant message', async () => {
  const output = {
    messages: [
      { info: { role: 'assistant' }, parts: [{ type: 'text', text: 'hi' }] },
      userMessage('refactor this'),
    ],
  };

  await (await transformOf())({}, output);

  assert.equal(textParts(output.messages[0]).length, 1, 'assistant untouched');
  assert.equal(textParts(output.messages[1]).length, 2, 'user got the gateway');
});

test('is a no-op on an empty or user-less conversation', async () => {
  const transform = await transformOf();

  const empty = { messages: [] };
  await transform({}, empty);
  assert.deepEqual(empty.messages, []);

  const assistantOnly = {
    messages: [{ info: { role: 'assistant' }, parts: [{ type: 'text', text: 'hi' }] }],
  };
  await transform({}, assistantOnly);
  assert.equal(textParts(assistantOnly.messages[0]).length, 1);
});

test('preserves the reference part shape it clones', async () => {
  const output = { messages: [userMessage('refactor this')] };
  output.messages[0].parts[0].id = 'part-123';

  await (await transformOf())({}, output);

  assert.equal(output.messages[0].parts[0].id, 'part-123', 'shape carried over');
});
