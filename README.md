# OpenCode Clean Code Skills

Five OpenCode agent skills for applying Clean Code principles. Each skill is a
chaptered reference with worked examples, a cheatsheet, a glossary, and a pattern
catalogue. The skill descriptions direct OpenCode to load the language-specific
skill that matches the file being edited.

Requires **OpenCode v2**. v1 is not supported: its `skills` configuration and
plugin API both differ.

## Install

Add this to `~/.config/opencode/opencode.json` (or a project's
`.opencode/opencode.json`):

```json
{
  "references": {
    "clean-code": {
      "repository": "https://github.com/korsicheg/opencode-marketplace.git",
      "branch": "main",
      "hidden": true
    }
  },
  "skills": ["~/.local/share/opencode/repos/github.com/korsicheg/opencode-marketplace@main/skills"]
}
```

The `references` entry makes OpenCode clone this repository and keep it current;
the `skills` entry loads the five skills from that checkout. `hidden` keeps the
repository itself out of the model's list of references, so only the skills are
used.

- **First start.** The clone runs in the background, so the skills appear from the
  next session onward.
- **Updates.** OpenCode refreshes the checkout at most once a day -- a fetch and a
  hard reset to `main` -- when references load and after each prompt. There is
  nothing to reinstall.
- **Private hosts.** The clone uses your existing Git credentials, so any
  repository you can `git clone` non-interactively works. Credentials written into
  the `repository` URL are stripped, so store them in a Git credential helper
  instead.

> **The checkout path is OpenCode's internal layout, not a documented contract.**
> It is `<repos>/<host>/<owner>/<repo>@<branch>`, where `<repos>` is the `repos`
> line of `opencode debug paths`. If the skills disappear after an OpenCode
> upgrade, check that directory and update the `skills` entry to match.

### Installing from a local clone

Use this instead if you want to pin a revision or review changes before they take
effect:

```sh
git clone https://github.com/korsicheg/opencode-marketplace.git
```

```json
{
  "skills": ["/absolute/path/to/opencode-marketplace/skills"]
}
```

Update with `git pull` when you choose to.

### Optional: the gateway plugin

The skills above are loaded by OpenCode when it judges them relevant. In practice
that judgement is the weak link -- a skill can sit listed and unread through a
whole editing session, because nothing says *when* to load one.

The gateway plugin fixes that by adding a short rule to the system instructions of
every agent request: a file-extension-to-skill dispatch table, the
load-before-you-write ordering, and a set of rebuttals to the usual reasons for
skipping ("it's a one-line change", "I'm matching the surrounding style"). It is
**opt-in and separate**, so it needs its own line:

```json
{
  "plugins": ["github:korsicheg/opencode-marketplace"]
}
```

Pin a revision by appending a tag or commit: `github:korsicheg/opencode-marketplace#<ref>`.
An unpinned plugin is checked for updates at startup but not upgraded in place;
run `opencode plugin update` to apply one.

The plugin adds the rule and nothing else -- it does **not** register skills, so
adding it cannot change which skills you have or how they update. Remove the
`plugins` entry to go back to skills alone.

To edit the rule itself, change `.opencode/clean-code-gateway.md` -- the plugin
only reads and appends it.

## Skills

- **`clean-code-java`**: The original book (Java examples): naming, functions,
  comments, formatting, error handling, classes/SRP, unit tests/TDD, systems,
  concurrency, refactoring case studies, and the 66-item smells-and-heuristics
  catalogue.
- **`clean-code-typescript`**: The labs42io adaptation: SOLID in TypeScript,
  `type` versus `interface`, `readonly` and `as const` immutability, unions over
  `instanceof`, Failable result types, async/await, ESLint, and Prettier.
- **`clean-code-javascript`**: The Ryan McDermott adaptation: argument counts and
  flag parameters, side effects and argument mutation, polymorphism over
  conditionals, closure privacy, SOLID in an untyped language, and async code.
- **`clean-code-python`**: The zedr adaptation: type hints over type-prefixes, the
  two-argument limit with dataclass/NamedTuple/TypedDict parameter objects,
  generators, SOLID through ABCs and mixins, mypy-enforced LSP, and duck-typed
  dependency inversion.
- **`clean-code-universal`**: Language-agnostic guidance for Go, Rust, C#, C++,
  Kotlin, Ruby, PHP, Swift, Scala, YAML, Terraform/HCL, SQL, Bash, and Dockerfiles.
  It distinguishes principles that apply everywhere from those requiring specific
  language constructs.

Each skill is also available as a slash command, such as `/clean-code-python`.

> **Sources and licensing differ per skill.** The three community adaptations are
> MIT; the book-derived material is independently written restatement with
> citations. Read [`NOTICE.md`](NOTICE.md) before redistributing.

## Layout

```text
package.json                              # Plugin package manifest (opt-in gateway)
NOTICE.md                                 # Sources, licences, and attribution
scripts/validate_skills.py                # Checks every skill loads as intended
tests/clean-code.test.js                  # Gateway plugin tests
.github/workflows/validate.yml            # Runs both checks on pushes and PRs
.opencode/
├── clean-code-gateway.md                 # The injected rule -- edit this
└── plugins/clean-code.js                 # Opt-in gateway plugin
skills/
├── clean-code-java/                      # SKILL.md + chapters/ + cheatsheet + glossary + patterns
├── clean-code-typescript/
├── clean-code-javascript/
├── clean-code-python/
└── clean-code-universal/                 # Includes declarative translation reference
```

## Changing a skill

Whatever lands on `main` reaches every user within a day, so check it first:

```sh
pip install pyyaml
python scripts/validate_skills.py   # every skill loads under the id and description you expect
node --test                         # the gateway plugin
```

Validation rejects a skill whose directory name is not a lowercase-hyphenated id of
at most 64 characters, that is missing `SKILL.md`, has missing or unparseable
frontmatter, declares a `name` that disagrees with its directory, or has no
`description` -- without one, OpenCode never offers the skill to the model. All
failures are reported together rather than one at a time. The workflow runs both
checks on every pull request and every push to `main`.

Nothing is verified beyond Git itself: the security boundary is "who can push to
`main`". Users who want to review changes before they take effect should use the
local-clone install.
