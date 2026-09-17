#!/usr/bin/env python3
"""Structural gate for codecraft-skills. Stdlib only.

Usage: python3 scripts/check_skills.py [repo_root]
Exits 0 when all checks pass, 1 otherwise.
"""
import re
import sys
from pathlib import Path

ROOT_SKILLS = {"refactor-detect", "patterns-detect"}
LEAF_COUNTS = {
    "refactor-methods": 9,
    "refactor-objects": 8,
    "refactor-data": 15,
    "refactor-conditionals": 8,
    "refactor-calls": 14,
    "refactor-generalization": 12,
    "patterns-creational": 5,
    "patterns-structural": 7,
    "patterns-behavioral": 10,
}
EXPECTED_TOTAL = sum(LEAF_COUNTS.values())
MIN_DESC, MAX_DESC = 150, 1000
EXCLUDE_DIRS = {".git", "scripts", "eval"}


def parse_frontmatter(text):
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fm[key.strip()] = value.strip()
    return fm


def main(root: Path) -> int:
    failures = []

    def fail(msg):
        failures.append(msg)
        print(f"FAIL  {msg}")

    def ok(msg):
        print(f"PASS  {msg}")

    skill_dirs = sorted(
        d for d in root.iterdir()
        if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith(".")
    )
    names = {d.name for d in skill_dirs}
    expected = ROOT_SKILLS | set(LEAF_COUNTS)
    if names == expected:
        ok(f"{len(names)} skill directories present, names match catalog")
    else:
        fail(f"skill dirs unexpected={sorted(names - expected)} missing={sorted(expected - names)}")

    item_total = 0
    for d in skill_dirs:
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            fail(f"{d.name}: missing SKILL.md")
            continue
        text = skill_md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            fail(f"{d.name}: missing or malformed YAML frontmatter block")
            continue
        name = fm.get("name", "")
        desc = fm.get("description", "")
        if name != d.name:
            fail(f"{d.name}: frontmatter name '{name}' does not equal directory name")
        extra_fields = set(fm) - {"name", "description"}
        if extra_fields:
            fail(f"{d.name}: unexpected frontmatter fields {sorted(extra_fields)}")
        if not MIN_DESC <= len(desc) <= MAX_DESC:
            fail(f"{d.name}: description length {len(desc)} outside {MIN_DESC}-{MAX_DESC}")

        if d.name in ROOT_SKILLS:
            if "|" not in text:
                fail(f"{d.name}: root skill has no table (routing/detection)")
            if "rout" not in text.lower():
                fail(f"{d.name}: root skill has no routing section")
            if d.name in names and skill_md.exists():
                ok(f"{d.name}: root detector structure OK")
        else:
            expected_items = LEAF_COUNTS.get(d.name)
            if expected_items is None:
                fail(f"{d.name}: not a known leaf; add it to LEAF_COUNTS with its count")
                continue
            if "## Quick Pick" not in text:
                fail(f"{d.name}: missing '## Quick Pick' disambiguation table")
            items = sum(1 for ln in text.splitlines() if ln.startswith("### "))
            item_total += items
            if items != expected_items:
                fail(f"{d.name}: {items} '### ' item sections, expected {expected_items}")
            else:
                ok(f"{d.name}: {items}/{expected_items} catalog items present")

    if item_total != EXPECTED_TOTAL:
        fail(f"catalog total {item_total} != expected {EXPECTED_TOTAL}")
    else:
        ok(f"catalog coverage invariant holds ({EXPECTED_TOTAL} items across 9 leaves)")

    if failures:
        print(f"\n{failures.__len__()} check(s) FAILED")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    sys.exit(main(root))
