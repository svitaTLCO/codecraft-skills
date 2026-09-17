---
name: refactor-data
description: Detect and apply refactoring.guru "Organizing Data" refactorings: Self Encapsulate Field, Encapsulate Field, Encapsulate Collection, Replace Data Value with Object, Replace Array with Object, Replace Magic Number with Symbolic Constant, Change Value to Reference, Change Reference to Value, Duplicate Observed Data, Change Unidirectional Association to Bidirectional, Change Bidirectional Association to Unidirectional, Replace Type Code with Class/Subclasses/State-Strategy, Replace Subclass with Fields. Use for primitive obsession, magic numbers, naked public fields, type-code switches, value-vs-reference confusion, or awkward object associations. Triggers: "model this better", "magic number", "public field", "type code", "status int", "value or reference", "array of mixed types".
---

# Organizing Data (Refactoring.Guru set)

Restructure fields, values, and object relationships so data modeling expresses intent and protects invariants. Load `refactor-detect` first if unsure which category applies.

## Quick Pick

| Symptom | First choice | Notes |
|---|---|---|
| Primitive used where a concept exists (money as float, date as string) | Replace Data Value with Object | + Encapsulate Field on it |
| Public/mutable field, or direct `.field` access outside owner | Encapsulate Field / Self Encapsulate Field | Self-encapsulate is the prep step before moves |
| Naked collection exposed (getter returns live list/map) | Encapsulate Collection | Return copy or read-only view |
| Meaningless literal (`if (x > 3)`), repeated constants | Replace Magic Number with Symbolic Constant | Or replace enum→subclass if it branches behavior |
| Mixed-type positional array as pseudo-record | Replace Array with Object | Named slots instead of indices |
| Two references that should track one source of truth | Duplicate Observed Data | Keep single writer; invalidate cache on change |
| Need both directions of an association, only have one | Change Unidirectional Association to Bidirectional | With consistency discipline |
| Back-references cause cycles/stale pointers/hard delete logic | Change Bidirectional Association to Unidirectional | Compute the other direction on demand |
| Same-value objects compared by identity when they mean equality (or vice versa) | Change Value to Reference / Change Reference to Value | Decide semantics deliberately |
| `switch(typeCode)` deciding behavior across classes | Replace Type Code with Subclasses or State/Strategy | See decision below |
| Rare distinct subclasses each differing by one flag | Replace Subclass with Fields | Collapse over-specialization |

Decision helper for type codes: several types with different *behavior* → Subclasses; runtime state machine of one object → State/Strategy; static config difference → plain field/class constant.

## Techniques

### Self Encapsulate Field
**Detect:** a field is accessed directly from other methods/classes and you plan to move/extract it.
**Apply:** add getter (and setter only if needed); redirect all in-class accesses through the accessor; leave external API unchanged.
**Pitfalls:** purely mechanical but must be total — grep every `this.field`; performance-neutral in practice, don't micro-bench getters.

### Encapsulate Field
**Detect:** field is public (or language-exposed) and mutated by many callers; invariant violations possible.
**Apply:** make field private; expose getter; add setter with validation *only for states callers actually need*; migrate mutating call sites; keep the old assignment shape working nowhere else.
**Pitfalls:** removing setters breaks frameworks (ORMs, serialization libs may require no-arg visibility) — check binding layers; consider Remove Setting Method (`refactor-calls`) if setters take arbitrary values.

### Encapsulate Collection
**Detect:** getter returns the live internal collection; callers can add/remove/reorder elements.
**Apply:** return a defensive copy or immutable view; add intent-named operations (`addIngredient`, `removeAt`) on the owning class for legitimate modifications.
**Pitfalls:** copies cost memory/time for large collections — use unmodifiable wrappers where supported; document which operations are intended.

### Replace Data Value with Object
**Detect:** Primitive Obsession — `float price`, `string email`, `int status = 2`; validation duplicated at every write site; units hidden.
**Preconditions:** tests pin down current parsing/validation behavior.
**Apply:** create a small class wrapping the primitive with constructor-time validation and semantic methods (`price.addTax()`); replace the field's type; migrate reads/writes; delete ad-hoc validators scattered elsewhere.
**Pitfalls:** value objects should be immutable and cheap; persistence/serialization may need mapping; equality/hashcode updated.

### Replace Array with Object
**Detect:** arrays/lists used positionally with mixed meanings (`parts[0]`=name, `parts[1]`=qty) or index-based access with comments explaining positions.
**Apply:** introduce an object/struct with named properties; update all indexed accesses to named ones; remove index constants.
**Pitfalls:** external contracts (APIs, files, queues) may truly be positional — the *internal* representation changes; keep boundary mappings explicit.

### Replace Magic Number with Symbolic Constant
**Detect:** numeric/string literals whose meaning needs a comment to decode; the same literal repeated.
**Apply:** declare a named constant near its domain (UPPER_CASE name); replace all occurrences; group related constants into an enum/namespaced module.
**Pitfalls:** naming by value (`MAX_100`) encodes accidents, not intent — name by role (`RETRY_LIMIT`); zero/one often fine inline (loops, initializers).

### Change Value to Reference
**Detect:** two "equal" instances that should be *the same thing* (two open handles to one connection; two Price objects that should sync); currently duplicating mutable shared state.
**Apply:** centralize a single instance (registry/factory/cache keyed by identity key); hand out references; remove duplicated copies.
**Pitfalls:** introduces sharing hazards (concurrent mutation, lifetime) — protect with immutability or synchronization; serialization now emits references.

### Change Reference to Value
**Detect:** objects passed around but always copied/compared structurally; accidental coupling to a long-lived instance; identity surprises (changing one changes everyone).
**Apply:** make the type immutable/value-based (copy-on-read already true), drop shared caches, compare by structure; if heavy, store copies at point of use.
**Pitfalls:** loses cheap sharing (Flyweight territory — see `patterns-structural`); identity checks (`===`, pointer equality) must become structural comparisons.

### Duplicate Observed Data
**Detect:** same fact stored/derived independently (client-side copy of server's balance; cached price) — acceptable only with a defined invalidation rule.
**Apply:** pick the authoritative source; tag duplicates clearly as derived/cached; wire invalidation (refresh on observed change or TTL); assert drift in tests.
**Pitfalls:** undocumented duplicates silently rot — without an invalidation contract, prefer Remove middle-man data paths instead.

### Change Unidirectional Association to Bidirectional
**Detect:** traversing A→B and separately looking up B→A via maps/scans repeatedly; navigation feels slow or awkward.
**Preconditions:** you can guarantee consistency of both links (creation/deletion updates both).
**Apply:** add reverse field on B; maintain both sides in constructors/factories and mutators; encapsulate link mutations behind operations.
**Pitfalls:** consistency bugs are the classic failure — enforce via a single `link/unlink` operation; watch circular references during disposal/serialization (weak refs, cycle breakers).

### Change Bidirectional Association to Unidirectional
**Detect:** back-references going stale; hard-to-delete graphs; serialization cycles; "forgot to clear parent" bugs.
**Apply:** remove the reverse field; compute the direction on demand (search, indexed query, event recompute); optimize later with a *cached* (observed) duplicate if needed.
**Pitfalls:** naive on-demand lookup can be O(n·m) hot — benchmark before shipping if traversal-heavy.

### Replace Type Code with Class
**Detect:** type code (enum/int) attached to data, validation of legal values done everywhere, some behavior depends on it but lives in the host.
**Apply:** extract a class per code (or one parameterized class holding the code) with the associated behavior; host holds the class; switch-sites start delegating.
**Pitfalls:** intermediate step toward Subclasses/State — decide end-state first to avoid double migration.

### Replace Type Code with Subclasses
**Detect:** stable closed set of types, each with clearly different behavior; switches on the code appear in multiple places.
**Preconditions:** adding new types can wait for a compile-break (i.e., new type = new class is acceptable); tests per existing type.
**Apply:** introduce base interface/abstract class; create a subclass per code migrating its switch arms into overridden methods; factory replaces `new Host(code)` (Replace Constructor with Factory Method, `refactor-calls`).
**Pitfalls:** hierarchy explosion with rare variants (use Replace Subclass with Fields / State instead); persisted type codes need mapping tables.

### Replace Type Code with State/Strategy
**Detect:** open or frequently changing set of behaviors; one object's behavior varies by mode at runtime; new type means touching many switch statements.
**Apply:** define an interface for the varying behavior; implement one strategy/state object per code; host holds a reference and delegates; construction swaps implementations (Factory or registry). Runtime-mutable modes → State (self-swapping states); swappable policies → Strategy.
**Pitfalls:** don't pattern-ify a 2-value bool (YAGNI); context must own what stays invariant; see `patterns-behavioral` for full shapes.

### Replace Subclass with Fields
**Detect:** subclasses differing only by constructor flags or 1–2 overridden getters; variant count exceeds meaningful behavioral splits; new "variant" is really a configuration.
**Apply:** remove the subclasses; promote distinguishing flags to fields on a single class; replace polymorphic dispatch with a few conditionals or a field-driven lookup table; update factories to configure instead of choose class.
**Pitfalls:** conditional bloat is the trade-off — if conditionals multiply past ~4 decision points, you misdiagnosed; go back to Subclasses/State.

## Safe application protocol
Baseline tests → encapsulate before you model (Self Encapsulate/Encapsulate Field) → one data-boundary change per step → verify invariants (persistence mapping, equality, concurrency) after each → report any public data-model change explicitly.
