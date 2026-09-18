---
name: patterns-detect
description: Analyze a user query and design to detect which refactoring.guru design pattern applies, then guide its application. Master entry point for all 22 GoF patterns in three families (creational — Factory Method, Abstract Factory, Builder, Prototype, Singleton; structural — Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy; behavioral — Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor). Use when the user asks "which pattern fits" without naming one, describes adding variants that force switch changes, complains about rigid coupling between objects, or needs controlled creation/configuration. If the query already names a GoF pattern or matches a family's symptoms, load that family skill directly instead. Triggers — "design pattern", "which pattern should I use", "too coupled", "plugin architecture".
---

# Patterns Detect (Refactoring.Guru set — router)

Detect the *structural problem* behind the user's request, classify it into a family, pick the pattern, and verify the fit before any code is written. Patterns are solutions to named design problems — not labels to decorate new code.

## Step 0 — Anti-overengineering gate

Before classifying, require at least ONE concrete evidence item:
- A real second/third variant already exists or is imminent (not hypothetical), OR
- The same change keeps forcing edits across multiple files (Shotgun Surgery), OR
- A coupling violates an actual constraint (performance, lifecycle, security boundary), OR
- The user explicitly asked for the pattern as a requirement.
If none holds, say so plainly: prefer the simpler construct (direct construction, plain methods, simple interfaces). A pattern added for a problem that doesn't exist is dead abstraction (Speculative Generality smell).

Also check the cheap alternatives first:
- Can an interface + a few implementations (no ceremony) solve it? → stop, that's enough (essentially Strategy-lite / Replace Conditional with Polymorphism territory — `refactor-conditionals`).
- Is the ask really local ugliness? → use the `refactor-*` skills instead of a pattern.

## Step 1 — Intake: what is actually varying/fixed?

Extract from the query + code:
1. **What object is awkward?** (how it's created / how it's built / whether it must be unique) → creational pressure.
2. **How are these objects related?** (composition of incompatible parts, trees, layered features, huge substructure memory, need for indirection/caching/authorization/lazy loading around an existing subject) → structural pressure.
3. **How do they talk/behave?** (algorithms swapping at runtime, state machines, many small messages crossing two objects, undo, iteration over containers, notification fans, operation dispatch on varied type hierarchies, request pipelines) → behavioral pressure.
4. **What must stay stable vs change often?** Name the seam. If you can't name the seam, stop and gather evidence again.

## Step 2 — Classification decision tree

```
Does the pain concern CREATING objects?
├─ Yes
│   ├─ One product, complex construction steps (optional parts, ordered builds, shared config)?        → Builder
│   ├─ One product with variants chosen by parameters/subclasses, clients shouldn't name concrete classes? → Factory Method
│   ├─ FAMILIES of related products (A1-B1-C1 or A2-B2-C2) must stay consistent?                     → Abstract Factory
│   ├─ Costly graph/tree to duplicate partially?                                                    → Prototype
│   └─ Exactly one configured instance needed everywhere (and users keep inventing their own)?      → Singleton
└─ No: does the pain concern how OBJECTS COMBINE / are RELATED?
    ├─ Yes
    │   ├─ Two existing incompatible types must interoperate (legacy/third-party API)?               → Adapter
    │   ├─ Implementation varies along TWO independent dimensions (platform × feature)?             → Bridge
    │   ├─ Part-whole hierarchy where clients should treat parts uniformly?                          → Composite
    │   ├─ Features added dynamically/decoratively without subclasses or sibling explosion?          → Decorator
    │   ├─ Subsystem has many internals; clients need a simple unified entry?                        → Facade
    │   ├─ Thousands of similar objects blow up memory; shared part extractable?                    → Flyweight
    │   └─ Need indirection to control ACCESS to subject: lazy load, caching, auth checks, remote/large-object access, logging/audit hooks? → Proxy
    └─ No: does the pain concern ALGORITHMS / COMMUNICATION between objects?
        ├─ One algorithm/behavior swaps among several variants at runtime                            → Strategy
        ├─ Behavior depends on internal MODE and transitions rewrite big conditionals                → State
        ├─ Same skeleton algorithm, individual steps differ per subtype                              → Template Method
        ├─ Operation applied to nodes of a varied type hierarchy without polluting node classes      → Visitor
        ├─ Objects notify dependents; fan-out of changes                                            → Observer
        ├─ Sender/receiver decoupled: queue commands, transactions, retry, macro of operations       → Command
        ├─ Request handled by a pipeline of handlers; no fixed handler known up front                → Chain of Responsibility
        ├─ Two dense-messaging objects would know too much about each other                          → Mediator
        ├─ Capture/restore object state for undo without coupling to internals                       → Memento
        └─ Uniform traversal over different collection structures                                    → Iterator
```

Two matches often compete (Strategy↔State, Decorator↔inheritance, Proxy↔Adapter↔Facade, Factory Method↔Abstract Factory). Run the tie-breakers below.

## Step 3 — Tie-breakers

| Contest | Decide by |
|---|---|
| Strategy vs State | Swapped wholesale by client choice, context stays constant → **Strategy**. Object drives transitions itself, clients don't choose → **State**. Both look identical structurally; intent decides. |
| Decorator vs inheritance hierarchy | Variants combine *multiplicatively* at runtime (scrollable + resizable window) → **Decorator**; closed taxonomy of static kinds → inheritance suffices. |
| Proxy vs Adapter vs Facade | **Proxy**: same interface as subject, adds access policy (auth/cache/lazy/remote). **Adapter**: translates a *different* interface. **Facade**: simplifies a *subsystem* (narrower view, not 1:1). |
| Factory Method vs Abstract Factory | One product type varies → Factory Method; coordinated *families* of products vary → Abstract Factory. |
| Template Method vs Strategy | Fixed extension points in a stable skeleton (steps in place, holes fill) → **Template Method**; whole-algorithm replacement expected → **Strategy**. |
| Observer vs Mediator | Many-to-many broadcast where subjects don't coordinate each other → **Observer**; two (or few) parties whose direct chatter tangles → **Mediator** centralizes. |
| Command vs Chain of Responsibility | Command: store/queue/log/reverse a single invokable action. CoR: route a request along a chain until some handler accepts it. |

## Step 4 — Route and apply

Load the matching family skill for full shapes, pitfalls, and step-by-step guidance:
- Creational details → `patterns-creational`
- Structural details → `patterns-structural`
- Behavioral details → `patterns-behavioral`

Application protocol:
1. **Name the seam** in domain language (interface names matter: `DiscountPolicy`, not `Util2`).
2. **Interface first**: define the contract the pattern enforces; implement the current behavior as the first implementation — this makes the refactor testable before generalization.
3. **Migrate one call site cluster at a time**, keeping old paths working until tests pass; never mix two pattern introductions in one unverified diff.
4. **Limit ceremony**: if the pattern needs more new types than it removes of variation, reconsider — likely the gate (Step 0) was crossed prematurely.
5. Verify after: build + tests green; show the user the new file/class graph and confirm the original pain point is gone, not relocated.

## Anti-patterns to refuse

- "Patterns-for-the-resume": introducing a GoF pattern with zero concrete variant/coupling evidence.
- Inverted dependencies through a pattern to hide a missing module boundary.
- Pattern stacking (Builder inside Factory inside Abstract Factory) without each earning its keep.
- Using Singleton to fix constructor injection gaps (prefer explicit passing/DI).
- Decorator chains longer than ~3 with indistinguishable ordering semantics (smell → Flatten or replace with configuration).
