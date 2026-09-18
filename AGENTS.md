# AGENTS.md — codecraft-skills

Canonical instructions for AI agents (and humans) working in this repository.
If anything here conflicts with a passing preference in chat, this file wins.

## What this repo is

Eleven auto-detecting agent skills: two master detectors (`refactor-detect`,
`patterns-detect`) and nine leaf skills covering the complete refactoring
catalog (66 techniques, 6 categories) and the GoF design pattern catalog
(22 patterns, 3 families). Consumers load skills through their `SKILL.md`
frontmatter `description`; nothing else in this repo ships. The root
`.claude-plugin/` directory holds packaging metadata for Claude Code's plugin
loader (`plugin.json` + `marketplace.json`, cross-checked by the structural
gate); it is consumed only by that loader. Installer state
lives at `~/.config/codecraft/` outside the shipped surface, and `scripts/` +
`eval/` are tooling only — never installed into a skill directory.

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
`scripts/check_skills.py`). The value is a YAML *plain scalar*: it must never
contain `": "` (colon+space) or `" #"` — strict parsers (PyYAML and similar
loaders) reject it with "mapping values are not allowed in this context".
Delimit label lists with an em dash instead (`Triggers — "x", "y"`), and
verify with `python3 scripts/check_skills.py`, which fails on both sequences.

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

## Leading words

Classic software-engineering terms prime agent behavior more reliably than
original phrasing ("leading words"). Use them deliberately, never decoratively.

### Selection side (descriptions, Detect lines)

When a smell has a canonical name, **open** the symptom clause with it — these
phrases are the highest-weight tokens an auto-selector matches against user
queries. Never bury a canonical term mid-list. One per sentence, max; keep
plain English around it.

Curated smell vocabulary (additions require the same care as new items):

| Term | What it names | Routes toward |
|---|---|---|
| feature envy | a method reaches into another object more than its own | `refactor-objects` (Move Method, Hide Delegate) |
| data clumps | variables travel together repeatedly | `refactor-data` (Replace Data Value with Object) |
| shotgun surgery | one change forces many edits across classes | `refactor-objects` (Extract Class, moves) |
| divergent change | one class edited for many unrelated reasons | `refactor-objects` (Extract Class) |
| primitive obsession | raw strings/ints standing in for concepts | `refactor-data` (Replace Type Code with …) |
| magic number | unexplained literal used inline | `refactor-data` (Symbolic Constant) |
| switch proliferation | parallel type-code switches replicated across modules | `refactor-conditionals` (Replace Conditional with Polymorphism) |
| dead weight | locals/parameters unused or needlessly copied | `refactor-methods` (Inline Temp, Split Temporary Variable) |
| ball of mud / god class | sprawling aggregate doing everything | route via `refactor-detect` |

### Execution side (Apply, Pitfalls)

At most **one** discipline phrase per block, and only where it sharpens an
ordering or verification step — it must change what the executing agent does,
not decorate prose.

Curated discipline vocabulary:

| Term | Meaning here |
|---|---|
| golden path | do/harden the highest-frequency variant first, stub the rest |
| tracer bullet | thin end-to-end slice proving integration before widening scope |
| tests pin the seam | snapshot observable behavior before moving it |
| fail explicit | refuse silent defaults; missing config becomes an error |
| strangler fig | wrap and replace incrementally; old path stays green during migration |
| smallest possible diff | no drive-by refactors inside a behavior-preserving move |
| contract-first | freeze the public shape before internals move |

Rules: do not coin new terms; do not stack two leading words in one sentence;
if a term from the bank does not fit, plain English wins.

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
  rewriting Apply. Most routing quality lives in symptoms, not steps — and
  symptom text follows the leading-words doctrine above.
- Pseudocode stays language-neutral (see content standards).
- Attribution headers and the README "Source & credit" section are
  load-bearing for licensing honesty: never remove them.
- No emojis, no commentary paragraphs describing the edit inside the skill
  text.

## Regression capture

A misroute, non-engagement, or force-fit observed in real use becomes a
permanent probe in `eval/queries.tsv` **before** the fix that addresses it
merges — the query verbatim (minimally de-identified when needed), labeled
with the skill that should engage, or `NONE` for out-of-domain. A fix without
its probe is incomplete: the defect it targeted is unguarded. Corpus growth
moves the documented baseline; that is growth, not a regression.

## Verification workflow

Always run, in this order:

1. **Structural and content gates** (must pass, exit 0):
   ```sh
   python3 scripts/check_skills.py
   python3 scripts/security_scan.py
   python3 scripts/leading_word_audit.py
   ```
   The first checks directory/name match, frontmatter validity, description
   length and required markers, Quick-Pick presence, per-leaf item counts
   against the invariants table, router-to-leaf cross-reference integrity,
   the pairwise description-overlap floor, and README badge agreement with
   `eval/BASELINE.md`, and VERSION presence/format. It also
   reports per-skill and total `SKILL.md` byte size (context cost;
   informational — no limit enforced). The second refuses secret-looking
   literals, credential assignments, fetch-piped-into-shell patterns,
   off-whitelist URLs, exfiltration-shaped imperatives, and prompt-injection
   tells anywhere in the tree. The third verifies every curated smell term
   above actually appears in its routed skill.
2. **Selection regression** (required whenever a `description` or routing
   table changed; stdlib only):
    ```sh
    cd eval
    python3 build_input.py          # regenerate semantic_input.txt
    # ask any capable agent: given semantic_input.txt + the queries in
    # queries.tsv (column 5 only), emit pred.tsv rows "<query_id>\t<skill-or-NONE>"
    python3 grade_semantic.py pred.tsv
    ```
    Canonical scores and known-miss provenance live in `eval/BASELINE.md`
    (single source of truth); the current baseline there is 61/63 positive
    under majority vote across three independent closed-book passes, 13/13
    negatives rejected, with per-pass detail in its run-history table. Any new
    leak on a negative query is a hard regression: fix the description before
    merging. Optional lexical floor: `python3 lexsim.py`. Stability across
    repeated passes: `python3 pass_at_k.py pred_a.tsv pred_b.tsv pred_c.tsv`.
    Optional cross-model spot-check (when a second provider/model is
    available): rebuild the same closed-book attachment and run fresh headless
    passes pinned to the foreign model (`opencode run --pure -m
    <provider>/<model>`, neutral working directory, external skill scans
    disabled); save raw answer vectors under `eval/predictions/` and record
    per-pass scores plus agreement-with-consensus in `eval/BASELINE.md`.
    Directional evidence only — never badge material.
3. **Live spot-check (blind, fresh context)**: use a new agent session that
   has not made this change — the editing session cannot review its own
   work. Give it no hint about which skill changed; ask one in-scope question
   targeting the changed area plus one deliberately out-of-domain question;
   confirm the right skill engages on the first and declines or reroutes on
   the second.

## PR checklist

- [ ] `python3 scripts/check_skills.py` passes.
- [ ] `python3 scripts/security_scan.py` and
      `python3 scripts/leading_word_audit.py` pass.
- [ ] Any real-world misroute or non-engagement this change fixes ships with
  its probe in `eval/queries.tsv` (see Regression capture).
- [ ] `eval` grading shows no regression versus baseline (if applicable).
- [ ] Description still lists every covered item verbatim.
- [ ] Counts in this file and README match the leaves (if inventory moved).
- [ ] Attribution lines intact.
- [ ] Commit message states intent, no secrets, no generated artifacts.
