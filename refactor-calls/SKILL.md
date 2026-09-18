---
name: refactor-calls
description: Detect and apply refactoring.guru "Simplifying Method Calls" refactorings — Rename Method, Add Parameter, Remove Parameter, Separate Query from Modifier, Parameterize Method, Replace Parameter with Explicit Methods, Preserve Whole Object, Replace Parameter with Method Call, Introduce Parameter Object, Remove Setting Method, Hide Method, Replace Constructor with Factory Method, Replace Error Code with Exception, Replace Exception with Test. Use when function names mislead, signatures carry noise, bool/int parameters encode choices, side effects hide in getters, or error handling uses magic codes. Triggers — "rename this", "bad parameter", "bool arg", "get mutates state", "too many call sites differ by one arg", "error code", "factory instead of new".
---

# Simplifying Method Calls (Refactoring.Guru set)

Make the *interface* between callers and functions honest: names match behavior, parameters carry meaning, results/errors are unambiguous. Load `refactor-detect` first if unsure which category applies.

## Quick Pick

| Symptom | First choice | Combine with |
|---|---|---|
| Name describes what it does, not why/what-it-is; verb inconsistent with effect | Rename Method | Get ahead of every other fix — cheap and clarifying |
| Function needs extra data from caller it currently lacks | Add Parameter | Or Replace Parameter with Method Call / Preserve Whole Object |
| Parameter is always the same value at all/most call sites | Remove Parameter | Check for hidden coupling removed along with it |
| Getter/setter performs work; a "query" changes state | Separate Query from Modifier | Split into pure accessor + named mutation |
| Same function with only one argument varying across N call sites | Parameterize Method | Or Replace Parameter with Explicit Methods |
| Bool/enum parameter selects among distinct behaviors (`format(useXml)`) | Replace Parameter with Explicit Methods | One clear name per behavior |
| Passing 4 fields separately that always come from the same object | Preserve Whole Object | Or Extract Class so they live together (`refactor-objects`) |
| Caller must compute an expression just to pass a standard input | Replace Parameter with Method Call | Push the fetch inside the callee |
| 3+ related parameters forming a clump; signature keeps growing | Introduce Parameter Object | With Self Encapsulate on each member |
| Setter used once by frameworks/tests but accepts any junk | Remove Setting Method | Make constructor-required or factory-created |
| Public method exists only for legacy subclasses/frameworks | Hide Method | Demote to protected/private after auditing overrides |
| `new Foo(...)` forces ugly init sequence; creation logic leaks into callers | Replace Constructor with Factory Method | Abstract Factory territory if families involved (`patterns-creational`) |
| Returns `-1`/`false`/magic ints for failure; callers ignore them | Replace Error Code with Exception | Define real error types per failure class |
| Hot path pays exception cost for expected conditions (validation in tight loops) | Replace Exception with Test | Pre-check with a query before the operation |

## Techniques

### Rename Method
**Detect:** comment next to the call explaining what it really does; name implies purity but body mutates; verb doesn't match tense/effect.
**Preconditions:** full reference search (including reflection/string-based lookups); no external contract pinned to the name (APIs, RPC).
**Apply:** rename everywhere mechanically; keep names revealing: verbs for commands (`calculateDiscount`), nouns/adjectives for queries (`isEligible`); update docs/examples touched.
**Pitfalls:** half-renamed call graphs confuse readers more than old names; rename the *entire* concept coherently (related constants/classes too).

### Add Parameter
**Detect:** function reaches for ambient state/config/global it should receive explicitly; two callers need different values.
**Preconditions:** every call site can supply the new value (audit before committing).
**Apply:** add parameter with sane default where the language supports it; migrate call sites from least to most critical; delete the ambient access.
**Pitfalls:** long-parameter-list drift — >~4 params means stop and reach for Introduce Parameter Object.

### Remove Parameter
**Detect:** constant-valued argument; value derivable from receiver; duplicated information in two params.
**Preconditions:** confirm derivation/source is available at the callee for *every* caller (not just local ones).
**Apply:** inline the source (hardcode constant, fetch internally, derive from another param); update all call sites; simplify wrappers that existed only to forward the param.
**Pitfalls:** some "constant" callers differ in tests/environments — capture those before deleting the escape hatch.

### Separate Query from Modifier
**Detect:** "getter" or seemingly-pure read with side effects (lazy load, caching write, logging as only effect, validation throws on read).
**Preconditions:** consumers of the data and consumers of the side effect can be distinguished (often yes: auditable).
**Apply:** split into a pure query returning data and an explicit modifier performing the change; migrate callers by intent.
**Pitfalls:** lazy initialization masquerades as side effect — decide deliberately whether read-triggered creation is wanted (if yes, document it; if no, make it explicit init).

### Parameterize Method
**Detect:** duplicate methods differing by one literal/expression; near-identical blocks with a small constant swap.
**Apply:** extract shared body into one method taking the varying element(s); replace twins with calls; if variants grow beyond naming sanity, Replace Parameter with Explicit Methods.
**Pitfalls:** parameterized method whose only "parameter" varies in ways that need documentation becomes less readable than the pair — prefer explicit methods for semantically distinct cases.

### Replace Parameter with Explicit Methods
**Detect:** bool/flag/switch-arg: `transfer(amount, isUrgent)`, `draw(format=2)`; call sites read like config lines.
**Apply:** create one method per meaningful option (or per common combination) delegating to a shared private core; migrate call sites to readable names.
**Pitfalls:** combinatorial explosion when options multiply (≥4 independent switches) — model the options (Replace Data Value with Object, `refactor-data`) instead.

### Preserve Whole Object
**Detect:** caller passes several members of the same object (`foo.getA(), foo.getB()`); the object exists elsewhere and will likely gain relevant members.
**Apply:** change the callee to accept the object; have it access needed members itself (encapsulating its own reads); update call sites to pass the object.
**Pitfalls:** creates dependency on a larger interface than needed — acceptable trade-off vs data-clump drift; watch for introducing cycles.

### Replace Parameter with Method Call
**Detect:** every caller computes the same value right before calling (`fn(obj.computeX())`); parameter is redundant given the receiver.
**Preconditions:** computation has no meaningful side effects (or is fine moving inside); receiver always non-null.
**Apply:** remove the parameter; callee invokes the producing method on the receiver (or a passed collaborator); update call sites.
**Pitfalls:** subtle if the precomputed value came from a *different* instance than the receiver — check identity carefully.

### Introduce Parameter Object
**Detect:** Long Parameter List / Data Clumps: ≥3 related params; pairs repeating across methods; order-swapping bugs (`a,b` vs `b,a`).
**Preconditions:** the clump's elements share conceptual ownership (testable by whether you'd give them one name).
**Apply:** create the parameter class (immutable preferred); Self Encapsulate each field (`refactor-data`); swap signatures; callers construct one object.
**Pitfalls:** don't create a parameter object spanning unrelated values (forces fake cohesion); binary/API boundaries may forbid struct changes — version the boundary instead.

### Remove Setting Method
**Detect:** setter whose only real consumer is framework plumbing; allows invalid states; enables arbitrary post-construction reconfiguration.
**Preconditions:** legitimate mutation paths identified (none → constructor/factory only; some → keep narrowed operations).
**Apply:** delete the generic setter; route through constructor, factory, or purpose-named mutations (`markPaid()`, not `setStatus(2)`); fix remaining clients.
**Pitfalls:** reflection-based frameworks (DI, ORM, mapping libs) may require setters or field injection — check before removal.

### Hide Method
**Detect:** public method effectively used only within package/subclass; exposure invites misuse and future lock-in.
**Preconditions:** exhaustive call-site + override audit (including dynamic dispatch, serialization annotations).
**Apply:** lower visibility stepwise (public→protected→private/internal); if only inheritance needed it, keep protected; delete if fully internal-only.
**Pitfalls:** virtual methods called via base references from other modules stay public-visible even if "unused" locally — audit by base-type usage.

### Replace Constructor with Factory Method
**Detect:** constructors overloaded with alternatives; creation involves branching/caching/lookup; subclass selection by type code.
**Apply:** introduce static/named factory accepting simpler inputs, returning the type (possibly a subclass); migrate call sites; make constructors restricted; factory hides allocation decisions.
**Pitfalls:** factories return base types — casts proliferate unless design intends polymorphism; naming discipline essential (`createDraftInvoice` vs `create` overload soup).

### Replace Error Code with Exception
**Detect:** magic failure sentinels (-1, NULL, false-as-error) mixed with valid values; unchecked errors; layered code copying the same `if (err == -1)` dance.
**Preconditions:** failure classes distinguishable (I/O vs validation vs not-found…) and callers able to react differently.
**Apply:** define exception hierarchy mirroring failure taxonomy; throw at the origin with context (values, ids); catch at layer boundaries; convert residual sentinel returns as you touch them.
**Pitfalls:** exception volume explodes if used for ordinary flow (use Replace Exception with Test there); never swallow silently — each catch either handles, logs with context, or rethrows.

### Replace Exception with Test
**Detect:** exceptional condition is actually *expected* (validation, probing existence, capacity checks) and exceptions are thrown/handled in hot paths.
**Apply:** provide a query/test method answering the question cheaply (`canWithdraw(amount)`, `exists(id)`); perform it before invoking the throwing operation; keep the exception for true anomalies.
**Pitfalls:** check-then-act races under concurrency — if mutable state intervenes, keep the throwing form and handle it; don't double-validate expensive preconditions repeatedly.

## Safe application protocol
Baseline tests incl. error-path coverage → one signature family at a time → compile-driven migration (let the compiler find call sites) → verify error semantics unchanged (same failures, better surfaced) → report every public API change to the user.
