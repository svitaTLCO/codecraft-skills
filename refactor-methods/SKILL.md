---
name: refactor-methods
description: Detect and apply refactoring.guru "Composing Methods" refactorings — Extract Method, Inline Method, Extract Variable, Inline Temp, Replace Temp with Query, Split Temporary Variable, Remove Assignments to Parameters, Replace Method with Method Object, Substitute Algorithm. Use when a method/function is too long, full of local variables or temps, comment-heavy, duplicated inside itself, or computes something with an inappropriate algorithm. Triggers — "split this function", "method too long", "clean up locals", "too many temp vars", "rename what this block does", "wrong algorithm here".
---

# Composing Methods (Refactoring.Guru set)

Restructure code *inside* functions/methods so intent reads clearly. Load `refactor-detect` first if you need to decide which category applies.

## Quick Pick

| Symptom | First choice | Fallback / combine with |
|---|---|---|
| Function > ~20 lines or mixes levels of abstraction | Extract Method | Repeat until top-level reads as a summary |
| One-liner called once, name adds nothing | Inline Method | Then rename the call site |
| Meaningful value needs a name; magic computation inline | Extract Variable | Introduce Explaining Variable style naming |
| Temp variable assigned once, used nearby, no side effects | Inline Temp | If reassigned between uses → keep or Split |
| Long chain of temp assignments feeding one result | Replace Temp with Query | Only safe when statements are non-interacting |
| Temp mutated in multiple unrelated ways | Split Temporary Variable | One variable per semantic purpose |
| Function modifies its own parameters | Remove Assignments to Parameters | Local var instead of parameter |
| Method needs many helpers/locals, state scattered across temps | Replace Method with Method Object | Also eliminates temporary fields |
| Computation works but via wrong/slow/over-complex mechanism | Substitute Algorithm | Verify identical output on edge cases |

General preconditions: target unit compiles + tests pass before and after; language supports nested/local functions where needed; statement ordering preserved (side effects stay observable).

## Techniques

### Extract Method
**Detect:** long method; commented section ("// compute discount"); duplicated fragment inside the same method; nested conditionals doing distinct jobs.
**Preconditions:** no temps spanning the extracted range (or hoist them out first); extracted block touches only accessible data.
**Apply:** move statements into a private method; name it by *intent* (what the result means, not how); pass required inputs explicitly; return the result if used.
**Pitfalls:** extracting ranges that share mutable temps changes behavior; avoid extracting blocks whose correctness depends on execution interleaving with siblings; don't extract single statements without a reason.

### Inline Method
**Detect:** method body is one simple expression/statement and the method's name adds no information over the expression itself; wrapper exists only historically.
**Preconditions:** exactly one call site (or all sites benefit); not virtual/dispatched/polymorphic; not public API used elsewhere.
**Apply:** replace calls with the body; delete the method; fix imports/references; run tests.
**Pitfalls:** inlining a polymorphic override silently breaks subclasses' expectations; check reflection/dynamic dispatch usages.

### Extract Variable
**Detect:** a non-trivial expression is repeated, hard to parse, or named by position (`result[i]`); comments explain the computed value.
**Preconditions:** expression has no meaningful side-effect order, or duplicating it is acceptable; the variable name can capture intent.
**Apply:** compute into a well-named variable at point of use; use the variable everywhere the expression appeared.
**Pitfalls:** if the expression must re-evaluate (e.g., time-dependent), extracting freezes it — verify semantics.

### Inline Temp
**Detect:** `temp = <simple expr>` assigned once; every use could take the expression directly; variable name is opaque (`x`, `t`); dead weight — locals/parameters unused or needlessly copied.
**Preconditions:** single assignment; expression pure (no side effects); cheap enough to repeat; no language aliasing subtleties (by-reference captures).
**Apply:** substitute the expression at each use; delete the declaration.
**Pitfalls:** repeated evaluation may have different performance/exception timing; closures capturing the temp by reference change semantics when inlined.

### Replace Temp with Query
**Detect:** sequence like `t1 = f(a); t2 = g(t1); result = h(t2)` where each step only depends on earlier ones.
**Preconditions:** each statement depends only on previously computed values (no interactions between later/earlier statements); no shared mutable state touched mid-sequence.
**Apply:** turn each temp into a small query method returning its value; main flow becomes a readable pipeline of calls.
**Pitfalls:** if any two statements interact through globals/collections, splitting breaks causality — stop and use Split Temporary Variable instead.

### Split Temporary Variable
**Detect:** one temp written in several places serving different purposes (`amount` used for both gross and discounted); reader can't track current meaning.
**Preconditions:** each semantic role can be identified from usage context.
**Apply:** create one variable per role; replace writes/reads so each variable is written once or monotonically.
**Pitfalls:** missed read/write conversion silently flips values — diff-check every occurrence.

### Remove Assignments to Parameters
**Detect:** `param = <new value>` inside a function; parameter shadows an outer concept; caller cannot know post-call value.
**Preconditions:** assigned value isn't intentionally returned through the parameter (some languages/C-style APIs do this — convert to return value instead).
**Apply:** introduce a local variable holding the new value; leave the parameter read-only.
**Pitfalls:** languages with pass-by-reference (C, Go pointers, Python lists) — the "assignment" may be mutation of a shared object; handle with Replace Data Value with Object territory.

### Replace Method with Method Object
**Detect:** method needs many helper methods and locals; a procedure that mutates multiple temporary fields; complex computation interleaved with I/O/state.
**Preconditions:** the temp state is confined to the method (no other code reads it).
**Apply:** create a class with a field per local variable; move the method body into a `compute()` there; move helper methods along; callers construct the object and invoke `compute()`.
**Pitfalls:** increases object count; keep the class package-private/internal; this is also the fix for the *Temporary Field* smell.

### Substitute Algorithm
**Detect:** computation produces correct results but via brute force, string hacking, O(n²) where O(n log n) suffices, or an idiom that obscures intent (bit acrobatics, hand-rolled parsing).
**Preconditions:** input/output contract fully characterized by tests — including edge cases (empty, max, invalid); old and new produce equal outputs.
**Apply:** write the better algorithm alongside; add differential test comparing old vs new on a corpus; swap; remove old.
**Pitfalls:** performance substitutions hide behavioral changes (tie-breaking, locale, floating rounding) — pin those down in tests first.

## Safe application protocol
Baseline tests → one technique per step → compile+test after each → diff review for reordered side effects → final sweep for dead locals/imports.
