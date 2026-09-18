#!/usr/bin/env python3
"""Pass@k stability report for the semantic routing corpus (diagnostic).

Grades k independent LLM prediction passes over the same labeled corpus and
reports per-probe flip rate: whether a probe produced different answers across
the k passes. A flipped probe points at description ambiguity or a boundary
case worth sharpening; a stable wrong one points at a systematic selection
bias. Reporting tool only: exit code is always 0, matching
grade_semantic.py - the machine gate lives in scripts/check_skills.py.

Input: k prediction files ("<qid><TAB><skill-or-NONE>", row order irrelevant),
typically three independent runs:

    python3 pass_at_k.py pred_a.tsv pred_b.tsv pred_c.tsv
"""
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parent


def load_preds(path):
    preds = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            preds[parts[0].strip()] = parts[1].strip()
    return preds


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    rows = [
        (line.split("\t")[0], line.split("\t")[1].strip())
        for line in (EVAL / "queries.tsv").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    k = len(sys.argv) - 1
    passes = [load_preds(p) for p in sys.argv[1:]]
    missing_any = {q: [i for i, p in enumerate(passes, 1) if q not in p]
                   for q, _ in rows
                   if any(q not in p for p in passes)}
    stable = []
    flips = []
    for qid, _label in rows:
        answers = [p.get(qid, "?missing") for p in passes]
        if len(set(answers)) == 1:
            stable.append((qid, answers[0]))
        else:
            flips.append((qid, answers))
    total = len(rows)
    print(f"pass@{k} stability: {len(stable)}/{total} probes answered identically "
          f"across all {k} passes")
    print(f"flipped probes ({len(flips)}):")
    for qid, answers in flips:
        print(f"  {qid}: {' | '.join(answers)}")
    consistent_pos = sum(1 for q, a in stable if a != "NONE")
    consistent_none = sum(1 for q, a in stable if a == "NONE")
    print(f"stable breakdown: {consistent_pos} consistently-routed, "
          f"{consistent_none} consistently-rejected, "
          f"{sum(1 for q, a in stable if a == '?missing')} unanswered")
    if missing_any:
        bad = ", ".join(f"{q} (pass {','.join(map(str, v))})"
                        for q, v in sorted(missing_any.items()))
        print(f"WARNING: queries missing from some passes: {bad}")


if __name__ == "__main__":
    main()
