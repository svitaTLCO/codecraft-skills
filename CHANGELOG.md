# Changelog

Version format is semver. Catalog inventory moves (items added, renamed, or
removed) always bump the minor version and state the delta here.

## [Unreleased]

### Verified

- Claude Code plugin channel public-URL flow validated end-to-end (issue #1
  acceptance criteria 1–3, on Claude Code 2.1.266): `marketplace add
  https://github.com/svitaTLCO/codecraft-skills` clones and validates the
  repo, install completes, `details` lists exactly 11 skills with zero extra
  components, and a fresh headless session engaged `refactor-methods` for an
  in-scope restructuring request while declining an out-of-domain deploy
  request without loading any catalog content. The remaining items (second
  CLI version, older-client degradation note) stay tracked in issue #1.

## [1.2.0] - 2026-09-18

### Added

- Claude Code plugin channel: root `.claude-plugin/` manifests (`plugin.json`
  + `marketplace.json`), validated end-to-end on Claude Code 2.1.266 via local
  path (`marketplace add` → `install` → `details`: 11 skills discovered, zero
  extra runtime components). The structural gate now cross-checks the manifests
  against the catalog directories and `VERSION`; README quick-start documents
  the loader flow plus the one-channel-per-machine precedence note. Public
  URL-flow validation across client versions is tracked in a GitHub issue.
- Cross-model spot-check evidence (`eval/predictions/pred_{g,h,i}.tsv`,
  recorded in `eval/BASELINE.md`): headless passes pinned to a different model
  family (DeepSeek-V4-Flash) scored 63/63 strict-primary with 13/13 negative
  rejections and zero leaks on the identical closed-book corpus. The three
  captures were byte-identical, so they are recorded as one effective answer
  vector (directional evidence, never badge material); the AGENTS.md
  verification workflow now documents the spot-check protocol.

### Changed

- Eval corpus label corrections (no shipped-text change; existing closed-book
  passes re-scored rather than regenerated): `x2` primary label corrected from
  `refactor-data` to `refactor-conditionals` (five of six historical votes and
  the query's dominant Replace-Conditional-with-Polymorphism semantics), and
  `g3` marked as a dual-cover ambiguity with rival leaf `refactor-objects`
  added to its secondary column. Canonical majority-vote baseline moves
  60/63 → 61/63; residual misses reduce to {g3, w1}.
- `scripts/security_scan.py` allowlist extended for the official Anthropic
  plugin `$schema` URI (metadata reference only, nothing executable).

## [1.1.0] - 2026-09-18

### Added

- Baseline single source of truth in `eval/BASELINE.md` (canonical scores,
  known-miss provenance, run history); the structural gate verifies README
  badge values against it, and every doc/grader that duplicated the numbers
  now points at it instead.
- Structural-gate checks: router→leaf routing cross-reference integrity,
  pairwise description-overlap floor (Jaccard-4 shingles), per-item depth
  scorecard (informational only), and `VERSION` presence/format.
- `scripts/security_scan.py`: content-security scan of the whole tree (secret
  literals, credential assignments, fetch-piped-into-shell patterns,
  exfiltration-shaped imperatives, off-whitelist URLs, prompt-injection
  tells). Hard-gated; wired into CI and the PR checklist.
- `scripts/leading_word_audit.py`: verifies the curated smell vocabulary in
  AGENTS.md actually lands in its routed skill (AGENTS.md stays the single
  source of truth). First run surfaced five missing terms, now planted:
  data clumps, shotgun surgery, switch proliferation, dead weight,
  ball of mud / god class.
- Eval corpus growth: +13 labeled probes — four paraphrase variants
  (r1–r4), three multi-skill wide probes using the secondary column
  (w1–w3), six adversarial out-of-domain decoys (z8–z13) — growing the
  corpus to 76 (63 positive / 13 negative). Re-graded through two rounds of
  three independent closed-book agent passes (artifacts in
  `eval/predictions/`, pred_a–f): canonical baseline is 60/63 positive under
  majority vote with 13/13 negatives rejected and zero leaks in every pass.
  Known misses are documented per-probe in `eval/BASELINE.md`.
- `eval/pass_at_k.py`: stability reporting over multiple prediction passes
  (per-probe flip rates; 72/76 probes stable in the initial run). Reporting
  tool — exit-0 policy, like the grader.
- `scripts/install.sh`: ownership-manifest installer for the OpenCode and
  Claude Code targets (`install` / `doctor` / `uninstall`, `--dry-run`
  everywhere). Manifest lives at `~/.config/codecraft/` outside the shipped
  surface; uninstall refuses to remove files modified after install.
  Maintainer-facing; never part of the shipped skill surface.
- GitHub Actions CI (`.github/workflows/ci.yml`) gating the static gates:
  structure gate, security scan, leading-word audit, plus the lexical floor
  as a diagnostic step. Semantic regression stays an explicit manual /
  agent-run step (the grader is deliberately exit-0).

### Fixed

- `eval/lexsim.py` read the wrong tab column for query text (it scored each
  probe's secondary-skill list instead of the query), silently degrading the
  diagnostic proxy; it now reads the query column.
- AGENTS.md verification docs pointed at a dangling upstream `PLAN.md`; the
  in-repo `eval/BASELINE.md` is now the reference.
- `patterns-behavioral` failed to engage on retry-with-compensation queries
  (probe `r3`: 1/3 across passes). Its description now carries the
  retry-with-compensating-rollback symptom plus the "retry and compensate"
  and "roll back the half-done step" triggers; 3/3 engagement after the
  change.

## [1.0.0] - initial release (unversioned)

Initial catalog release: 66 refactorings + 22 GoF design patterns packaged as
eleven auto-detecting skills, with the structural gate and a 63-probe
selection-eval corpus.
