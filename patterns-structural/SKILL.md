---
name: patterns-structural
description: Detect and apply refactoring.guru structural patterns: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy. Use when integrating incompatible/legacy interfaces, decoupling two varying dimensions, modeling part-whole trees, adding features without subclass explosion, simplifying a complex subsystem's surface, saving memory on massive similar objects, or controlling access to a subject (lazy loading, caching, auth, remote/large objects). Triggers: "wrap this legacy API", "incompatible interface", "tree of nodes", "add behavior dynamically", "simplify these 30 classes", "memory blowup with many objects", "auth/cache/lazy around X", "facade around a subsystem", "convert this adapter/decorator/proxy".
---

# Structural Patterns (Refactoring.Guru set)

Restructure *relationships* between objects — composition, adaptation, indirection — without changing their fundamental responsibilities. Load `patterns-detect` first if unsure whether a pattern applies at all.

## Quick Pick

| Situation | Pattern | Kill switch (don't use) |
|---|---|---|
| Existing class has wrong interface; you can't/can't touch it (legacy, third-party) | Adapter | You own both sides → just refactor the interface |
| Two independent axes of variation creating matrix of subclasses (OS × widget, driver × protocol) | Bridge | Only one axis varies → plain Factory/polymorphism |
| Parts form a tree; clients should not special-case leaf vs branch | Composite | Flat structure or fixed depth (2 levels fine without it) |
| Features must combine dynamically/orthogonally; sibling-per-feature blows up | Decorator | Fixed small feature set → inheritance or config flag |
| Subsystem exposes dozens of classes; client needs 4 operations | Facade | Client legitimately uses most internals directly |
| Thousands of near-identical objects; memory dominated by shared data | Flyweight | Objects cheap; distinct parts don't factor cleanly |
| Need controlled ACCESS to existing subject: lazy creation, caching, permission checks, large-object/remote stand-in, audit hooks | Proxy | Direct access fine; access concerns trivial |

## Techniques

### Adapter
**Intent:** convert an existing interface into one clients expect, making incompatible classes cooperate.
**Detect:** legacy/third-party API with working behavior but wrong shape; wrapping a callback-style API behind clean methods; bridging sync↔async boundaries.
**Avoid:** when you control the source interface (fix it instead); adapting across layers repeatedly (each hop multiplies wrappers — flatten); adapters that also add behavior (that drift becomes Decorator/Proxy territory).
**Shape:**
```
Client expects Target { operation() }
Adapter : Target { wraps Adaptee: operation() → adaptee.specificRequest() }
```
**Apply:** 1) name the target interface from the *client's* vocabulary, 2) implement adapter wrapping the adaptee (by composition), translating inputs/outputs/error semantics explicitly, 3) swap clients to the target, 4) keep adapters thin — mapping code only.
**Pitfalls:** silent semantic loss in translation (units, encodings, error→exception mapping, default values); circular adapters (A adapts B, B adapts A); object adapters (wrap instance) are usually cheaper than class adapters (subclassing) — prefer the former unless multiple inheritance is available and clean.

### Bridge
**Intent:** decouple abstraction from implementation so both vary independently along separate dimensions.
**Detect:** 2×N (or N×M) grid: e.g., RemoteDocument interface implemented locally and remotely, each with PDF/Word variants → 4+ classes where 2 concepts suffice; "every new platform re-implements every feature" hierarchy.
**Avoid:** implementations rarely vary (abstraction-only suffices); the two dimensions aren't genuinely orthogonal; language lacks clean pointer/reference abstraction for the implementee.
**Shape:**
```
Abstraction { impl: Implementor; request() → impl.operate() }
RefinedAbstraction : Abstraction { extra behaviors built on impl }
Implementor { operate(): base op; altOperate(): variant }
ConcreteImplX / ConcreteImplY : Implementor
```
**Apply:** 1) extract the interface of the implementation (Implementor), 2) move concrete implementations out of the hierarchy into their own line, 3) make the abstraction hold a reference (not superclass) to an Implementor, 4) refine abstractions for higher-level behavior composing Implementor ops, 5) construct pairs at injection points.
**Pitfalls:** everything-through-interface cost (virtual dispatch per call — profile hot paths); over-abstracting makes simple cases confusing (Bridge for one dimension = Factory + composition already); leakage when RefinedAbstraction needs impl-specific details it shouldn't know (interface split signal).

### Composite
**Intent:** compose objects into tree structures; treat individual and composites uniformly.
**Detect:** recursive part/whole models (file systems, org charts, UI node trees, expression trees); client code full of `if node.isLeaf()` branches; adding container types breaks callers.
**Avoid:** non-recursive structures (flat lists of mixed types → sealed union or tagged enum); shallow 2-level cases; when leaves and branches genuinely need different APIs everywhere (uniformity is theater then).
**Shape:**
```
Component { operation(); child management API optional }
Leaf : Component { terminal behavior }
Composite : Component { children: [Component]; recurse }
```
**Apply:** 1) define Component as the union of what clients actually do (keep it narrow — Iterator segregation matters), 2) implement Leaf straightforwardly, 3) implement Composite delegating/recursing to children, guarding invalid child ops (empty list, read-only tree), 4) migrate client branches off type-checks onto uniform calls.
**Pitfalls:** exposing child-management API on every component (leaves silently accepting `addChild`) — decide safe-failure loudly (throw) or hide mutators in a narrower interface; deep-tree recursion limits (stack overflow → iterative traversal); security: untrusted serialized trees can encode cycles/depth bombs — validate on load.

### Decorator
**Intent:** attach responsibilities to objects dynamically, individually, via composition; features stack.
**Detect:** cross-cutting additions (logging, caching, retry, compression, scroll+resizable+bordered UI element); inheritance tree producing one subclass per feature combination; runtime enable/disable of capabilities.
**Avoid:** features are mutually exclusive states (that's State — `patterns-behavioral`); one or two known additions forever (explicit method/flag simpler); decorators changing identity-critical behavior clients rely on transparently.
**Shape:**
```
Component { op() }
Decorator : Component { c: Component; op() → wrap(c.op()) }
LoggingDecorator, CachingDecorator, RetryDecorator ...
subject = Retry(Cache(Logging(core)))
```
**Apply:** 1) start from a stable component interface (the seam), 2) write base decorator forwarding everything while intercepting its concern, 3) implement each concern decorator keeping *one* responsibility per class, 4) document ordering semantics (which layer wins), 5) assemble at composition point, passing the same type out to clients.
**Pitfalls:** unwieldy constructor chains — factory/builder helpers for assembly (see Builder, `patterns-creational`); ordering-dependence bugs (cache-before-retry ≠ retry-before-cache — state which you guarantee); long chains obscure the core (cap practical depth ~3–5); identity checks (`===`, locks keyed on object) break through layers unless documented.

### Facade
**Intent:** provide a unified simplified interface to a complex subsystem, without modifying the subsystem.
**Detect:** clients wiring 8+ collaborator classes for one user-facing operation; onboarding docs longer than the feature; subsystem changed internally and broke 20 client files.
**Avoid:** subsystem is genuinely used piecemeal (clients need fine-grained control — facade hides that capability); you're tempted to build a façade to force migration away from old direct usage (plan the retirement deliberately); "god service" anti-facade accumulating all app concerns.
**Shape:**
```
Facade { init(a, b, c...) once; highLevelOp1(); highLevelOp2() }
subsystem internals remain accessible for advanced cases (optionally)
```
**Apply:** 1) enumerate the 3–6 operations users truly perform, 2) implement facade orchestrating the subsystem (construct/hold collaborators internally), 3) expose high-level entrypoints; optionally keep a documented escape hatch for power users, 4) migrate common clients first, 5) let low-level API shrink over time as adoption proves itself.
**Pitfalls:** facades accrete into Second God Class (review scope creep); bypassing the facade for one edge case normalizes direct use — either support it visibly or refuse it clearly; facades over microservices multiply round-trips (batch operations inside).

### Flyweight
**Intent:** share bulk quantities of similar fine-grained objects by splitting intrinsic (shared) vs extrinsic (per-use) state.
**Detect:** object counts in the thousands/millions where identical data dominates memory (board game pieces, rendered glyphs, tree nodes of same species); GC pressure from near-duplicate instances.
**Avoid:** distinct state dominates per object; counts modest (thousands of small objects fine); sharing would create surprising aliasing in a domain where objects feel individually owned.
**Shape:**
```
Flyweight { intrinsicState; operation(extrinsicState) }
FlyweightFactory { cache: map(key → shared) ; get(k) → shared-or-create }
Client holds key + extrinsic data, asks factory for shared core
```
**Apply:** 1) profile: quantify duplication and savings before building anything, 2) partition state into intrinsic (value-equal ⇒ shareable) vs extrinsic (passed at operation time), 3) build immutable intrinsic core + interned factory/cache (weak refs if lifetimes matter), 4) refactor operations to receive extrinsic parameters, 5) verify aliasing-safety: no mutation of shared cores under any path.
**Pitfalls:** accidental mutation of shared intrinsic state corrupts everyone using that key (top risk — enforce immutability); bookkeeping overhead (factory lookups) exceeds savings at low cardinality — measure again post-change; GC may defeat interning in managed languages (benchmark real heap, not theory).

### Proxy
**Intent:** control access to a subject: a substitute managing *when/how* the real thing is reached, same interface.
**Detect:** expensive construction needing lazy creation (DB session, parser for huge input); remote object behind stub; cached results guarding costly computation; authorization/audit wrapper before privileged service; large-object virtual scrolling (load pages on demand).
**Avoid:** access policy changes frequently enough to justify explicit middleware/handler; wrapping everything because "indirection feels good" (measure); subject must be swappable freely (that's Strategy/decoration intent, or a DI seam).
**Shape:**
```
Subject { op() }
RealSubject : Subject
Proxy : Subject { real?: RealSubject;
  op() → guard/auth/lazy-init/cache, then delegate(real?.op() ?? create-real-op()) }
```
**Apply:** 1) choose proxy subtype by need (Lazy / Virtual / Protection / Remote / Caching — often hybrids), 2) implement the guard logic *before* delegation (cheap checks first: permissions, presence of cache hit), 3) manage lifecycle of the real subject (dispose, connection close) in the proxy, 4) keep the same public interface so clients stay oblivious; log/access policies configurable, not hardcoded.
**Pitfalls:** double-initialization races for lazy proxies (thread-safe init required); proxy holding subject after release (lifetimes: who owns disposal? decide and document); exception paths leaking proxy state (failed op leaving half-initialized real); transparent proxies hiding *why* latency appeared (profile distinguishes proxy overhead from real work); recursion via self-proxy loops (proxy of proxy of subject) — bound them explicitly.
