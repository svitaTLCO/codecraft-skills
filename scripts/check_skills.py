#!/usr/bin/env python3
"""Structural gate for codecraft-skills. Stdlib only.

Usage: python3 scripts/check_skills.py [repo_root]
Exits 0 when all checks pass, 1 otherwise. Enforces: schema and inventory
invariants, root-to-leaf routing cross-references, pairwise description
overlap floor, README badge consistency with eval/BASELINE.md, VERSION
presence/format, and .claude-plugin manifest cross-checks. Also
reports per-skill and total SKILL.md byte size (context cost) and a per-item
depth scorecard — informational, not gated.
"""
import json
import itertools
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
OVERLAP_WARN = 0.15
OVERLAP_FAIL = 0.30
SECTION_RE = re.compile(r"\*\*(Detect|Preconditions(?:\s*/\s*Avoid)?|Avoid|Apply|Pitfalls)[: ]?\*\*\s*(.*)$")


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


def shingles4(s):
    words = re.findall(r"[a-z]+", s.lower())
    return set(tuple(words[i:i + 4]) for i in range(len(words) - 3))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def inline_units(text):
    parts = [p for p in text.split(";") if p.strip()]
    return max(1, len(parts)) if text.strip() else 0


def item_depth(block_lines):
    detect_chars = 0
    pitfall_units = 0
    apply_units = 0
    has_precond = False
    in_fence = False
    i = 0
    while i < len(block_lines):
        line = block_lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        m = None if in_fence else SECTION_RE.match(stripped)
        i += 1
        if not m:
            continue
        kind, val = m.group(1), m.group(2)
        units = 0
        # absorb continuation lines (wrapped values / bullets) until a blank
        # line, label, heading, or fence marker
        while i < len(block_lines):
            nxt = block_lines[i].strip()
            if (not nxt or nxt.startswith("**") or nxt.startswith("#")
                    or nxt.startswith("|") or nxt.startswith("```")
                    or SECTION_RE.match(nxt)):
                break
            if nxt.startswith(("- ", "* ")):
                units += 1
            i += 1
        numbered = re.findall(r"(?:^|[\s;])\d+\)\s", " " + val)
        if kind == "Detect":
            detect_chars += len(val) + 4 * units
        elif kind in ("Preconditions", "Avoid"):
            has_precond = True
        elif kind == "Apply":
            apply_units += max(len(numbered), inline_units(val)) if val.strip() else 0
        elif kind == "Pitfalls":
            pitfall_units += inline_units(val) + units
    return detect_chars, pitfall_units, apply_units, has_precond


def fmt_range(lo, hi):
    return str(lo) if lo == hi else f"{lo}-{hi}"


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
    sizes = {}
    texts = {}
    descs = {}
    depth = {}
    for d in skill_dirs:
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            fail(f"{d.name}: missing SKILL.md")
            continue
        text = skill_md.read_text(encoding="utf-8")
        sizes[d.name] = len(text.encode("utf-8"))
        texts[d.name] = text
        fm = parse_frontmatter(text)
        if fm is None:
            fail(f"{d.name}: missing or malformed YAML frontmatter block")
            continue
        name = fm.get("name", "")
        desc = fm.get("description", "")
        descs[name] = desc
        if name != d.name:
            fail(f"{d.name}: frontmatter name '{name}' does not equal directory name")
        extra_fields = set(fm) - {"name", "description"}
        if extra_fields:
            fail(f"{d.name}: unexpected frontmatter fields {sorted(extra_fields)}")
        if not MIN_DESC <= len(desc) <= MAX_DESC:
            fail(f"{d.name}: description length {len(desc)} outside {MIN_DESC}-{MAX_DESC}")
        hazardous = [tok for tok in (": ", " #") if tok in desc]
        if hazardous:
            fail(f"{d.name}: description contains YAML-hazardous sequence(s) {hazardous} "
                 f"(strict parsers reject plain scalars with ': ' — use an em dash)")

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
            blocks = {}
            cur = None
            for ln in text.splitlines():
                if ln.startswith("### "):
                    cur = ln[4:].strip()
                    blocks[cur] = []
                elif cur is not None and not ln.startswith("#"):
                    blocks[cur].append(ln)
            stats = [item_depth(blk) for blk in blocks.values()]
            if stats:
                depth[d.name] = {
                    "items": len(stats),
                    "pit": (min(s[1] for s in stats), max(s[1] for s in stats)),
                    "apply": (min(s[2] for s in stats), max(s[2] for s in stats)),
                    "detect": (min(s[0] for s in stats), max(s[0] for s in stats)),
                    "thin": [n for n, s in zip(blocks, stats) if s[1] < 2 or s[2] < 2],
                }

    if item_total != EXPECTED_TOTAL:
        fail(f"catalog total {item_total} != expected {EXPECTED_TOTAL}")
    else:
        ok(f"catalog coverage invariant holds ({EXPECTED_TOTAL} items across 9 leaves)")

    for root_name in sorted(ROOT_SKILLS):
        text = texts.get(root_name)
        if text is None:
            continue
        fam = sorted(l for l in LEAF_COUNTS if l.startswith(root_name.split("-")[0]))
        missing = [l for l in fam if f"`{l}`" not in text]
        if missing:
            fail(f"{root_name}: does not reference sibling leaves {missing} "
                 "(router must name every skill it can route to)")
        else:
            ok(f"{root_name}: references all {len(fam)} sibling leaves")

    overlap_notes = []
    for (na, da), (nb, db) in itertools.combinations(sorted(descs.items()), 2):
        j = jaccard(shingles4(da), shingles4(db))
        if j >= OVERLAP_FAIL:
            fail(f"description overlap {na} x {nb}: Jaccard-4 {j:.2f} >= {OVERLAP_FAIL}")
        elif j >= OVERLAP_WARN:
            overlap_notes.append(f"  {na} x {nb}: {j:.2f}")
    print(f"\ndescription overlap (warn >= {OVERLAP_WARN}, fail >= {OVERLAP_FAIL})")
    print("\n".join(overlap_notes) if overlap_notes else "  none above warn threshold")

    baseline = root / "eval" / "BASELINE.md"
    values = {}
    if baseline.exists():
        for ln in baseline.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^baseline_(positive|negative)\s*=\s*(\d+)/(\d+)", ln)
            if m:
                values[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    else:
        fail("eval/BASELINE.md missing (single source of truth for baseline numbers)")
    readme = (root / "README.md").read_text(encoding="utf-8")
    badges = {
        "positive": re.search(r"routing-(\d+)%2F(\d+)", readme),
        "negative": re.search(r"declines-out-of-domain(?:-|%20)(\d+)%2F(\d+)", readme),
    }
    badge_problems = []
    for key, m in badges.items():
        if m is None:
            fail(f"README: {key} badge pattern not found")
            badge_problems.append(key)
        elif key not in values:
            fail(f"README: {key} badge present but baseline_{key} missing in BASELINE.md")
            badge_problems.append(key)
        elif (int(m.group(1)), int(m.group(2))) != values[key]:
            fail(f"README {key} badge {m.group(1)}/{m.group(2)} != BASELINE.md "
                 f"{values[key][0]}/{values[key][1]}")
            badge_problems.append(key)
    if values and not badge_problems:
        ok(f"README badges consistent with eval/BASELINE.md "
           f"(positives {values['positive'][0]}/{values['positive'][1]}, "
           f"negatives {values['negative'][0]}/{values['negative'][1]})")

    version_file = root / "VERSION"
    if version_file.exists():
        v = version_file.read_text(encoding="utf-8").strip()
        if re.fullmatch(r"\d+\.\d+\.\d+", v):
            ok(f"VERSION {v} present")
        else:
            fail(f"VERSION file malformed: {v!r} (want semver MAJOR.MINOR.PATCH)")
    else:
        fail("VERSION file missing")

    plugin_manifest = root / ".claude-plugin" / "plugin.json"
    marketplace_manifest = root / ".claude-plugin" / "marketplace.json"
    if not (plugin_manifest.exists() and marketplace_manifest.exists()):
        fail(".claude-plugin manifests missing (want plugin.json + marketplace.json)")
    else:
        try:
            pm = json.loads(plugin_manifest.read_text(encoding="utf-8"))
            mm = json.loads(marketplace_manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f".claude-plugin manifest invalid JSON: {e}")
            pm = mm = None
        if isinstance(pm, dict) and isinstance(mm, dict):
            ver = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else ""
            leaf_names = sorted(d.name for d in skill_dirs)
            problems = []
            if pm.get("name") != "codecraft-skills":
                problems.append("plugin.json name must be codecraft-skills")
            if mm.get("name") != pm.get("name"):
                problems.append("manifest names disagree")
            if str(pm.get("version")) != ver or str(mm.get("version")) != ver:
                problems.append("manifest versions out of sync with VERSION")
            if sorted(str(s) for s in pm.get("skills", [])) != [f"./{n}" for n in leaf_names]:
                problems.append("plugin.json skills array out of sync with catalog directories")
            if not str(pm.get("description") or "").strip():
                problems.append("plugin.json description empty")
            owner = mm.get("owner")
            if not (isinstance(owner, dict) and str(owner.get("name") or "").strip()):
                problems.append("marketplace.json owner.name missing")
            plugins = mm.get("plugins")
            if (not isinstance(plugins, list) or len(plugins) != 1
                    or plugins[0].get("name") != pm.get("name")
                    or plugins[0].get("source") != "./"):
                problems.append('marketplace.json plugins must be [{name, source: "./"}]')
            if problems:
                fail("; ".join(problems))
            else:
                ok(f"Claude Code manifests consistent (.claude-plugin: "
                   f"{len(leaf_names)} skills, version {ver})")

    print("\ncontext cost (SKILL.md bytes, informational — not gated)")
    for d in skill_dirs:
        n = sizes.get(d.name)
        print(f"  {d.name:<24} {n if n is not None else 'missing'}")
    print(f"  {'TOTAL':<24} {sum(sizes.values())}")

    print("\nitem depth (informational — not gated; thin = pitfalls < 2 units or apply < 2 units)")
    for leaf in sorted(depth):
        s = depth[leaf]
        print(f"  {leaf:<24} items={s['items']:<2} pitfall {fmt_range(*s['pit']):<4} "
              f"apply {fmt_range(*s['apply']):<4} detect {fmt_range(*s['detect'])}B "
              f"thin: {', '.join(s['thin']) if s['thin'] else '-'}")

    if failures:
        print(f"\n{failures.__len__()} check(s) FAILED")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    sys.exit(main(root))
