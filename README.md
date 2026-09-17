# CodeCraft Skills

Give your agent the craft. Auto-detecting agent skills that cover the complete
refactoring catalog (66 techniques) and the classic design pattern catalog
(22 GoF patterns). Drop them into any agent that loads Markdown skills and it
can detect which refactoring or pattern applies from plain-language symptoms —
no lookups, no prompting tricks.

## What's inside

Two coordinated sets. Each set starts at a master detector that handles vague,
global requests and routes to specialized leaf skills.

### Set A — Refactorings (`refactor-*`)

Catalog source: the refactoring.guru "Refactoring" guide (Alexander Shvets).
All prose, detection heuristics, and pseudocode below are original to this
project.

| Skill | Scope | Techniques |
|---|---|---|
| `refactor-detect` | Master detector & router | routes global/meta requests |
| `refactor-methods` | Improving method structure | 9 |
| `refactor-objects` | Moving and manipulating object-level units | 8 |
| `refactor-data` | Data structures, variables, arrays, records | 15 |
| `refactor-conditionals` | Conditional logic, guards, polymorphic switches | 8 |
| `refactor-calls` | Method calls, parameters, API shape | 14 |
| `refactor-generalization` | Inheritance, templates, generics, hierarchies | 12 |

Total: **66 refactorings**.

### Set B — Design Patterns (`patterns-*`)

Catalog source: the refactoring.guru "Design Patterns" guide.

| Skill | Family | Patterns |
|---|---|---|
| `patterns-detect` | Master detector & router | routes global/meta requests |
| `patterns-creational` | Creational | 5 |
| `patterns-structural` | Structural | 7 |
| `patterns-behavioral` | Behavioral | 10 |

Total: **22 design patterns**.

## How it works

- A **root skill** in each set answers broad questions ("refactor this file",
  "is there a pattern that fits this code?"). It collects smell signals from
  the code or conversation, resolves ordering and ties, and routes to one or
  more leaf skills.
- A **leaf skill** owns its category: a Quick-Pick disambiguation table plus a
  per-item block — Detect (smells/symptoms), Preconditions/Avoid, Apply
  (language-neutral pseudocode), Pitfalls.
- Selection behavior was validated against a 63-query corpus (see `eval/`):
  semantic routing hits the labeled target skill on 55/56 in-scope queries and
  correctly rejects all 7 out-of-domain queries.

## Install

Copy or symlink the skill directories into your agent's skills location. Every
directory contains a single `SKILL.md` with YAML frontmatter (`name`,
`description`) — the same contract other skills ecosystems use.

```sh
# example: opencode
cp -R ./<skill-dir> ~/.agents/skills/

# example: Claude Code layout
cp -R ./<skill-dir> ~/.claude/skills/
```

Symlinking is handy while iterating locally:

```sh
ln -s "$PWD/refactor-detect" ~/.agents/skills/refactor-detect
```

## Source & credit

Catalog names, classifications, and family structure follow
[refactoring.guru](https://refactoring.guru/) (copyright Alexander Shvets).
Every explanation, heuristic, and example in this repository is written from
scratch and is not copied from the site.

## Contributing

- [`AGENTS.md`](AGENTS.md) — canonical instructions for AI agents (and
  humans) editing this repository: skill schema, content standards, coverage
  invariants, verification workflow.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — short human quickstart.
- `scripts/check_skills.py` — structural gate (stdlib-only Python).
- `eval/` — selection-quality corpus and graders.

## License

MIT — see [LICENSE](LICENSE).
