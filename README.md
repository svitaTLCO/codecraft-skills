# CodeCraft Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Your agent should not need a lecture before it knows when to **Extract Method**
or when a billing engine deserves a **State** object. CodeCraft Skills hands
it two complete catalogs — **66 refactorings** and **22 design patterns** — as
auto-detecting agent skills: it reads the symptoms, picks the technique, and
applies it with the pitfalls already known.

```
you      this function computes tax, discounts and formatting — all inline
agent    refactor-methods ▸ Extract Method: split along the responsibility
         seams; keep the original as a delegating shell; pitfall: don't
         extract across a side-effect boundary
```

## What you get

| Set | Skills | Catalog |
|---|---|---|
| Refactorings (`refactor-*`) | 7 — master detector + 6 category leaves | 66 techniques, every category of the refactoring.guru guide |
| Design Patterns (`patterns-*`) | 4 — master detector + 3 family leaves | 22 GoF patterns, all three families |

Each skill is one `SKILL.md`: YAML frontmatter plus body. No runtime, no
dependencies, works with anything that loads Markdown skills
(opencode, Claude Code style layouts, or your own loader).

## How detection works

Every set has a **root detector** for the vague requests — *"this file feels
like a ball of mud"*, *"is there a pattern hiding in here?"* — that collects
smell signals, breaks ties by explicit rules, and routes to the right leaf.
Leaves carry the substance: a **Quick Pick** table for the items people
confuse most, then per item — **Detect** (what it looks like), **Preconditions**
(when *not* to apply), **Apply** (language-neutral steps), **Pitfalls**.

It runs on plain language, because that's what developers actually type:

| You say | What engages |
|---|---|
| *"our checkout module feels like a ball of mud, tell me what to fix first"* | `refactor-detect` — an ordered, signal-ranked plan |
| *"split calculateTotal: it computes tax, applies discounts and formats output, all inline"* | `refactor-methods` → **Extract Method** |
| *"BillingService has forty fields and knows how to email, invoice and store - break it up"* | `refactor-objects` → **Extract Class** |
| *"legacy SDK is callbacks; I want a promise-based wrapper over it without touching the vendor lib"* | `patterns-structural` |
| *"shipping cost policy differs per carrier and must be chosen per order at dispatch time"* | `patterns-behavioral` → **Strategy** territory |
| *"deploy this Flask app to Azure App Service"* | nothing — out of domain, correctly declined |

Rows above are verbatim samples from the evaluation corpus in [`eval/`](eval).

## Evidence

Selection behavior was benchmarked against a 63-query corpus (52 leaf
probes, 4 root/meta probes, 7 deliberately out-of-domain):

- **55/56** strict-primary routing hits (the single miss is a probe two
  skills legitimately co-cover)
- **7/7** out-of-domain queries rejected instead of force-fitted

Reproduce it yourself — stdlib only, see `AGENTS.md` → Verification workflow:

```sh
python3 scripts/check_skills.py   # structural gate: schema, counts, invariants
```

## Install

```sh
git clone https://github.com/svitaTLCO/codecraft-skills
cd codecraft-skills

# opencode
cp -R <skill-dir> ~/.agents/skills/        # or symlink while iterating

# Claude Code layout
cp -R <skill-dir> ~/.claude/skills/
```

Install all eleven or cherry-pick a leaf — they compose and each description
carries its own scope boundary, so wrong-skill pickup stays unlikely.

## Source & credit

Catalog names, classifications, and family structure follow
[refactoring.guru](https://refactoring.guru/) (© Alexander Shvets). Every
explanation, heuristic, and example here is written from scratch — nothing is
copied from the site.

## Contributing

Read [`AGENTS.md`](AGENTS.md) — it is the canonical contract for human *and*
AI agents: skill schema, coverage invariants, verification workflow.
[`CONTRIBUTING.md`](CONTRIBUTING.md) is the short version. Detection-quality
fixes, pitfall corrections, and new corpus rows especially welcome.

## License

[MIT](LICENSE)
