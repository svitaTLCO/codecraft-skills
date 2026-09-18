---
name: refactor-detect
description: Analyze a user query and code to detect which refactoring.guru refactoring applies, then apply it safely. Master entry point for all 66 refactoring techniques in six categories (composing methods, moving features between objects, organizing data, simplifying conditionals, simplifying method calls, dealing with generalization). Use when the user says "refactor", complains about long methods/functions, duplicated code, weird classes, tangled inheritance, messy conditionals, bad naming, or asks "how do I clean up this code". Triggers — "refactor this", "clean up", "code smell", "too long", "too many parameters", "split function", "move this logic", "simplify if/else", "tighten inheritance".
---

# Refactor Detect (Refactoring.Guru set — router)

Detect which refactoring(s) fit the situation described by the user or shown in their code, choose an order, apply them one at a time, and verify behavior is unchanged. Refactoring changes structure only — never observable behavior.

## Workflow

1. **Intake** — Extract from the user's message + the code they point at:
   - Which file/class/function is painful? Read it first; never diagnose from vibes alone.
   - Is there a test suite that runs fast? If not, say so before touching anything (see Safety).
   - What must NOT change? Public API, file names, performance-critical paths, DB queries, side effects.
2. **Classify the hotspot** — Match what you see against the Smell Detection Table below. One hotspot usually matches 1–3 smells.
3. **Pick technique(s)** — Use the smell→technique mapping, then open the matching sub-skill for steps:
   | Code area hurts | Load skill |
   |---|---|
   | Inside one function/method body | `refactor-methods` |
   | Logic in wrong class; class too big/too small | `refactor-objects` |
   | Fields, values, types, data modeling | `refactor-data` |
   | if/else/switch tangles, flags, null checks | `refactor-conditionals` |
   | Function signatures, params, return/error conventions | `refactor-calls` |
   | Inheritance hierarchy: base/derived mismatches | `refactor-generalization` |
4. **Order the changes** — Apply the ordering rules below; present the ordered list to the user before editing multi-step work.
5. **Apply one step at a time**, verifying after each (Safety section). Each single-technique edit should be independently reviewable in the diff.
6. **Debrief** — report per step: technique used, why it fits the symptom, verification result.

If the pain is architectural ("this design keeps changing in N places", "I add a new X and touch five files") rather than local ugliness, the answer may be a **design pattern** instead of a refactoring — use the `patterns-detect` skill.

## Smell Detection Table

How to read a user's symptoms into smells. Multiple rows can match; strongest signals win.

| # | Smell | Signal in code | Signal in user words | Primary techniques (sub-skill) |
|---|-------|---------------|----------------------|-------------------------------|
| 1 | Long Method | >~20 lines; nested blocks; comments narrating sections | "method too long", "split this function" | Extract Method, Split Temporary Variable, Replace Temp with Query (`refactor-methods`) |
| 2 | Large Class | Dozens of fields; does everything; unclear name | "class does too much", "break this up" | Extract Class (`refactor-objects`) |
| 3 | Primitive Obsession | int/string booleans representing concepts (money, email, status=2) | "model this properly", "magic numbers everywhere" | Replace Data Value with Object, Encapsulate Field (`refactor-data`) |
| 4 | Long Parameter List | 5+ params; callers pass same clusters repeatedly | "too many args", "confusing call signature" | Introduce Parameter Object, Replace Parameter with Explicit Methods (`refactor-calls`) |
| 5 | Data Clumps | Same pair/group of variables appears in several functions/classes | "these three values always travel together" | Introduce Parameter Object, Extract Class (`refactor-calls` / `refactor-objects`) |
| 6 | Switch Statements | switch on type/tag scattered across the codebase | "every new type means new switches" | Replace Conditional with Polymorphism, Replace Type Code with Subclasses (`refactor-conditionals` / `refactor-data`) |
| 7 | Temporary Field | A field only exists during one computation | "why is this instance var here?", stray `var x` at top-level flow | Extract Class (as state holder), Replace Method with Method Object (`refactor-objects`) |
| 8 | Refused Bequest | Derived ignores/overrides most of base API | "base class has stuff I don't use", "override returns notImplemented" | Replace Inheritance with Delegation, Push Down Method (`refactor-generalization`) |
| 9 | Alternative Classes with Different Interfaces | Similar classes missing members each other have | "Foo and Bar are almost the same shape" | Extract Superclass (`refactor-generalization`) |
| 10 | Divergent Change | One class changes for many unrelated reasons | "one edit breaks N unrelated things" | Extract Class (`refactor-objects`) |
| 11 | Shotgun Surgery | One feature touches many classes | "changing this requires edits in five files" | Move Method/Move Field toward cohesion, Extract Class (`refactor-objects`) |
| 12 | Parallel Inheritance Hierarchies | Two hierarchies mirror each other (e.g., Foo bars with Baz bazes) | "two trees that should be one" | Extract Interface, Collapse Hierarchy (`refactor-generalization`) |
| 13 | Comments | Comments explaining *why* a block does something (not just the fact) | "comments carry the real meaning" | Extract Variable, Rename Method (make intent explicit in code) (`refactor-methods` / `refactor-calls`) |
| 14 | Duplicate Code | Copied blocks differing in few details | "copy-pasted this again" | Extract Method (Consolidate Duplicate Fragments), Substitute Algorithm, Parameterize Method (`refactor-methods` / `refactor-calls`) |
| 15 | Lazy Class | Small object barely used, mostly getters/setters | "do we even need this wrapper?" | Inline Class (`refactor-objects`) |
| 16 | Data Class | Pure data + accessors, no behavior | "bag of fields", "where's the logic?" | Move related behavior into it; else Inline Class (`refactor-objects` / `refactor-data`) |
| 17 | Dead Code | Unused methods/fields/branches | "is this still used?" | Verify with call-site search, then delete (no special technique) |
| 18 | Speculative Generality | Abstractions for imagined future needs | "added interface for maybe-later" | Remove the abstraction; Inline Class; Collapse Hierarchy |
| 19 | Feature Envy | A method uses another class's data far more than its own | "this method wants to live elsewhere" | Move Method, Move Field (`refactor-objects`) |
| 20 | Inappropriate Intimacy | Peering deep into internals of a close friend | "they know too much about each other" | Extract Class (facade-like boundary), Hide Delegate (`refactor-objects`) |
| 21 | Message Chains | `a.getB().getC().doD()` traversals | "long chains of getters" | Introduce Foreign Method / Hide Delegate (`refactor-objects`) |
| 22 | Middle Man | Pass-through methods doing nothing but forward | "why is this wrapper here?" | Remove Middle Man (`refactor-objects`) |
| 23 | Incomplete Library Class | Wrapping/extending a library class whose needs don't match yours | "fighting the base class from a third-party lib" | Replace Inheritance with Delegation (`refactor-generalization`) |

Numbered 1–23 because the guide groups 22 named smells plus the library-class case; treat all as equal detection inputs.

## Ordering Rules

1. **Test-first, extract-first.** Ensure a passing test/build baseline before the first edit. Prefer pure-comprehension steps (Rename, Extract Variable) before structural ones (Extract Class).
2. **Small → large within a category.** Fix composition inside methods before moving features between objects; encapsulate before you move data around.
3. **Prepare dependencies before the risky step.** E.g., before Pull Up/Push Down, make sure the moved member compiles in the target class; before Extract Class, self-encapsulate the fields it will take.
4. **One logical unit per commit/step.** Never bundle two different techniques in one unverified hunk.
5. **Finish leaves before trimming branches.** After restructuring, check for now-redundant pieces (Inline Class, Collapse Hierarchy, remove dead code) in a final pass.
6. **Polymorphism last in a cluster.** If a smell chain ends at Switch Statements, replace conditionals with polymorphism only after the objects they discriminate over have been extracted.

## Safety Protocol

- Before any step: confirm build + relevant tests pass (record the command). If none exist, propose adding a characterization test for the changed unit first, or proceed only with zero-risk mechanical renames/extractions and tell the user explicitly.
- During: change ONE technique per step; keep public signatures stable unless the technique's purpose is to change them (state which callers were updated).
- After each step: re-run build/tests; inspect the diff for accidental behavior drift (reordered statements, swallowed exceptions, widened visibility, default-value shifts).
- Roll back immediately if a step can't be verified; mark it pending in the plan.

## Verification Checklist (final)

- [ ] All planned techniques applied, or deviations stated.
- [ ] Build + tests pass with the same results as baseline.
- [ ] Diff reviewed: no behavior changes, no leftover cruft (unused imports, orphaned helpers).
- [ ] Public API delta reported (or "none").
- [ ] Remaining known smells listed honestly instead of silently fixed.
