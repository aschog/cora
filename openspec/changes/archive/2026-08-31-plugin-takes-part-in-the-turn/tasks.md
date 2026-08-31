Every item is one failing test, and group 2 comes first because everything else
subscribes through it. Ticked items are covered rather than counted: several items are
one test each, and a few share one — an observer that raises and an amender that raises
are the same path, because an observer *is* an amender that amends nothing.

## 1. The outer test

- [x] 1.1 **Outer.** Write a test that shows a fixture plugin amending the brief,
      refusing one tool call and wrapping one result in a single turn, with the trace
      naming it each time. Mark it `@pytest.mark.xfail(strict=True)`

## 2. The event table and the two kinds

- [x] 2.1 Write a test that shows a refusing event's handler returning a refusal raised as
      that event's own exception
- [x] 2.2 Write a test that shows a refusing event's handler returning nothing letting the
      value through
- [x] 2.3 Write a test that shows an amending event's handler returning a value handing it
      on
- [x] 2.4 Write a test that shows an amending event's handler returning nothing leaving the
      value as it was
- [x] 2.5 Write a test that shows two amenders chaining, the second handed what the first
      returned

## 3. Subscribing through the host

- [x] 3.1 Write a test that shows a plugin's handler running at the event it subscribed to
- [x] 3.2 Write a test that shows a subscription carrying the module that made it
- [x] 3.3 Write a test that shows a subscription to an event cora does not name refused,
      naming the module and the event
- [x] 3.4 Write a test that shows a handler that cannot be called refused at registration,
      by name

## 4. Cora's own screen is a subscriber

- [x] 4.1 Write a test that shows cora's empty-input and length rules running as handlers
      on the screening event
- [x] 4.2 Write a test that shows cora's own registrations listed under cora's own name
- [x] 4.3 Write a test that shows cora's handler refusing first when a plugin's would
      refuse the same question
- [x] 4.4 Write a guard that shows no module names a validation-rule port or a rules list,
      so screening has one door

## 5. The four events in the turn

- [x] 5.1 Write a test that shows a screening handler's refusal ending the turn before the
      model is called
- [x] 5.2 Write a test that shows what a brief handler returned in the brief the model
      reads
- [x] 5.3 Write a test that shows a refused tool call not running, the model told why, and
      the turn answering
- [x] 5.4 Write a test that shows a refused tool call costing the turn no round
- [x] 5.5 Write a test that shows what a tool-result handler returned being what the model
      is told
- [x] 5.6 Write a test that shows a handler that returns nothing leaving the turn unchanged
      and seeing what it subscribed to

## 6. The trace names the plugin

- [x] 6.1 Write a test that shows the trace attributing an amendment to the plugin that
      made it
- [x] 6.2 Write a test that shows two plugins' amendments named in the order they ran
- [x] 6.3 Write a test that shows a handler's step surviving a checkpoint and the
      conversation store

## 7. A handler that goes wrong

- [x] 7.1 Write a test that shows a screening handler that raises refusing the turn, with
      the trace naming the plugin
- [x] 7.2 Write a test that shows a brief handler that raises dropped, the turn completing
      without that amendment
- [x] 7.3 Write a test that shows an observer that raises dropped, the turn unchanged and
      the plugin named
- [x] 7.4 Write a test that shows a tool-call handler that raises refusing that call while
      the turn answers
- [x] 7.5 Write a test that shows what a handler was holding staying out of the refusal and
      the trace

## 8. Scope is one field and one filter

- [x] 8.1 Write a test that shows a scoped handler not running in a different scope
- [x] 8.2 Write a test that shows a system-wide handler running in every scope and with
      none active
- [x] 8.3 Write a test that shows a scoped tool not offered to the model outside its scope
- [x] 8.4 Write a test that shows scoped instructions out of the brief outside their scope
- [x] 8.5 Write a test that shows the turn's active scopes surviving a checkpoint
- [x] 8.6 Write a test that shows a system-wide screen refusing an injection in either
      scope and with none active

## 9. The plugins cora ships

- [x] 9.1 Write a test that shows the security plugin registering its rule as a system-wide
      screening handler
- [x] 9.2 Write a test that shows the fitness plugin registering instructions and tools
      under its own scope
- [x] 9.3 Write a test that shows the fitness plugin's medical filter registered
      system-wide
- [x] 9.4 Write a test that shows a medical question refused in another scope and with no
      scope active
- [x] 9.5 Bring the component-map guard green again over the assembly this change rewires

## 10. The marker comes off

- [x] 10.1 Drop 1.1's `xfail` marker and watch the outer test pass

## 11. What review found

- [x] 11.1 Write a test that shows a result handler unable to answer another call
- [x] 11.2 Write a test that shows a result handler unable to strip the untrusted label
      off the user's own documents
- [x] 11.3 Write a test that shows a call handler unable to rewrite the arguments the
      model asked for
- [x] 11.4 Write a test that shows a class refused where a handler function belongs
- [x] 11.5 Write a test that shows a refusal that is not a sentence refusing on cora's
      own wording
- [x] 11.6 Write a test that shows a registration under a blank scope refused
- [x] 11.7 Write a test that shows cora's own screen registered under cora's own name
- [x] 11.8 Write a test that shows a result handler's step traced under the call it
      changed, not above it
- [x] 11.9 Write a test that shows `CORA_SCOPES` read, and a turn running under what the
      deployment named
