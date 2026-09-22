# Clean Code skills changelog

Version history for the OpenCode marketplace package and its five skills.

Format follows [Keep a Changelog](https://keepachangelog.com/); newest first. Semver on the
package: **major** = removed/renamed skill or breaking routing change, **minor** = new skill
or capability, **patch** = content fix or doc change with no new surface.

Sources and licensing for the shipped content are recorded in [NOTICE.md](NOTICE.md).

## [1.1.0] — 2026-09-22

### Added

- **An opt-in gateway plugin** (`.opencode/`), so the family gets loaded rather than merely
  being available. Five well-described skills were not enough on their own: OpenCode loads a
  skill when it judges it relevant, and that judgement is the weak link — a skill sits listed
  and unread through a whole editing session, because nothing says *when* to load one. The
  plugin injects a short rule at the start of each session: a file-extension-to-skill
  dispatch table, the load-before-you-write ordering, and rebuttals to the usual reasons for
  skipping it ("it's a one-line change", "I'm matching the surrounding style", "I'm
  reviewing, not writing").
  - `.opencode/clean-code-gateway.md` — the rule, 367 words. **Edit this to change
    behaviour;** the plugin only reads and wraps it.
  - `.opencode/plugins/clean-code.js` — injects via `experimental.chat.messages.transform`,
    into the first *user* message rather than a system one (OpenCode repeats system messages
    every turn and several models break on more than one). Carries a marker-based
    double-injection guard, and caches the rule at module level because the hook fires on
    every agent **step**, not every turn.
  - `.opencode/plugins/clean-code.test.js` — five tests, zero dependencies:
    `node --test .opencode/plugins/clean-code.test.js`.
  - `package.json` — the plugin package manifest, `main` pointing at the plugin.

### Notes

- **The skills are untouched, and so is their install.** A skill index cannot carry a
  plugin, so the gateway needs its own `plugin` line in `opencode.json` alongside the
  existing `skills.urls`. The Pages index, the per-skill version hashes and the documented
  outage behaviour are all unchanged; no skill's version hash moves, so no user re-downloads
  anything. Removing the `plugin` line returns you to skills alone.
- **The plugin is gateway-only by design.** Unlike the `superpowers` plugin it is modelled
  on, it does **not** push onto `config.skills.paths` — installing it therefore cannot change
  which skills you have or how they update. One job, one reason to change.
- **`experimental.chat.messages.transform` is experimental**, and the prefix is OpenCode's
  own. The API may shift between releases. The skills install does not depend on it.
- **Failure is reported, not swallowed.** An unreadable gateway logs once to stderr — visible
  via `opencode run --print-logs` — naming the path and the underlying error, then no-ops;
  silence would be indistinguishable from the plugin not having loaded. The once-only
  logging matters because the hook runs on every agent step.
- **Not wired into CI.** The publish workflow triggers on `skills/**`, `scripts/` and
  `site/**`, so nothing here rebuilds the Pages index — correct, since no skill changed, but
  it also means the tests are not run by the workflow. Note that Node's test runner skips
  hidden directories, so `.opencode/` cannot be passed as a glob target; the file must be
  named.

## [1.0.0] — 2026-09-21

First release. Five skills, 82 files, ~16k lines.

### Added

- **`clean-code-java`** — the original book (Java examples): naming, functions, comments,
  formatting, error handling, classes/SRP, unit tests/TDD, systems, concurrency, the
  refactoring case studies, and the 66-item smells-and-heuristics catalogue.
- **`clean-code-typescript`** — the labs42io adaptation: SOLID in TS, `type` vs `interface`,
  `readonly`/`as const` immutability, unions over `instanceof`, `Failable` result types,
  async/await and `Promise.all`, ESLint/Prettier.
- **`clean-code-javascript`** — the Ryan McDermott adaptation: argument counts and flag
  parameters, side effects and argument mutation, polymorphism over conditionals, closure
  privacy, ES6 classes and chaining, SOLID in an untyped language, callbacks → promises →
  async/await.
- **`clean-code-python`** — the zedr adaptation: type hints over type-prefixes, named regex
  groups, the two-argument limit with dataclass/NamedTuple/TypedDict parameter objects,
  generators, SOLID through ABCs and mixins, mypy-enforced LSP, duck-typed dependency
  inversion, DRY with the bad-abstraction caveat.
- **`clean-code-universal`** — the family's shared core, and the reason the set is published
  together. A language-agnostic distillation of the book cross-checked against the three
  adaptations above, organised on a **three-tier spine**: Tier 1 rules assume only that you
  can name something and run some verification; Tier 2 rules bind where a specific construct
  exists (parameter list, type system, substitutability mechanism, exception, test runner,
  thread, branching construct); Tier 3 is language-specific idiom, out of scope by name.
  Covers the languages with no dedicated sibling — Go, Rust, C#, C++, Kotlin, Ruby, PHP,
  Swift, Scala — and the declarative languages the book never addresses: YAML (Kubernetes,
  Helm, CI pipelines), Terraform/HCL, SQL, Bash, Dockerfile. Ships
  `references/declarative-translation.md`, a 53-row table stating per rule what it means
  where there are no functions, no classes and no unit tests, including the rules that
  genuinely **do not apply**.
- **Reciprocal routing across all five.** Every description names its siblings and ends by
  routing anything else to `clean-code-universal`, so the model loads one skill rather than
  guessing between five. Measured before release: universal fires on 45/45 prompts no
  sibling covers and 0/55 sibling-owned or oblique ones.
- **`NOTICE.md`** — per-skill sources and licences. The three community adaptations are MIT
  (notices reproduced verbatim); the book-derived material is not open source and is
  distributed as independently written restatement with citations.
