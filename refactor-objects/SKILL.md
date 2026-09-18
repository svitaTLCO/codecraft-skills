---
name: refactor-objects
description: Detect and apply refactoring.guru "Moving Features Between Objects" refactorings — Move Method, Move Field, Extract Class, Inline Class, Hide Delegate, Remove Middle Man, Introduce Foreign Method, Introduce Local Extension. Use when logic lives in the wrong class, a class is too large or does nothing, getters/setters leak internals, message chains of `a.getB().getC()`, or pass-through wrappers clutter design. Triggers — "this method belongs elsewhere", "class too big", "feature envy", "split this object", "remove wrapper", "too many getters", "message chain".
---

# Moving Features Between Objects (Refactoring.Guru set)

Move behavior and data to where they belong — the core fix for Feature Envy, Large Class, Lazy Class, Middle Man, and Message Chains. Load `refactor-detect` first if unsure which category applies.

## Quick Pick

| Symptom | First choice | Combine with |
|---|---|---|
| Method uses another object's data more than its own | Move Method | Move Field after it |
| Group of fields + their accessors used only by some methods | Extract Class | Encapsulate Field/Self Encapsulate first (`refactor-data`) |
| Object that mostly forwards calls; one field per instance | Inline Class / Remove Middle Man | Collapse hierarchy afterwards (`refactor-generalization`) |
| Third party digs into your object's internal collaborator | Hide Delegate / Introduce Foreign Method | Prefer Foreign Method to avoid forwarding bloat |
| Same operation on an external type needed by several callers | Introduce Foreign Method | Or Introduce Local Extension for languages with extension syntax |
| Fields unused after a method move | Move Field / delete | Verify all references updated |

General preconditions: build+tests green before/after; public API changes explicitly reported; reference semantics unchanged unless intended.

## Techniques

### Move Method
**Detect:** Feature Envy — body reads far more from another object than its receiver; tests target the other object; method would be more discoverable there.
**Preconditions:** you can list every data element and helper method the body touches; each can be accessed from the new home (or will be moved).
**Apply:** 1) make needed collaborators accessible (Self Encapsulate/Encapsulate helpers), 2) move the method, adjusting `this` vs explicit references, 3) leave a forwarder at the old site until call sites are migrated, 4) remove the forwarder and any now-dead accessors.
**Pitfalls:** dropping a forwarder too early breaks polymorphic clients; moving a virtual method changes override contract — check subclasses.

### Move Field
**Detect:** a field is read/written almost exclusively through another class; getter exists but is barely called.
**Preconditions:** no code outside the two classes depends on the field's location (serialization boundaries, reflection, persistence mappings).
**Apply:** create field in destination; update all accesses; encapsulate both sides (getters); delete old field; tests.
**Pitfalls:** databases/ORMs often treat field location as part of the schema mapping — verify mapping layers before moving persistent fields.

### Extract Class
**Detect:** Large Class, Divergent Change: one class answers several unrelated questions; >~10 fields or >~5 responsibilities; name forces an "and..." description.
**Preconditions:** a coherent cluster of fields can be identified (a Data Clump); tests exist for affected behavior.
**Apply:** 1) create new class, move the clump's fields + all methods that primarily use them, 2) replace direct field access with accessors on the original, 3) migrate callers gradually (keep delegating accessors), 4) remove dead code from the source class.
**Pitfalls:** extracting without tests = highest-risk refactoring here; don't extract speculative singletons; watch circular dependencies introduced.

### Inline Class
**Detect:** Lazy Class — small class with few methods, always created together with one owner, rarely used alone.
**Preconditions:** instances never shared across owners; no identity comparisons against it; no subclassing.
**Apply:** promote its members into the containing class (prefix names to avoid clashes); convert references to plain values; delete the class; tests.
**Pitfalls:** value-object equality may carry meaning (two equal Dates ≠ same object) — if identity matters, don't inline.

### Hide Delegate
**Detect:** your class exposes an accessor returning an internal collaborator; outside code directly drives that collaborator, bypassing your invariants.
**Preconditions:** you can identify the full set of delegated operations actually used by clients (audit call sites first).
**Apply:** remove the accessor (or make it private); add narrow forwarding methods on the host class for used operations; migrate clients onto them.
**Pitfalls:** blanket-forwarding every client operation recreates Middle Man — forward only what's legitimately the host's responsibility; consider whether clients should hold the collaborator themselves.

### Remove Middle Man
**Detect:** most methods just forward to a subobject with no added validation/behavior; classic anti-corruption boilerplate.
**Preconditions:** no subclass depends on overrides of the forwarded methods; delegation isn't a seam you plan to swap (if you do → keep it, it's intentional, see patterns: Proxy/Adapter).
**Apply:** let clients talk directly to the subobject (expose via a *documented* accessor instead of hidden forwarding), or promote the subobject to top-level ownership; delete forwarders.
**Pitfalls:** in inheritance hierarchies, removing middle-man overrides severs template-method flows; deliberate indirection (Proxy/Decorator) looks identical — check pattern intent before deleting.

### Introduce Foreign Method
**Detect:** Message Chains: `customer.getAddress().getCity()` repeated everywhere; caller needs an operation conceptually owned by an object further down the chain.
**Preconditions:** the operation is meaningful for the distant object (not a hack); stable chain between caller and target.
**Apply:** define the operation *at the distant object* (e.g., `Address.getCity()` is already fine; add e.g. `Person.getHomeCity()` on Person if that's the real intent); call it directly; shorten chains above.
**Pitfalls:** adding methods to third-party classes needs wrapping (see Incomplete Library Class) or extension functions (Introduce Local Extension).

### Introduce Local Extension
**Detect:** need foreign-method-like additions in dynamic-friendly languages (Python, Ruby, JS/TS, Go interfaces+extensions style); cannot modify target type (library type).
**Preconditions:** language supports open extensions/mixins or module-level helper conventions; no conflicting same-name methods on the type.
**Apply:** implement the addition as an extension method/mixin/local helper bound to the type conventionally; document that it's not part of the original type.
**Pitfalls:** discovery problem — readers must know the extension exists; version drift when the base library changes; prefer this over monkey-patching shared library objects globally (namespace collisions).

## Safe application protocol
Baseline tests → self-encapsulate before moving → one object-boundary crossing per step → compile+test after each → verify no visibility widening was needed beyond intended → final diff review of the whole object graph touched.
