---
name: refactor-conditionals
description: Detect and apply refactoring.guru "Simplifying Conditional Expressions" refactorings — Decompose Conditional, Consolidate Conditional Expression, Consolidate Duplicate Conditional Fragments, Remove Control Flag, Replace Nested Conditional with Guard Clauses, Replace Conditional with Polymorphism, Introduce Null Object, Introduce Assertion. Use for if/else tangles, deep nesting, boolean flags as control flow, type-code switches, scattered null checks, or preconditions hidden in conditionals. Triggers — "simplify this if", "too much nesting", "guard clauses", "early return", "switch on type", "null check everywhere", "this flag is weird".
---

# Simplifying Conditional Expressions (Refactoring.Guru set)

Make decisions explicit, shallow, and localized. Load `refactor-detect` first if unsure which category applies.

## Quick Pick

| Symptom | First choice | Combine with |
|---|---|---|
| Long boolean expression needing a comment | Decompose Conditional | Extract Variable for sub-expressions |
| Same boolean computed twice / negated versions (`if x … else !x`) | Consolidate Conditional Expression | Single source of truth for the predicate |
| Several functions share an identical guard block | Consolidate Duplicate Conditional Fragments | Extract the shared branch into one method/object |
| Loops/functions driven by booleans passed to steer them | Remove Control Flag | Break/return; parameterize if needed (`refactor-calls`) |
| Deep nested if/else inside else branches | Replace Nested Conditional with Guard Clauses | Invert + early exit until happy path is flat |
| `switch(type)` / `if type == A … elif type == B` repeated across classes | Replace Conditional with Polymorphism | Needs extracted classes first (`refactor-objects`) |
| Scattered `if (x != null)` before every use; NPE risk bandits | Introduce Null Object | Only when null means "no instance but valid behavior" |
| Preconditions buried in conditional logic mixed with policy | Introduce Assertion | Fail fast with clear error instead of silent branching |

General precondition: tests covering each branch *before* restructuring — count branches beforehand, verify all still reachable and behaving identically afterwards.

## Techniques

### Decompose Conditional
**Detect:** multi-clause boolean with operators mixed at several levels; reader must re-evaluate precedence; comment explaining it.
**Apply:** extract named predicates (Extract Variable / small methods) for each semantic clause; compose top-level expression from names so it reads like the rule's prose.
**Pitfalls:** preserve short-circuit semantics exactly (order of evaluated side-effecting calls); naming a clause that is half-truth misleads — decompose further instead.

### Consolidate Conditional Expression
**Detect:** two+ conditionals with equivalent bodies; same predicate tested positively once and negatively elsewhere; drift between copies over time.
**Apply:** create one canonical predicate (method/constant); replace every variant with calls to it, choosing sign appropriately; delete local duplicates.
**Pitfalls:** near-equivalent isn't equivalent — diff clause-by-clause before merging; one copy may encode an intentional special case.

### Consolidate Duplicate Conditional Fragments
**Detect:** same if-guard with similar body repeated in multiple methods; changing the rule means editing N places.
**Preconditions:** you can name the shared fragment's intent.
**Apply:** 1) unify the fragment into one helper returning whether-to-continue/result, or a Method Object (`refactor-methods`) for stateful cases, 2) call sites invoke the helper and keep their distinct tail behavior, 3) tests per call site.
**Pitfalls:** if tails differ significantly, consolidation creates a new God-helper — keep the shared part truly shared only.

### Remove Control Flag
**Detect:** boolean variable/param used purely to alter control flow mid-function ("flag = true … if flag break"); function becomes two mini-functions.
**Apply:** replace the flag's steering with direct structure: `break`/`return`, separate loops, or two specialized methods; parameterized behavior → Parameterize Method or Split (`refactor-calls` / `refactor-methods`).
**Pitfalls:** flags crossing threads are synchronization state, not control flow — out of scope; don't remove flags that communicate results upward unless converted to return values first.

### Replace Nested Conditional with Guard Clauses
**Detect:** pyramid of nested if/else where the interesting code sits deepest; exceptions handled after the main flow.
**Apply:** invert each condition and exit early (`if (!eligible) throw/return…`); let the remaining straight-line code be the common path; wrap happy path last.
**Pitfalls:** early exits must replicate the original cleanup/finally behavior; don't turn guard clauses into exception-spamming style for ordinary invalid input (use validation up front).

### Replace Conditional with Polymorphism
**Detect:** the *Switch Statements* smell (switch proliferation): parallel type-code switches/if-chains on a type discriminator replicated across modules; adding a type = editing everything.
**Preconditions:** a class hierarchy exists per type (else do Extract Class/Subclass first, `refactor-data` / `refactor-objects`); base has no meaningful common implementation for the varied operation.
**Apply:** declare abstract/interface method for the varied operation in the base; implement per subclass (migrating each branch); remove discriminators and factory's type-argument logic becomes plain construction.
**Pitfalls:** inverted dependency check: if the base conceptually shouldn't know the variants, consider Strategy composition (`patterns-behavioral`) instead of inheritance.

### Introduce Null Object
**Detect:** null-check-before-use scattered across many clients of a nullable collaborator; clients treat absence as fatal but should treat it as benign default.
**Apply:** create a null/substitute object implementing the interface with inert default behavior; ensure the factory never returns raw null; update contract docs; clients drop defensive checks they can rely on.
**Pitfalls:** hiding *required*-ness errors behind silent defaults masks bugs — reserve for genuinely optional collaborators; distinguish "not found" (Null Object OK) from "error state" (throw).

### Introduce Assertion
**Detect:** preconditions enforced inline mid-computation (`if (i < 0) return -1`); invariant checks buried in business conditionals; callers silently pass bad data.
**Apply:** express each precondition as an assertion at the boundary (contract check right after entry), failing fast with a descriptive error; move the business branching back to pure decision logic.
**Pitfalls:** assertions compiled out (e.g., Java `-ea` off) or stripped in release builds are *not* runtime guards — use real exception throws in production paths; avoid asserting performance characteristics that belong in tests.

## Safe application protocol
Branch-count audit → baseline tests hitting every branch → one conditional cluster per step → after each step re-run tests AND confirm no branch became unreachable → final read-through of the now-flat control flow.
