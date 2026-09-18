---
name: patterns-creational
description: Detect and apply refactoring.guru creational patterns — Factory Method, Abstract Factory, Builder, Prototype, Singleton. Use when object creation is tangled into clients, constructors leak configuration, product families must stay consistent, objects are expensive to clone/copy, or an uncontrolled "one instance" is needed. Triggers — "how should I create these objects", "construction is a mess", "fluent builder", "clone this", "shared config everywhere", "DI container keeps making duplicates".
---

# Creational Patterns (Refactoring.Guru set)

Decouple *where/how* objects come into existence from *where they're used*. Load `patterns-detect` first if unsure whether a pattern applies at all.

## Quick Pick

| Situation | Pattern | Not this if |
|---|---|---|
| Clients shouldn't name concrete product class; one product type varies by env/params | Factory Method | A family of coordinated products varies → Abstract Factory |
| Must keep related product sets consistent across platforms/builds | Abstract Factory | Only one kind of product varies → Factory Method |
| Construction needs many optional/ordered steps; parameter explosion; staged config | Builder | Construction is 2-3 simple args → plain constructor + defaults |
| Duplicating an existing configured object graph is cheaper than rebuilding | Prototype | Fresh objects are cheap/stateless → just construct |
| Exactly one instance must exist & be shared (and misuse = multiple instances) | Singleton — reluctantly | You can inject the instance explicitly (usually you can) |

## Techniques

### Factory Method
**Intent:** define a creation interface; let subclasses decide which class to instantiate. Calls refer to the operation, not `new Concrete()`.
**Detect:** `new X(params)` scattered in client code where X should depend on environment/config; adding a variant forces editing every construction site; tests want to swap implementations.
**Avoid:** trivial products with fixed construction (constructor suffices); more than ~4 variants each needing unique logic (consider registry/factory-with-strategy); languages without easy subclassing for the creator role (use named factory functions instead).
**Shape:**
```
Product (interface)
Creator { createProduct(): Product }          // static/instance method — the seam
ConcreteCreatorA { createProduct() → ProductA }
```
**Apply:** 1) extract product interface from existing class, 2) move `new` into a factory method (on creator class, static function, or base-class virtual), 3) replace direct constructions with factory calls, 4) point tests/DI at alternative creators.
**Pitfalls:** naming — factories returning the same base type across siblings need distinct names (`createLogger` vs `createDatabaseHandle`); don't build deep creator hierarchies mirroring product ones unless real (that drift leads toward Abstract Factory territory).

### Abstract Factory
**Intent:** produce *families* of related/dependent products through one interface, guaranteeing compatibility (e.g., GUI widgets for Windows vs macOS; ORM drivers for Postgres vs MySQL).
**Detect:** several product interfaces that must vary *together*; mixing A-family with B-family produces broken combos; a "platform"/"vendor" dimension running through construction.
**Avoid:** products independent of each other (plain Factory Method per product); only two products ever (a paired-factory function suffices); runtime mix-and-match desired (factories imply consistency).
**Shape:**
```
AbstractFactory { createA(): A; createB(): B }
ConcreteFactoryX { → AX, BX }   // compatible set
ConcreteFactoryY { → AY, BY }
```
**Apply:** 1) identify the family dimension (what must stay consistent), 2) declare product interfaces per member, 3) implement one concrete factory per family, 4) inject/select the factory at composition root only; components receive products via their interfaces, never factories directly (or use lazy factory handles if products materialize late).
**Pitfalls:** family growth = combinatorial new factory per combination — accept that as the cost of consistency; exposing factories throughout your codebase defeats the decoupling; version-mismatched product families slipping in from different factory generations is the classic bug — validate coherence at injection time.

### Builder
**Intent:** separate construction of a complex object from its representation so the same process builds different representations.
**Detect:** telescoping constructors (overloads for every option combo); long mutable setters called in sequence with possible mis-ordering; multi-stage construction (validate → build → finalize); API with 8+ parameters.
**Avoid:** 2–3 mandatory fields, no options (constructor wins); immutable value objects with few properties; when users actually want free-form partial state (builder implies completed-product semantics).
**Shape:**
```
Builder { setRequired(...); addOptional(...); step(); build() → Product }
Director (optional) { standardBuild(b) / specialBuild(b) }  // ordered recipes
```
**Apply:** 1) make the product's constructor package-private/restricted, 2) implement a builder with fluent methods enforcing presence of required parts in `build()` (fail fast with clear errors), 3) add directors only when *ordered recipes* are reused, 4) migrate call sites bottom-up.
**Pitfalls:** builders returning `this` on mutators enable misuse chains (`b.a().c().a()` again) — decide immutability-of-builder-policy deliberately; serializing builders leaks internals; prefer separate directed builders over one mega-builder with 30 optional methods (split per recipe).

### Prototype
**Intent:** clone an existing object instead of reconstructing, often after customization.
**Detect:** expensive initialization data (loaded configs, loaded trees/graphs, DB-seeded structures) reused with small deltas; object graphs too costly to rebuild per variation.
**Avoid:** shallow-copy-only languages pretending deep structure is copied (prototype clones share nested references — clone recursively or by copy-constructor); objects with resources needing explicit ownership transfer (file handles, sockets); flat fresh-state cases (constructor is simpler and safer).
**Shape:**
```
Prototype { clone(): Self }
ConcreteProto { clone(): copy(self) /* deep where needed */ }
Client registers prototypes; gets customized copies
```
**Apply:** 1) audit what truly needs deep copying vs reference sharing, 2) implement clone doing deep copy of owned substructure, 3) keep an archetype/catalog of base prototypes, 4) register new prototypes instead of `new`ing inline; customize returned copies.
**Pitfalls:** identity-dependent features (equality caches, registries keyed by object identity) break on clones; forgotten deep-copy of one nested field is the #1 correctness bug; cloning across threads requires synchronization of the source during copy.

### Singleton
**Intent:** guarantee exactly one instance of a class with a global access point.
**Detect:** users keep creating duplicate instances of something that must be shared (connection pools, thread pools, hardware handles); a God-service being hand-wired everywhere with mismatched configs.
**Avoid:** testability-critical paths (hidden global state wrecks unit tests — prefer DI); the dependency could be injected naturally (always possible unless you're inside a library boundary); lazy-vs-eager lifetime ambiguity matters (pick consciously).
**Shape:**
```
class S {
  private static let instance = ...      // or thread-safe init
  public static func shared() -> S { return instance }
  private init() {}
}
```
**Apply:** 1) make construction inaccessible (private ctor), 2) provide one well-defined access (lazy holder, eager static, language idiom — Rust `OnceLock`, Go var+mutex, Java enum singleton for serialization-safety), 3) replace ad-hoc constructions with the accessor, 4) document what it owns and its lifecycle.
**Pitfalls:** hidden coupling makes refactors and tests hard — treat every Singleton as a smell you're consciously accepting; serialization/deserialization can spawn second instances (Java: readResolve; or forbid); static-init ordering across modules; "singleton per context" (per-request scope) is NOT Singleton — model scopes explicitly (registry keyed by scope).
