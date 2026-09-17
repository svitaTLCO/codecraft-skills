#!/usr/bin/env python3
"""Regenerate eval/semantic_input.txt from the repo's SKILL.md files.

The input is the full inventory (names + descriptions) that the model performs
selection over. Run this whenever a description or item list changes so the
grading pass measures current content, not a stale snapshot.

Stdlib only: python3 build_input.py
"""
import re
from pathlib import Path

EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parent
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def frontmatter(path: Path) -> dict:
    m = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fm[key.strip()] = value.strip()
    return fm


def main() -> None:
    blocks = []
    for skill_dir in sorted(ROOT.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        fm = frontmatter(skill_md)
        name = fm.get("name", skill_dir.name)
        desc = fm.get("description", "")
        blocks.append(f"{name}\n{desc}\n===SKILL===")
    out = EVAL / "semantic_input.txt"
    out.write_text("\n".join(blocks) + "\n", encoding="utf-8")
    print(f"wrote {len(blocks)} skills -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
