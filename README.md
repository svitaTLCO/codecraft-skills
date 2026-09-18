<div align="center">

# 🛠️✨ codecraft-skills

### Give any coding agent the craft of refactoring and design patterns.

**Complete catalogs · symptom-driven detection · pitfalls known upfront · zero runtime**

<br>

![items](https://img.shields.io/badge/items-88%20catalog--complete-brightgreen?style=for-the-badge)
![routing](https://img.shields.io/badge/routing-60%2F63%20benchmarked-purple?style=for-the-badge)
![declines](https://img.shields.io/badge/declines-out-of-domain%2013%2F13-blue?style=for-the-badge)
![agents](https://img.shields.io/badge/agents-opencode%20%C2%B7%20claude-code%20%C2%B7%20any-loader-orange?style=for-the-badge)
![license](https://img.shields.io/badge/license-MIT-lightgrey?style=for-the-badge)

</div>

---

## 📑 Contents

- [Why](#why-)
- [Quick Start](#quick-start-)
- [How It Works](#how-it-works-)
- [Skill Catalog](#skill-catalog-)
- [Evidence & Quality Contract](#evidence--quality-contract-)
- [Supported Install Paths](#supported-install-paths-)
- [Source & Credit](#source--credit-)
- [Contributing](#contributing-)
- [License](#license-)

## Why 💡

Most agents don't fail because they lack intelligence. They fail because they arrive **uncertain**:

- 🤷 No idea whether to *Extract Method* or reach for *Strategy*
- 📚 Complete catalogs exist out there — nobody hands them over at the moment of need
- 🔁 Every session re-derives the same smell-to-technique mapping from scratch
- 💥 Applies the wrong move and silently breaks behavior (extracting across side effects, premature polymorphism)

**codecraft-skills fixes all four.** Two complete catalogs — **66 refactorings** + **22 GoF design patterns** — packaged as eleven auto-detecting agent skills. Describe the symptoms in plain language; the right skill engages on its own, picks the technique, and applies it with the pitfalls already known.

| Capability | What You Get |
|---|---|
| 🎯 **Symptom Detection** | Smell tables map what developers *actually type* to the exact technique |
| 🧭 **Master Routing** | Root detectors handle vague/global requests with explicit tie-break rules |
| ⚡ **Quick-Pick Disambiguation** | Every leaf opens with the pairs people confuse most |
| 🧪 **Apply + Pitfalls** | Language-neutral steps plus concrete failure modes per item |
| 🚫 **Honest Declines** | Out-of-domain requests rejected instead of force-fit |

> 💡 **Say one sentence** — *"BillingService knows how to email, invoice and store — break it up"* — and you get a routed, preconditions-checked application plan with its known failure modes attached.

## Quick Start ⚡

```bash
git clone https://github.com/svitaTLCO/codecraft-skills.git
cd codecraft-skills

cp -R refactor-methods ~/.agents/skills/       # opencode layout
cp -R patterns-behavioral ~/.claude/skills/    # Claude Code layout

# or use the tracked installer (ownership manifest in ~/.config/codecraft/,
# so uninstall removes exactly what it installed):
scripts/install.sh install --target opencode
scripts/install.sh doctor                     # integrity + freshness check
scripts/install.sh uninstall --dry-run        # preview removals
```

Every skill is self-contained — one `SKILL.md`, YAML frontmatter, no runtime, no dependencies. Install all eleven or cherry-pick: each description carries its own scope boundary, so wrong-skill pickup stays unlikely. Symlink while iterating locally:

```bash
ln -s "$PWD/refactor-detect" ~/.agents/skills/refactor-detect
```

## How It Works 🧭

Detection runs the same strict loop for both catalogs:

1. 🎙️ **Intake** — developer describes symptoms in plain language
2. 🧭 **Route** — a root detector collects smell signals, resolves ties by explicit rules, loads the right leaf
3. 🎯 **Disambiguate** — the leaf's Quick-Pick table narrows candidates to the exact item
4. ✅ **Apply** — preconditions checked → numbered language-neutral steps → pitfalls stated up front

It works on the phrasing developers actually use — verbatim rows from the benchmark corpus in [`eval/`](eval):

| You say | What engages |
|---|---|
| *"our checkout module feels like a ball of mud, tell me what to fix first"* | `refactor-detect` — an ordered, signal-ranked plan |
| *"split calculateTotal: it computes tax, applies discounts and formats output, all inline"* | `refactor-methods` → **Extract Method** |
| *"BillingService has forty fields and knows how to email, invoice and store - break it up"* | `refactor-objects` → **Extract Class** |
| *"legacy SDK is callbacks; I want a promise-based wrapper over it without touching the vendor lib"* | `patterns-structural` |
| *"shipping cost policy differs per carrier and must be chosen per order at dispatch time"* | `patterns-behavioral` → **Strategy** territory |
| *"deploy this Flask app to Azure App Service"* | nothing — out of domain, correctly declined |

## Skill Catalog 🧰

```text
codecraft-skills/
  🧭 refactor-detect           master router for global / meta requests
  ✂️ refactor-methods          split, inline, extract, simplify                    (9 techniques)
  📦 refactor-objects          move classes, methods, fields; Extract Class        (8)
  🗃️ refactor-data             variables, arrays, records, constants               (15)
  ❓ refactor-conditionals     guards, nesting, polymorphic switches               (8)
  📞 refactor-calls            signatures, parameters, API shape                   (14)
  🌳 refactor-generalization   inheritance, templates, generics                    (12)
  🧩 patterns-detect           master router for pattern-level requests
  🏗️ patterns-creational       Factory Method, Abstract Factory, Builder, Prototype, Singleton (5)
  🧱 patterns-structural       Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy (7)
  ⚙️ patterns-behavioral       Strategy, State, Observer, Mediator, Command, Iterator … (10)
```

**66 refactorings + 22 patterns = 88 catalog items**, each carrying Detect / Preconditions / Apply / Pitfalls. Counts are invariants enforced by the gate, not marketing numbers.

## Evidence & Quality Contract 🧾

Measured, not asserted — on a 76-probe corpus (63 in-domain, 13 deliberately out-of-domain), scored by three independent closed-book agent passes:

- 📊 **60/63** strict-primary routing hits under majority vote across the three passes (per-pass range 60–61; residual misses are documented dual-covered / wide-boundary probes in `eval/BASELINE.md`)
- 🚫 **13/13** out-of-domain queries rejected instead of force-fitted — zero leaks on all three passes
- 🔁 **Stability** — `pass_at_k.py` reports per-probe flip rate; 73/76 probes answered identically across passes
- 🧪 **Structural gate** — `python3 scripts/check_skills.py` enforces schema, inventory invariants (66+22), router→leaf cross-references, a description-overlap floor, README-badge↔baseline agreement, and VERSION presence/format
- 🛡️ **Content security** — `scripts/security_scan.py` hard-gates against secret-looking literals, credential assignments, fetch-piped-into-shell patterns, off-whitelist URLs, exfiltration imperatives, and prompt-injection tells
- ✂️ **Leading words** — `scripts/leading_word_audit.py` verifies every curated smell term appears in the skill it routes to
- 🧾 **Reproducible eval** — stdlib-only corpus + graders in [`eval/`](eval); canonical numbers in [`eval/BASELINE.md`](eval/BASELINE.md); workflow documented in `AGENTS.md`

> ✅ **Any change that degrades routing without a measured improvement is a regression.** That's the floor, not the ceiling.

## Supported Install Paths 🤝

| Agent | Skills Directory |
|---|---|
| 🟢 **OpenCode** | `~/.agents/skills/<name>/` |
| 🟠 **Claude Code** | `~/.claude/skills/<name>/` |
| ⚪ **Any loader** | one `SKILL.md` per skill, YAML frontmatter (`name`, `description`) — nothing else to wire |

The root `SKILL.md` files are the single source of truth for each category — no duplicated config, no generated artifacts.

## Source & Credit 📚

Catalog names, classifications, and family structure follow [refactoring.guru](https://refactoring.guru/) (© Alexander Shvets). Every explanation, heuristic, and example here is written from scratch — nothing is copied from the site.

## Contributing 🛠️

Want to sharpen a detection heuristic? Read [`AGENTS.md`](AGENTS.md) — the canonical contract for human *and* AI agents — and [`CONTRIBUTING.md`](CONTRIBUTING.md) for the short version.

Every PR must include:

- ✅ Spec validation pass (`python3 scripts/check_skills.py`)
- ✅ Selection eval with no regression vs baseline ([`eval/`](eval))
- ✅ Description still lists every covered item verbatim
- ✅ Attribution intact

## License 📜

[MIT](LICENSE)

<div align="center">

**Built for engineers who expect their agents to know the craft.**

</div>
