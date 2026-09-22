/**
 * clean-code gateway plugin for OpenCode.
 *
 * Five well-described skills turned out not to be enough on their own: nothing
 * in a session says *when* to load one, so they get read past. This injects a
 * short rule naming the language-to-skill dispatch before any code is written.
 *
 * Gateway only. It deliberately does not register the skills themselves --
 * those install through `skills.urls` or `skills.paths`, and keeping the two
 * separate means installing this cannot change which skills you have.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const GATEWAY_FILE = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../clean-code-gateway.md',
);

// Present in every injected payload, so it doubles as the marker that says
// "already injected" on a message array passed through the hook twice.
const INJECTION_MARKER = 'EXTREMELY_IMPORTANT';

// The transform hook fires on every agent step, not every turn, because
// OpenCode reloads messages from the database each step. Reading and wrapping
// the gateway once keeps that off the hot path.
const gateway = { loaded: false, text: null };

const readGateway = () => {
  if (gateway.loaded) return gateway.text;
  gateway.loaded = true;

  try {
    const rule = fs.readFileSync(GATEWAY_FILE, 'utf8');
    gateway.text = `<${INJECTION_MARKER}>\n${rule}\n</${INJECTION_MARKER}>`;
  } catch (error) {
    // Reported rather than swallowed: silence here is indistinguishable from
    // the plugin never having loaded. Surfaced via `opencode run --print-logs`.
    console.error(
      `clean-code gateway: could not read ${GATEWAY_FILE} — ${error.message}. ` +
        'Load the matching clean-code skill manually before writing or reviewing code.',
    );
    gateway.text = null;
  }

  return gateway.text;
};

const firstUserMessage = (messages) =>
  messages.find((message) => message.info.role === 'user');

const alreadyInjected = (message) =>
  message.parts.some(
    (part) => part.type === 'text' && part.text.includes(INJECTION_MARKER),
  );

export const CleanCodeGatewayPlugin = async () => ({
  // Injected as a user message rather than a system one: OpenCode repeats
  // system messages every turn, and several models break on more than one.
  'experimental.chat.messages.transform': async (_input, output) => {
    const text = readGateway();
    if (!text) return;

    const target = firstUserMessage(output.messages ?? []);
    if (!target || !target.parts.length || alreadyInjected(target)) return;

    // Mutating `output` is this hook's contract -- it is how the transform
    // returns its result.
    target.parts.unshift({ ...target.parts[0], type: 'text', text });
  },
});
