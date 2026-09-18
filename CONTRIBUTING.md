# Contributing

Thank you! This repo ships eleven auto-detecting agent skills (66
refactorings + 22 design patterns). Contributions are welcome: detection
heuristic fixes, pitfall corrections, pseudocode clarity, evaluation corpus
growth, and packaging/docs improvements.

## Requirements

- Git
- Python 3.8+ (standard library only — no installs for tooling)
- An agent runtime that loads Markdown skills (optional, for live testing)

## Quickstart

```sh
git clone https://github.com/svitaTLCO/codecraft-skills
cd codecraft-skills
# make your change ...
python3 scripts/check_skills.py         # structural gate — must pass
python3 scripts/security_scan.py        # content security — must pass
python3 scripts/leading_word_audit.py   # curated terms land where they route
cd eval && python3 build_input.py       # if you touched a description/routing table
# see AGENTS.md "Verification workflow" for the selection-regression steps
```

## Testing with a live agent

In a fresh agent session that did not make the change (a session cannot
review its own edits), load the changed skill, then:

1. Ask an in-scope question and confirm the skill engages.
2. Ask an out-of-domain question and confirm it declines or reroutes.
3. For routing changes, run the `eval/` semantic grading and compare against
   the documented baseline (`eval/BASELINE.md` is the single source of truth;
   any new negative leak is a hard regression).

## What gets accepted

- Fixing wrong/misleading detection symptoms, preconditions, or pitfalls.
- Improving pseudocode without changing observable behavior.
- Strengthening `description` fields for better auto-selection (always keep
  the full item list verbatim).
- New queries for `eval/queries.tsv` (label them honestly: skill name, or
  `NONE` for out-of-domain).
- Regression probes captured from real failures: any misroute or
  non-engagement you hit must land as a `queries.tsv` row before the fix
  (AGENTS.md "Regression capture").

Out of scope without maintainer sign-off: adding items outside the two
closed catalogs, renaming/removing catalog items, third-party dependencies,
packaging for other ecosystems.

The canonical rules live in [`AGENTS.md`](AGENTS.md) — read it first.
