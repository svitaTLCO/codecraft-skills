---
name: patterns-behavioral
description: Detect and apply refactoring.guru behavioral patterns: Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor. Use when algorithms must swap at runtime ("pluggable strategies/policies chosen per instance"), objects coordinate via tangled messaging, undo/redo is needed, notification fans-out, request pipelines route dynamically, type hierarchies accrete new operations, or state machines hide in big conditionals. Triggers: "event bus", "undo this", "swap algorithm", "too many observers", "workflow pipeline", "state machine", "visit every node", "loose coupling between these two". Also handles direct named-pattern calls within this family: "apply the observer pattern", "make these pluggable strategies", "use template method for X", "state transitions here".
---

# Behavioral Patterns (Refactoring.Guru set)

Restructure *responsibilities and communication*: which object decides what runs, how behavior swaps, and how parts talk. Load `patterns-detect` first if unsure whether a pattern applies at all.

## Quick Pick

| Situation | Pattern | Kill switch |
|---|---|---|
| Whole algorithm swaps by client choice at runtime | Strategy | 2 stable variants → enum/dispatch suffices |
| Behavior follows internal MODE with transitions; `if state == X` sprawl | State | No real transition logic — just flags (plain fields) |
| Fixed skeleton, only steps vary per subtype | Template Method | Whole-algorithm replacement expected → Strategy |
| New operations keep being added onto varied type hierarchy without touching node classes | Visitor | Operations are few/known; nodes changing freely otherwise |
| Many dependents react to one source's changes | Observer | One fixed dependent → direct call |
| Two parties' mutual knowledge tangles everything | Mediator | Single owner relationship fine as-is |
| Requests queued/logged/retried/executed later as discrete actions | Command | Fire-and-forget simple calls need no ceremony |
| Request travels along handlers until accepted; unknown handler up front | Chain of Responsibility | Fixed single target → direct call; sequential all-required → pipeline composition |
| Capture + restore snapshot for undo without leaking internals | Memento | Changes trivially reversible by inverse ops (store those instead) |
| Uniform traversal over differently-structured collections | Iterator | Language already provides iteration protocol for your structures |

## Techniques

### Chain of Responsibility
**Intent:** pass a request along a chain of handlers until one handles it; decouple sender from the specific receiver.
**Detect:** "which component should handle this?" decided by rules that keep changing (severity routing, approval escalation, fallback parsers/decoders, validation pipelines); code with if/else selecting among peers where adding a peer means editing the selector; multiple possible receivers for the same message type.
**Avoid:** exactly one known handler (direct call); every handler MUST run (that's sequential pipeline/composition, not CoR — use an explicit ordered list with no early-stop semantics); handlers whose relative order is semantically meaningless but you need determinism anyway (name your ordering rules or use priorities explicitly).
**Shape:**
```
Handler { next?: Handler; handle(req) → handled-or-forward }
ConcreteA/B/C : Handler           // each tries its own slice
Client sends to head of chain only
```
**Apply:** 1) define the request type (narrow record, not raw event bag), 2) implement handlers checking their own acceptance criteria first, delegating to `next` when declined, 3) wire the chain at composition point (registry sorted by priority where order is rule-based), 4) add a terminal handler / default outcome so unhandled requests fail loudly instead of silently vanishing.
**Pitfalls:** silent drops when chain ends without handling (make exhaustion observable — throw/log/metric); diamond dependencies when two chains share handlers mid-graph (keep chains linear per message type); handlers doing work BEFORE deciding (side effects run even if a later handler would have owned the request — decide-then-act discipline); priority ties produce non-deterministic order under concurrency.

### Strategy
**Intent:** encapsulate interchangeable behaviors behind one interface; context delegates; behavior chosen at construction/injection.
**Detect:** switch/if on "mode"/"policy" parameter scattered across methods; siblings differing only in one operation; users demanding pluggable policies (pricing, discount, rendering, compression).
**Avoid:** behaviors share heavy internal state with the context (extracting them drags half the class out); selection depends on runtime data that itself varies continuously (a function/config may beat object-per-policy); only two trivial variants (named constants + small dispatch wins).
**Shape:**
```
Strategy { execute(input): result }
ConcreteStratA / B / C : Strategy
Context { s: Strategy; handle(i) → s.execute(i) }   // injected
```
**Apply:** 1) isolate the varying computation into an interface named by capability (`PricingPolicy`, not `IUtil`), 2) extract existing branches as concrete strategies one by one (tests pin each branch first), 3) inject strategy into context (constructor/DI), removing the selector parameter from hot methods, 4) expose registration points only where users legitimately extend.
**Pitfalls:** strategies needing access to whole context become god-strategies (pass a narrow input record instead); implicit selection defaults silently choosing strategy A for everyone (fail explicit); strategy objects stateless & immutable whenever possible.

### State
**Intent:** let an object alter behavior when its internal state changes, appearing to change class; transitions live where they belong.
**Detect:** mode enum + big conditional blocks re-evaluated everywhere ("in edit mode…"; order lifecycle NEW→PAID→SHIPPED); adding a mode touches N unrelated files.
**Avoid:** modes with no meaningful transitions (flags suffice); modes rarely used concurrently with complex interplay (State overhead unearned); when the stateful thing is really a separate component (model it separately).
**Shape:**
```
State { on(event) → self-or-next-state; handle(context) }
ConcreteStates : State           // each knows its transitions
Context { s: State; fireEvent(e) → s = s.on(e); s.handle(this) }
```
**Apply:** 1) model states explicitly (diagram/diary of legal transitions first — tests per transition incl. illegal ones throwing), 2) implement one state object per mode owning its event handling, 3) give states the power to mutate context's reference (`context.transitionTo(newState)` — prefer context-owned swap so states don't hold back-references unless events require it), 4) replace the mode field + conditionals with delegation.
**Pitfalls:** state explosion combinatorially (n modes × m events — audit the matrix; split concerns into smaller machines rather than one giant one); duplicated invariants across states → context still owns what's shared; concurrent transitions race (serialize state changes); debugging — log transitions (from→event→to) centrally.

### Template Method
**Intent:** define algorithm skeleton in base; subclasses fill specific step(s) while keeping flow fixed.
**Detect:** identical sequence of stages across subtypes (parse→validate→transform→output; setup→run→teardown) with individual steps varying; frameworks exposing hook points.
**Avoid:** steps reorder per variant (that's Strategy-per-step or full replacement); only one subclass ever exists (YAGNI); steps interact through mutable hidden state making overrides brittle.
**Shape:**
```
Base { final run() { setup(); doWork(); teardown() }
       doWork() abstract; hooks: before()/after() default no-op }
Sub : Base { doWork() specialized }
```
**Apply:** 1) write the skeleton once as a concrete non-overridable method, 2) mark variation points abstract (required) vs protected-hook-with-default (optional), 3) move existing shared code up, push divergences down, 4) document the algorithm and which steps may override what.
**Pitfalls:** inverted control confuses readers — top-of-class comment naming the skeleton helps; too many hooks = thin abstraction (compare Strategy when variants swap whole steps); late-binding surprises when subclasses add side effects in hooks — keep hook contracts strict and tested.

### Visitor
**Intent:** define an operation on elements of a structure without modifying their classes; new operation = new visitor type.
**Detect:** node/type hierarchy stable but operations keep multiplying (renderers, compilers, analyzers, serializers each adding methods to every node type); node classes becoming swiss-army-knives with method-per-operation.
**Avoid:** types change frequently (every new type forces edits to ALL visitors — the cost flips); operations are few and stable (methods on types suffice); language lacks clean double-dispatch (workarounds like tagging closures exist but fight the grain — weigh carefully).
**Shape:**
```
Element { accept(visitor) ; /* per concrete type */ }
ConcreteA { accept(v) → v.visitA(this) }
Visitor { visitA(a); visitB(b); ... }
ReportVisitor / ExportVisitor : Visitor
```
**Apply:** 1) freeze the element set deliberately (declare stability contract), 2) add `accept` per element, 3) create one visitor per new operation migrating the scattered if/instanceof ladders, 4) register/select visitors at use sites.
**Pitfalls:** open-closed violation is *inverted* here — closed for types, open for operations; say that out loud before committing; partial visitors visiting only some elements need defined no-op/error policy; performance: virtual double-dispatch + indirection in hot loops (profile; inline specialization in compiled languages often rescues it).

### Observer
**Intent:** one-to-many dependency; subscribers notified when subject state changes.
**Detect:** ad-hoc lists of callback arrays growing across modules; "who listens to price changes?" unanswered; UI layers + analytics + cache invalidation all reacting to same domain event.
**Avoid:** exactly one consumer with a stable interface (direct coupling simpler); event ordering guarantees needed beyond broadcast (mediator/choreography discipline required); subject emits nothing but noise (subscriber fatigue → useless listeners accumulate).
**Shape:**
```
Subject { subscribe(h); unsubscribe(h); notify(event) }
Observer { onEvent(subject, event) }
Concrete subjects emit typed events with payloads (immutable snapshots, NOT live references)
```
**Apply:** 1) define event taxonomy (what changed, who cares) — payload = data, not the subject (decoupling test: subscriber should survive subject refactor), 2) implement subscription registry (typed channels preferred), 3) emit at mutation points synchronously (documented) or async queue (documented; ordering consequences), 4) auto-clean subscriptions on scope end (frameworks: effect cleanup; manual: pair subscribe/unsubscribe in finally/RAII).
**Pitfalls:** leak #1: forgotten unsubscriptions (GC'd? callbacks pinned?) — pairing rule enforced by review/lint; circular notifications (subject A notifies B, B mutates notifying A) — detect via depth limits or logging; sync fan-out makes subject slow as listener count grows (batch/async when hot); ordering assumptions creep in silently — document guarantees (per-subscriber FIFO yes; cross-subscriber no).

### Command
**Intent:** encapsulate a request as an object: data about the invocation, sender decoupled from receiver, enables queues, logging, transactions, undo.
**Detect:** callers invoking receivers directly with parameters where you want (a) queuing/retry, (b) macro batches, (c) audit logs, (d) undo support; UI/menu buttons hardwired to controller methods.
**Avoid:** fire-and-forget one-shot calls with no deferred/audit needs (wrapping is tax); synchronous immediate execution guaranteed always (simple dispatcher beats object ceremony); extremely high-frequency invocations (object allocation per call — pool or bypass).
**Shape:**
```
Command { execute(); undo()? }
ConcreteCmd { receiver; arg; execute() → receiver.op(arg); undo() → inverse }
Invoker { queue: [Command]; history: [Command] }   // menu, queue, macro recorder
```
**Apply:** 1) define Command seam named by action (`SubmitOrderCommand`), 2) implement execute against a narrow receiver interface (testability), 3) implement undo ONLY where inversion semantics truly defined (log-based rebuild safer than hand-inversed ops), 4) wire invokers: queue with retry/persistence (serializable commands for durable queues — version your schema!), macros recording sequences.
**Pitfalls:** serializing command objects to durable stores freezes API evolution (version explicitly); undo asymmetry (execute succeeds, undo partially fails mid-way — transactional groups or log reconstruction); command objects holding live references prevent GC of big graphs (hold ids/serializable args); double-execution after retries without idempotency keys.

### Iterator
**Intent:** traverse aggregate's elements without exposing representation; same loop code across different structures.
**Detect:** client code indexing into internals (`for i in range(len(lst))`), trees traversed by bespoke recursion per caller, multiple container types sharing consumers; skipping/filtering repeated inline.
**Avoid:** single well-supported native container whose language iteration is idiomatic (use it — don't wrap for ritual); traversal needs random access/mutation-during-walk semantics the iterator contract can't promise cleanly; micro-performance-critical tight loops where index access provably faster (profile first).
**Shape:**
```
Iterator { next(): value|nil; reset(); remove?(current) }
Aggregate { createIterator(): Iterator }
ListIter / TreeIter(DFS/BFS variants) : Iterator
Consumer loops: while v := it.next() { ... }
```
**Apply:** 1) pick the iteration contract (order guarantee, failure signaling, mutation policy: fail-fast vs skip), 2) implement per structure (tree: choose DFS/BFS deliberately — both if clients differ, name them), 3) migrate consumers off index/recursion code onto the uniform loop, 4) expose filtered/projected views lazily where the language allows (composability > one-off methods).
**Pitfalls:** structural modification during iteration (define and enforce: exception or skip — never unspecified silent corruption); stale iterators after aggregate change (generation/version stamp check); memory: tree iterators holding deep parent stacks — bound depth or release resources deterministically.

### Mediator
**Intent:** replace many-to-many direct references among components with a central mediator defining coordination rules.
**Detect:** widget A updates B and C which update D — ripple spaghetti; chat/channel members pinging each other directly; two services knowing each other's internals "just to help."
**Avoid:** shallow interactions (one requester–responder pair → direct call); mediator would accrete ALL business logic of the system (god-controller anti-pattern — mediator coordinates, domains own their rules); strict point-to-point trust model demands isolation (that's proxy/security architecture, not Mediator).
**Shape:**
```
Mediator { register(part); onEvent(p, e); broadcast/update targets }
Colleague { env: Mediator; act() → env.request(...) }  // knows only mediator
```
**Apply:** 1) inventory current cross-talk edges; classify: coordination (belongs in mediator) vs domain decisions (stay in colleagues), 2) build mediator exposing intent-level operations (`setVolume(level)`) not raw peer messages, 3) swap direct references behind colleague façades one edge at a time, 4) delete residual peer references; test scenario scripts of multi-participant flows.
**Pitfalls:** mediator absorbing business logic = Second God Class; cyclic mediation (peer events triggering mediator actions that trigger peers...) — bound rounds or log loops; scaling: one mediator per bounded context beats global omniscient mediator (multiple mediators coordinating through narrower seams).

### Memento
**Intent:** capture and restore an object's internal state without exposing it; classic undo/redo, snapshots, checkpointing.
**Detect:** "save so we can roll back" features; transactions around expensive composite operations; editors storing history; long workflows needing cancel-to-checkpoint.
**Avoid:** state cheaply invertible by inverse operations (store the inverse op list — Command+undo usually lighter); entire-process snapshots needed (checkpoint/copy-on-write OS mechanisms fit better); huge states where every memento copies gigabytes (diff-based or incremental mementos required — design deliberately).
**Shape:**
```
Originator { set(state); memento() → Memento; restore(m) }
Memento { private internal snapshot }   // accessor restricted to Originator
Caretaker { stack: [Memento]; remember(o); restore(o) }
```
**Apply:** 1) define what "state" covers precisely (invariant sets — excluding derived caches or restoring them corrupts), 2) make snapshot capture atomic under concurrency (lock/snapshot boundary), 3) restrict memento access to originator (external reads of internals defeat encapsulation — enforce by language or convention), 4) bound history (ring buffer max size; evict oldest; persist optionally).
**Pitfalls:** mementos referencing live internals instead of copying (mutation after capture leaks into "snapshots"); memory growth from unbounded history (cap + compression); restoring mid-flight with concurrent writers racing (pause or serialize mutations around restore); semantic drift when originator gains fields and old mementos predate them (version mementos).
