# OpenCode Clean Code Skills

Five OpenCode agent skills for applying Clean Code principles. Each skill is a
chaptered reference with worked examples, a cheatsheet, a glossary, and a pattern
catalogue. The skill descriptions direct OpenCode to load the language-specific
skill that matches the file being edited.

## Install

OpenCode discovers skills from `.opencode/skills/` in a project or
`~/.config/opencode/skills/` globally. Clone this repository, then copy the skills
into one of those locations:

```sh
mkdir -p .opencode/skills
cp -R skills/* .opencode/skills/
```

Restart OpenCode after installing. The five skills appear in its native `skill`
tool and are loaded only when relevant.

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
NOTICE.md                                 # Sources, licences, and attribution
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
