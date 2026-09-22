# OpenCode Clean Code Skills

Five OpenCode agent skills for applying Clean Code principles. Each skill is a
chaptered reference with worked examples, a cheatsheet, a glossary, and a pattern
catalogue. The skill descriptions direct OpenCode to load the language-specific
skill that matches the file being edited.

## Install

Add the hosted skill index to `~/.config/opencode/opencode.json` (or a project's
`.opencode/opencode.json`):

```json
{
  "skills": {
    "urls": ["https://korsicheg.github.io/opencode-marketplace/skills/"]
  }
}
```

Restart OpenCode. The five skills appear in its native `skill` tool and are loaded
only when relevant.

That is the whole install. OpenCode re-reads the index on every start and replaces
any skill whose published version changed, so updates arrive on their own with
nothing to reinstall.

### Installing from a local clone

Use this instead if you want to pin a revision, review changes before they take
effect, work offline, or keep working during a GitHub Pages outage:

```sh
git clone https://github.com/korsicheg/opencode-marketplace.git
```

```json
{
  "skills": {
    "paths": ["/absolute/path/to/opencode-marketplace/skills"]
  }
}
```

Update with `git pull` when you choose to. `skills.paths` and `skills.urls` can
both be set; paths are read straight from disk and never fetched.

> **Outage behaviour.** If `index.json` cannot be fetched, OpenCode registers no
> skills from that URL — it does **not** fall back to its cached copy. A sustained
> outage means the skills disappear until it recovers. The local-clone install is
> immune to this.

### Optional: the gateway plugin

The skills above are loaded by OpenCode when it judges them relevant. In practice
that judgement is the weak link -- a skill can sit listed and unread through a
whole editing session, because nothing says *when* to load one.

The gateway plugin fixes that by injecting a short rule at the start of each
session: a file-extension-to-skill dispatch table, the load-before-you-write
ordering, and a set of rebuttals to the usual reasons for skipping ("it's a
one-line change", "I'm matching the surrounding style"). It is **opt-in and
separate** -- a skill index cannot carry a plugin, so it needs its own line:

```json
{
  "skills": {
    "urls": ["https://korsicheg.github.io/opencode-marketplace/skills/"]
  },
  "plugin": ["clean-code@git+https://github.com/korsicheg/opencode-marketplace.git"]
}
```

Pin a revision by appending a ref: `...opencode-marketplace.git#v1.1.0`.

The plugin injects the rule and nothing else -- it does **not** register skills,
so adding it cannot change which skills you have or how they update. Remove the
`plugin` line to go back to skills alone.

> **Caveat.** Injection uses OpenCode's `experimental.chat.messages.transform`
> hook. The `experimental.` prefix is OpenCode's own: the API may change between
> releases, and the skills install does not depend on it.
>
> **Updating.** Some OpenCode and Bun versions pin a resolved `git+https`
> dependency in a lockfile or cache, so a restart may not pick up a newer commit.
> Clear OpenCode's package cache or reinstall if an update does not appear.

To edit the rule itself, change `.opencode/clean-code-gateway.md` -- the plugin
only reads and wraps it.

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

> **Sources and licensing differ per skill.** The three community adaptations are
> MIT; the book-derived material is independently written restatement with
> citations. Read [`NOTICE.md`](NOTICE.md) before redistributing.

## Layout

```text
marketplace.json                          # Catalog metadata for installer clients
package.json                              # Plugin package manifest (opt-in gateway)
NOTICE.md                                 # Sources, licences, and attribution
scripts/build_index.py                    # Validates skills, generates index.json
site/index.html                           # Landing page served at the Pages root
.github/workflows/publish.yml             # Validate on PRs, publish on main
.opencode/
├── clean-code-gateway.md                 # The injected rule -- edit this
└── plugins/clean-code.js                 # Opt-in gateway plugin (+ .test.js)
skills/
├── clean-code-java/                      # SKILL.md + chapters/ + cheatsheet + glossary + patterns
├── clean-code-typescript/
├── clean-code-javascript/
├── clean-code-python/
└── clean-code-universal/                 # Includes declarative translation reference
```

`marketplace.json` is a lightweight catalog manifest for installer clients. It is
not an OpenCode built-in format: OpenCode currently has no native marketplace
registration command.

## Publishing

`skills/index.json` is **not** committed. It is generated at deploy time from the
contents of `skills/`, which keeps the checked-in tree the single source of truth
and removes any chance of a stale index being merged.

To publish, push to `main`. The workflow validates every skill, regenerates the
index, and deploys to GitHub Pages. To check your work first:

```sh
pip install pyyaml
python scripts/build_index.py --check          # validate, write nothing
python scripts/build_index.py --out _site/skills # build the publishable tree
```

Validation rejects a skill that is missing `SKILL.md`, has unparseable
frontmatter, is missing `name` or `description`, declares a `name` that disagrees
with its directory, uses a directory name that is not lowercase-hyphenated, or
contains a file path OpenCode would refuse to download. All failures are reported
together rather than one at a time.

### How updates reach users

Each skill carries a `version` in the index that is a hash of **that skill's own
files**. OpenCode stores it next to the cached copy as `.opencode-version` and
re-downloads only when the two differ, so editing one skill updates that skill
alone rather than churning all five for every user.

Two consequences worth knowing:

- **`version` is what makes updates work.** OpenCode skips downloading any file
  already present in its cache; the version-triggered refresh is the only code
  path that replaces existing content. Hand-writing an index without a `version`
  would freeze every user at whatever they first downloaded.
- **Nothing is verified beyond the version string.** Downloads are not checksummed
  and the version is self-declared by the host, so the security boundary is
  entirely "who can push to this repository and its Pages origin." Users who want
  to review changes before they take effect should use the local-clone install.

### First-time Pages setup

In the repository settings, under **Pages**, set the source to **GitHub Actions**.
The first push to `main` then publishes to
`https://korsicheg.github.io/opencode-marketplace/`, with the skill index at
`/skills/index.json`.
