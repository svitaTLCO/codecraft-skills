# Eval baseline

Single source of truth for selection-regression numbers. Every other mention
of baseline figures (README badges, AGENTS.md, the grader docstring,
CONTRIBUTING) stays consistent with this file — `scripts/check_skills.py`
verifies the README badge values against it.

## Current baseline

baseline_positive = 60/63
baseline_negative = 13/13

- Corpus: 76 probes — 63 positive (strict-primary label required) and
  13 negative. Growth on 2026-09-18 added four paraphrase variants
  (r1–r4), three multi-skill wide probes (w1–w3) using the secondary
  column, and six adversarial out-of-domain decoys (z8–z13).
- Canonical score rule: majority vote across k=3 independent closed-book
  agent passes (a probe counts when ≥2 passes match the label; identical
  label-free input built by `build_input.py`, no repo access for the
  graders). The passes resample one model family — this measures answer
  stability, not cross-model robustness. Artifacts:
  `eval/predictions/pred_{d,e,f}.tsv` (current era; `pred_{a,b,c}.tsv`
  predates the 2026-09-18 patterns-behavioral description change), graded
  by `grade_semantic.py`, stability by `pass_at_k.py` (73/76 stable;
  3 flipped probes).
- Known misses under the canonical score (accepted, documented):
  - `x2` ("replace the product-type conditionals with subclasses", labeled
    `refactor-data`, polarity `ambiguity`): 2/3 passes route to
    `refactor-conditionals`, which the secondary column lists as a valid
    co-cover. Dual-covered boundary probe.
  - `w1` (field-by-field DTO assembled across five services, labeled
    `refactor-objects` with `refactor-calls` secondary): all three passes
    route it to `patterns-creational`; wide compound — strict-primary
    scoring cannot reward partial credit here.
  - `g3` (relay-layer probe, labeled `refactor-generalization`): 2/3
    passes now answer `refactor-objects`; it survived 2/3 in the pred_a–c
    era, so it flips across eras — treat it as an unstable boundary probe
    rather than overfitting either side.
- Resolved during the 2026-09-18 re-grade: `r3` (retry-and-compensation
  paraphrase, labeled `patterns-behavioral`) was the hardest paraphrase in
  the corpus (1/3); after the patterns-behavioral description gained the
  retry-with-compensating-rollback symptom and its two trigger phrases, it
  engages 3/3.
- `c2` flipped in the pred_a–c era but answers identically in all current
  runs — no longer tracked as unstable.
- Any new leak on a negative query is a hard regression. Current grading
  run: zero leaks, 13/13 across all three passes.

## Run history

| Date | Positive | Negative | Corpus | Note |
|---|---|---|---|---|
| 2026-09-18 | 55/56 | 7/7 | 63 | Baseline re-verified via independent subagent grading passes (three). |
| 2026-09-18 | 60/63 | 13/13 | 76 | Corpus growth (+r1–r4 paraphrases, +w1–w3 wides, +z8–z13 decoys). Per-pass strict: 58, 60, 61 of 63; negatives 13/13 on all passes. Canonical = majority vote (see rule above); 4 probes flipped across passes (c2, g3, r3, w1), 72/76 stable. Zero negative leaks. |
| 2026-09-18 | 60/63 | 13/13 | 76 | Re-grade after patterns-behavioral description gained retry/compensating-rollback triggers (passes saved as pred_d–f): per-pass strict 61/60/60; r3 recovered to 3/3 engagement, c2 stable 3/3, g3 moved into known misses (2/3 refactor-objects), x2 dual-covered (2/3 secondary), w1 unchanged (3/3 patterns-creational). Flips: o3, g3, x2; 73/76 stable. Zero negative leaks. |

Update rule: after any corpus or description change, run the full grading
pass (AGENTS.md "Verification workflow", step 2), record the result in the
table above, and — when the corpus grows — update the two `baseline_*` lines
and the README badges in the same commit.
