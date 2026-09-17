# AGENTS.md — codecraft-skills

Canonical instructions for AI agents (and humans) working in this repository.
If anything here conflicts with a passing preference in chat, this file wins.

## What this repo is

Eleven auto-detecting agent skills: two master detectors (`refactor-detect`,
`patterns-detect`) and nine leaf skills covering the complete refactoring
catalog (66 techniques, 6 categories) and the GoF design pattern catalog
(22 patterns, 3 families). Consumers load skills through their `SKILL.md`
frontmatter `description`; nothing else in this repo ships.

## Layout and naming

- Flat layout: one directory per skill at the repo root, exactly one file in
  it: `SKILL.md`.
- Directory names and frontmatter `name` are kebab-case and MUST be
  identical: `<name>/SKILL.md` with `name: <name>`.
- Naming convention: roots are `*-detect`; leaves are `<family>-<scope>`
  (`refactor-<scope>`, `patterns-<family>`).

## SKILL.md schema

```yaml
---
name: <kebab-case, equals directory name>
description: <single paragraph, 150–1000 chars>
---
```

No other frontmatter fields are permitted (downstream loaders may reject
unknown keys). The `description` is the entire auto-selection surface; it must
contain, in this order of importance:

1. **What it detects** — one sentence on the triggering situation (symptom
   phrases matter most; agents match these against user queries).
2. **Full item list** — every technique/pattern the skill covers, comma
   separated. Never truncate: a missing entry makes the router unable to
   select this skill for that item.
3. **"Use when…" clause** — concrete trigger phrasings users actually type
   (quotes help), e.g. *"use when asked to simplify a conditional, flatten
   an if-chain"*.
4. **Scope boundary** — where relevant, what belongs to a sibling skill
   instead (this measurably improves routing on adjacent categories).

Style: plain professional English, no marketing adjectives, no emojis, no
links, no newlines. Keep between 150 and 1000 characters (enforced by
`scripts/check_skills.py`).

## Content standards

### Root (detector) skills

Required sections, in order:

1. Intake protocol — what to gather before routing (code sample, framework,
   error messages, constraints) and what to ask for when missing.
2. Smell/signal detection — a table mapping observable signals to candidate
   items, covering every leaf category.
3. Ordering and tie-breaking — explicit rules for when multiple candidates
   fit (e.g. correctness-preserving first, smallest blast radius first).
4. Routing table — which leaf skill(s) to load per signal group.
5. Safety — what the router must NOT do (apply edits without confirmation,
   fabricate context, route beyond its own set).
6. Output contract — what a routed response should look like.

### Leaf skills

Required structure:

1. One-line scope statement + source credit line (keep the existing
   "Refactoring.Guru set — ..." attribution header verbatim).
2. `## Quick Pick` — a disambiguation table for the items most often confused
   within this category.
3. One `### <Item Name>` section **per catalog item**, each with subsections:
   - **Detect** — smells, code shapes, user phrases.
   - **Preconditions / Avoid** — when applying would be wrong (merge into
     Detect if genuinely N/A).
   - **Apply** — numbered, language-neutral pseudocode steps. No binding to
     one language's idiom unless the step cannot exist without it.
   - **Pitfalls** — at least one concrete failure mode.
4. Item section order follows the Quick-Pick / catalog grouping, not
   alphabetical order.

## Coverage invariants

Closed catalogs; treat counts as invariants, not targets:

| Leaf | Items |
|---|---|
| refactor-methods | 9 |
| refactor-objects | 8 |
| refactor-data | 15 |
| refactor-conditionals | 8 |
| refactor-calls | 14 |
| refactor-generalization | 12 |
| patterns-creational | 5 |
| patterns-structural | 7 |
| patterns-behavioral | 10 |
| **Totals** | **66 refactorings + 22 patterns** |

Rules:

- The per-skill canonical inventory is the set of `###` sections in the leaf
  itself; this table holds only the counts (do not maintain a second copy of
  the item names anywhere).
- Never delete, rename, or reorder a catalog item silently. If an item really
  must change (upstream catalog correction), update the leaf, its description
  item list, this table, and the README counts in the same commit, and say so
  explicitly in the commit message.
- New items outside these two catalogs require maintainer sign-off; they
  change the product's promise of completeness.

## Editing rules

- Make the smallest coherent change that satisfies the request; preserve the
  verified structure (Quick Pick + per-item blocks).
- Detection-first: when improving an item, strengthen **Detect** before
  rewriting Apply. Most routing quality lives in symptoms, not steps.
- Pseudocode stays language-neutral (see content standards).
- Attribution headers and the README "Source & credit" section are
  load-bearing for licensing honesty: never remove them.
- No emojis, no commentary paragraphs describing the edit inside the skill
  text.

## Verification workflow

Always run, in this order:

1. **Structural gate** (must pass, exit 0):
   ```sh
   python3 scripts/check_skills.py
   ```
   Checks: directory/name match, frontmatter validity, description length and
   required markers, Quick-Pick presence, per-leaf item counts against the
   invariants table.
2. **Selection regression** (required whenever a `description` or routing
   table changed; stdlib only):
   ```sh
   cd eval
   python3 build_input.py          # regenerate semantic_input.txt
   # ask any capable agent: given semantic_input.txt + the queries in
   # queries.tsv (column 3 only), emit pred.tsv rows "<query_id>\t<skill-or-NONE>"
   python3 grade_semantic.py pred.tsv
   ```
   Baseline: 55/56 positive strict-primary, 7/7 negatives rejected (full
   detail in the history of `PLAN.md` upstream; the one known miss is the
   relay-layer probe accepted either way as dual-covered). Any new leak on a
   negative query is a hard regression: fix the description before merging.
   Optional lexical floor: `python3 lexsim.py`.
3. **Live spot-check**: load the changed skill in a real agent session and ask
   one in-scope question plus one out-of-domain question; confirm it engages
   on the first and declines/reroutes on the second.

## PR checklist

- [ ] `python3 scripts/check_skills.py` passes.
- [ ] `eval` grading shows no regression versus baseline (if applicable).
- [ ] Description still lists every covered item verbatim.
- [ ] Counts in this file and README match the leaves (if inventory moved).
- [ ] Attribution lines intact.
- [ ] Commit message states intent, no secrets, no generated artifacts.
