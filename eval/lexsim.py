#!/usr/bin/env python3
"""Lexical lower-bound baseline for auto-selection (diagnostic proxy only).

Scores each query against every skill's description with case-insensitive
word containment (multi-word triggers get extra weight, negation hints like
"not-to"/avoid penalize matches). This is NOT how agents actually select —
real routing is semantic — so treat low scores as noise floor information,
not a verdict. Useful mainly to catch gross description regressions where the
keyword surface of a skill shrank.

Reads skills straight from ../<skill>/SKILL.md; stdlib only.
Usage: python3 lexsim.py
"""
from pathlib import Path
import re

EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parent
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
NEGATION_HINTS = (" not-to", " not to", " instead ", " rather than", " avoid ")


def load_skills():
    skills = {}
    for skill_dir in sorted(ROOT.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        m = FRONTMATTER.match(skill_md.read_text(encoding="utf-8"))
        if not m:
            continue
        fm = {}
        for line in m.group(1).splitlines():
            key, sep, value = line.partition(":")
            if sep:
                fm[key.strip()] = value.strip()
        skills[fm.get("name", skill_dir.name)] = fm.get("description", "")
    return skills


def score(query: str, desc: str) -> float:
    s = 0.0
    q_words = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 3]
    d_lower = desc.lower()
    for w in set(q_words):
        if w in d_lower:
            s += 1.0
    for phrase in re.findall(r'"([^"]{4,})"', desc):
        if phrase.lower() in query.lower():
            s += 3.0
    if any(h in query.lower() for h in NEGATION_HINTS) and "instead" in desc.lower():
        s -= 0.5
    return s


def main():
    skills = load_skills()
    strict_correct = 0
    family_hits = {"refactor": 0, "patterns": 0}
    flag = []
    none_hits = 0
    for line in (EVAL / "queries.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        qid, label, query = line.split("\t")[:3]
        best = max(skills.items(), key=lambda kv: score(query, kv[1]))
        b_name, b_desc = best
        b_score = score(query, b_desc)
        b_family = "refactor" if b_name.startswith("refactor-") else \
            "patterns" if b_name.startswith("patterns-") else "other"
        if b_score < 1.0:
            flag.append((qid, label, round(b_score, 2), b_name))
        if label != "NONE":
            if label.startswith(b_family):
                family_hits[b_family] += 1
            if label == b_name:
                strict_correct += 1
        else:
            if b_name == "NONE" or b_score < 1.0:
                none_hits += 1
    lines = [x for x in (EVAL / "queries.tsv").read_text(encoding="utf-8").splitlines() if x.strip()]
    labels = [x.split("\t")[1].strip() for x in lines]
    labels_nonnone = sum(1 for l in labels if l != "NONE")
    n_refactor = sum(1 for l in labels if l.startswith("refactor-"))
    n_patterns = sum(1 for l in labels if l.startswith("patterns-"))
    print(f"strict primary-name top-1 : {strict_correct}/{labels_nonnone}")
    print(f"family-level top-1        : refactor {family_hits['refactor']}/{n_refactor}, patterns {family_hits['patterns']}/{n_patterns}")
    print(f"weak-signal flags (score < 1.0): {len(flag)}")
    for qid, label, sc, b in flag:
        print(f"  {qid} label={label} score={sc} picked={b}")


if __name__ == "__main__":
    main()
