#!/usr/bin/env python3
"""Leading-word audit for codecraft-skills. Stdlib only.

AGENTS.md curates the canonical smell vocabulary (term -> routed skill) and
the doctrine says those exact phrases are highest-weight tokens for
auto-selection, so each curated term must actually appear in the routed
skill. This audit parses that table straight from AGENTS.md (single source
of truth - no duplication here) and reports terms absent from their target.

Verdicts per term:
  desc   - found in the target's description frontmatter (best case)
  body   - found only in the target's body text (works, weaker priming)
  missing- not found anywhere in the target skill (fails the gate)

Usage: python3 scripts/leading_word_audit.py [repo_root]
Exits 0 when no term is missing, 1 otherwise.
"""

import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TARGET_CELL_RE = re.compile(r"`([a-z][a-z0-9-]*)`")


def load_skills(root):
    skills = {}
    for p in sorted(root.glob("*/SKILL.md")):
        text = p.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(text)
        desc = ""
        if m:
            for line in m.group(1).splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
        skills[p.parent.name] = {
            "desc": desc.lower(),
            "body": text[m.end():].lower() if m else text.lower(),
        }
    return skills


def parse_vocabulary_table(agents_text):
    rows = []
    in_selection = False
    for ln in agents_text.splitlines():
        if ln.startswith("### Selection side"):
            in_selection = True
            continue
        if in_selection and ln.startswith("### "):
            break
        if not (in_selection and ln.lstrip().startswith("|")):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if not cells[0] or set(cells[0]) <= {"-", " ", ":"}:
            continue
        if cells[0].lower().startswith("term"):
            continue
        tm = TARGET_CELL_RE.search(cells[2])
        if tm:
            rows.append((cells[0], tm.group(1)))
    return rows


def main():
    root = (
        Path(sys.argv[1]) if len(sys.argv) > 1
        else Path(__file__).resolve().parent.parent
    )
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    rows = parse_vocabulary_table(agents)
    if not rows:
        print("FAIL  could not parse the smell-vocabulary table from AGENTS.md")
        return 1
    skills = load_skills(root)
    weak = []
    missing = []
    for term, target in rows:
        variants = [v.strip().lower() for v in term.split("/") if v.strip()]
        info = skills.get(target)
        if info is None:
            missing.append((term, target, "target skill dir not found"))
            continue
        if any(v in info["desc"] for v in variants):
            continue
        if any(v in info["body"] for v in variants):
            weak.append((term, target))
            continue
        missing.append((term, target, "term not present in target skill"))
    body_only = []
    for term, target in weak:
        body_only.append(f"{term!r} only in body of {target}")
    print(f"leading-word audit: {len(rows)} curated terms checked")
    for note in body_only:
        print(f"WEAK  {note} (primed but not in description)")
    if missing:
        for term, target, why in missing:
            print(f"MISSING  {term!r} -> {target}: {why}")
        return 1
    print(f"PASS  every curated term appears in its routed skill"
          + (f" ({len(body_only)} body-only)" if body_only else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
