#!/usr/bin/env python3
"""Grade an LLM selection pass against the labeled corpus.

Inputs (tab-separated):
  eval/queries.tsv : query_id <TAB> expected_skill_or_NONE <TAB> query
  predictions file : one row per query, "<query_id><TAB><skill-or-NONE>"
                     (row order irrelevant)

Run: python3 grade_semantic.py predictions.tsv

Baseline recorded at creation: 55/56 positive strict-primary hits (the single
miss was a boundary probe dual-covered by another correct skill), 7/7 negative
queries rejected as NONE. A new leak on a negative query is a hard regression.
Exit code is always 0: this is a reporting tool, not a CI gate.
"""
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parent


def load_rows():
    rows = []
    for line in (EVAL / "queries.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        qid, label = line.split("\t")[0], line.split("\t")[1].strip()
        rows.append((qid, label))
    return rows


def load_preds(path):
    preds = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        preds[parts[0]] = parts[1].strip()
    return preds


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    rows = load_rows()
    preds = load_preds(sys.argv[1])
    missing = [q for q, _ in rows if q not in preds]
    positives = [(q, l) for q, l in rows if l != "NONE"]
    negatives = [(q, l) for q, l in rows if l == "NONE"]

    hits = [(q, l) for q, l in positives if preds.get(q) == l]
    misses = [(q, l, preds.get(q, "?")) for q, l in positives if preds.get(q) != l]
    rejected = [q for q, _ in negatives if preds.get(q) == "NONE"]
    leaks = [(q, preds.get(q, "?")) for q, _ in negatives if preds.get(q) != "NONE"]

    miss_txt = "; ".join(f"{q}: want {l}, got {p}" for q, l, p in misses) or "none"
    leak_txt = "; ".join(f"{q} -> {p}" for q, p in leaks) or "none"
    print(f"positives {len(hits)}/{len(positives)} strict-primary | misses: {miss_txt}")
    print(f"negatives rejected {len(rejected)}/{len(negatives)} | leaks: {leak_txt}")
    if missing:
        print(f"WARNING: {len(missing)} queries without predictions: {', '.join(missing)}")


if __name__ == "__main__":
    main()
