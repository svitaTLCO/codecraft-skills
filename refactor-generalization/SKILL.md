---
name: refactor-generalization
description: Detect and apply refactoring.guru "Dealing with Generalization" refactorings: Pull Up Field/Method/Constructor Body, Push Down Method/Field, Extract Subclass, Extract Superclass, Extract Interface, Collapse Hierarchy, Form Template Method, Replace Inheritance with Delegation, Replace Delegation with Inheritance. Use when a hierarchy has members in the wrong layer, siblings share code, a base class is half-useful, or inheritance fights you (Refused Bequest). Triggers: "tighten inheritance", "shared across subclasses", "base class problem", "too deep hierarchy", "composition vs inheritance here".
---

# Dealing with Generalization (Refactoring.Guru set)

Fix where behavior and data sit in a type hierarchy — neither higher than needed nor lower than shared. Load `refactor-detect` first if unsure which category applies.

## Quick Pick

| Symptom | First choice | Combine with |
|---|---|---|
| Same method body duplicated across 2+ siblings | Pull Up Method | Then Pull Up the fields it needs |
| Identical setup sequence repeated in sibling constructors | Pull Up Constructor Body | Into base constructor; keep variant tail |
| Sibling-only member inherited by classes that don't need it (Refused Bequest risk) | Push Down Method / Push Down Field | To each user, or extract to one subclass |
| Special case of an existing type deserves its own name/behavior set | Extract Subclass | Start from concrete class, move the special bits out |
| Two siblings share most of their shape but lack a common parent concept | Extract Superclass | Base = only what's *truly* shared |
| Unrelated types should be assignable/callable interchangeably | Extract Interface | Or Extract Superclass if real shared implementation exists |
| Middle layer used by almost nothing; hierarchy deeper than useful | Collapse Hierarchy | Merge parent into children; fix references |
| Siblings follow same skeleton with varying steps ("algorithm with holes") | Form Template Method | Abstract the step(s); hooks for options |
| Extending a class whose API/behavior you fight; third-party base; overriding feels illegal | Replace Inheritance with Delegation | Composition + forwarding or interface extraction |
| Delegating wrapper adds no behavior and duplicates a whole API surface | Replace Delegation with Inheritance | Only when IS-A genuinely holds |

Hierarchy health check before editing: can you state in one sentence what each level guarantees? If not, Extract Superclass/Interface to force that statement.

## Techniques

### Pull Up Field
**Detect:** same field declared in 2+ subclasses with compatible meaning.
**Preconditions:** types match; no subclass-specific initialization semantics conflict; persistence mappings update.
**Apply:** declare once in the common base; delete subclass copies; verify getters/setters resolve uniformly.
**Pitfalls:** visibility widening (field becomes visible to all descendants); serialization order/format may change per framework — run mapping tests.

### Pull Up Method
**Detect:** identical override in multiple siblings; callers go through the base type anyway.
**Preconditions:** no subclass relies on being able to re-override differently later (design intent check); behavior truly independent of subclass-specific state.
**Apply:** move implementation to base; remove overrides; keep abstract declaration if future variation expected.
**Pitfalls:** dynamic dispatch: code calling the method via a reference whose runtime type still carries the old override will change behavior — audit call graphs by static type.

### Pull Up Constructor Body
**Detect:** sibling constructors sharing long init sequences; bug fixes must be repeated per sibling.
**Apply:** factor the shared sequence into the base constructor (call it first via explicit super-call); siblings pass through their distinct inputs as parameters if needed; keep subclass-specific tail after super.
**Pitfalls:** ordering bugs (base using uninitialized subclass state) — never let base logic read subclass fields; parameter plumbing noise sometimes favors composition.

### Push Down Method
**Detect:** a base-class method makes sense only for some subclasses; others inherit dead weight or wrong defaults.
**Preconditions:** affected subclasses identified; remaining users of the method stay served (abstract or per-subclass implementations).
**Apply:** move the method into each needing subclass (copy → then specialize), or make it abstract in base and implement where needed; remove the universal version.
**Pitfalls:** external callers expecting the method on the base type break — decide whether they should actually be calling concrete types.

### Push Down Field
**Detect:** base field unused by most subclasses; Refused Bequest data.
**Apply:** move into the subclasses that use it (each gets its own copy or a shared narrower parent); update accesses; drop base storage.
**Pitfalls:** size/memory layout changes; identity/equality comparisons using the field recompute differently per subclass — test equality contracts.

### Extract Subclass
**Detect:** a class with optional features (flags, mostly-null fields) where one configuration deserves its own type (`Invoice` with `isDraft`).
**Apply:** create subclass capturing the special case; move specialized members into it; replace flags with instanceof/type selection; factory chooses construction (Replace Constructor with Factory Method, `refactor-calls`).
**Pitfalls:** flag→subclass migration touches every flag-check site; if variants are combinations of flags (cartesian explosion), model with Strategy/state objects instead (`patterns-behavioral`).

### Extract Superclass
**Detect:** similar siblings without common ancestor; clients would like a unified type.
**Apply:** create base holding ONLY verified shared members (fields/methods pulled up one at a time); point both children at it; expose base type at client boundaries only where semantics allow.
**Pitfalls:** forcing false cohesion into the base creates worse Refused Bequest than none — err on fewer, higher-quality shared members; parallel-hierarchy warning (see smell table in `refactor-detect`).

### Extract Interface
**Detect:** two hierarchies/classes offering equivalent operations clients want to treat uniformly; dependency should be on capability, not lineage.
**Apply:** declare an interface with the common operation set; have implementing types adopt it (multiple inheritance where the language allows, else refactor structure); depend on the interface at usage sites.
**Pitfalls:** interface segregation — group by *consumer* needs, not maximal overlap; breaking changes ripple to DI containers and serializers registering concrete types.

### Collapse Hierarchy
**Detect:** intermediate class with little/no unique behavior; few clients of the middle type; hierarchy depth > value.
**Preconditions:** full reference audit of the middle type (cast targets, factories, DB mappings).
**Apply:** merge middle into its single meaningful child (or promote children to top): transfer members, redirect references, delete the layer; update factories.
**Pitfalls:** removing a seam that was load-bearing for substitution (Proxy/Decorator territory) — confirm none of the collapsed layer's raison d'être is pattern-based indirection.

### Form Template Method
**Detect:** sibling algorithms share ordered steps with individual variation points; new sibling re-implements the skeleton.
**Apply:** codify the skeleton in base as a final concrete method; declare abstract/"hook" methods for variable steps; optionally define protected hooks (`beforeStep()`, default no-op) for optional variation; subclasses override only hooks.
**Pitfalls:** the inverted-control feel confuses junior readers — document the skeleton explicitly; too many hooks means the abstraction is thin (compare Form Template Method vs Strategy when steps swap wholesale: see `patterns-behavioral` comparison).

### Replace Inheritance with Delegation
**Detect:** Refused Bequest — subclass ignores/overrides most of base; base is third-party/frozen; multi-inheritance conflicts; you keep fighting initialization order.
**Apply:** stop extending; hold a delegate instance of the original type; forward only legitimately-needed operations (Hide Delegate discipline, `refactor-objects`); expose your own contract; keep an extracted interface if clients depended on polymorphism.
**Pitfalls:** forwarding boilerplate cost is real; `instanceof Base` checks and DI by concrete type break — plan boundary updates; lost automatic polymorphism requires explicit interface design.

### Replace Delegation with Inheritance
**Detect:** delegator forwards nearly the entire delegate API, adds little, and clients treat the pair as one thing; pure pass-through wrappers around your own type.
**Preconditions:** IS-A genuinely defensible in domain language (not just "convenient"); delegate isn't meant to be swapped at runtime.
**Apply:** absorb: extend the delegated type, merge members, delete the wrapper class and its forwarders; migrate references.
**Pitfalls:** swallowing indirection you'll regret later — if the wrapped object could become a different implementation someday, keep delegation (that's Adapter/Proxy intent — `patterns-structural`).

## Safe application protocol
Baseline tests per level of the hierarchy → one structural move per step (pull/push/extract/collapse separately) → after each step: compile, run hierarchy-focused tests, audit `instanceof`/cast/DI/mapping references touched → finally state the new hierarchy contract in one sentence per class and report it.
