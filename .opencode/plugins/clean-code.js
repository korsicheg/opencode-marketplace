/**
 * clean-code gateway plugin for OpenCode v2.
 *
 * Five well-described skills turned out not to be enough on their own: nothing
 * in a session says *when* to load one, so they get read past. This adds a
 * short rule naming the language-to-skill dispatch to every agent request.
 *
 * Gateway only. It deliberately does not register the skills themselves --
 * those install through the `skills` array, and keeping the two separate means
 * installing this cannot change which skills you have.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const GATEWAY_FILE = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../clean-code-gateway.md',
);

// `context` fires before every agent-loop model request, including tool-driven
// continuations. Reading the gateway once keeps disk I/O off that hot path.
const gateway = { loaded: false, text: null };

const readGateway = () => {
  if (gateway.loaded) return gateway.text;
  gateway.loaded = true;

  try {
    gateway.text = fs.readFileSync(GATEWAY_FILE, 'utf8');
  } catch (error) {
    // Reported rather than swallowed: silence here is indistinguishable from
    // the plugin never having loaded. Surfaced via `opencode run --print-logs`.
    console.error(
      `clean-code gateway: could not read ${GATEWAY_FILE} — ${error.message}. ` +
        'Load the matching clean-code skill manually before writing or reviewing code.',
    );
  }

  return gateway.text;
};

const appendGateway = (event) => {
  const text = readGateway();
  if (text) event.system.push({ type: 'text', text });
};

// `Plugin.define` from `@opencode/plugin` is an identity function, so the
// definition is exported bare to keep the plugin free of dependencies.
export default {
  id: 'clean-code',
  async setup(ctx) {
    await ctx.session.hook('context', appendGateway);
  },
};
