Every item is one failing test, and group 2 comes first because everything else
subscribes through it.

## 1. The outer test

- [ ] 1.1 **Outer.** Write a test that shows a fixture plugin amending the brief,
      refusing one tool call and wrapping one result in a single turn, with the trace
      naming it each time. Mark it `@pytest.mark.xfail(strict=True)`

## 2. The event table and the two kinds

- [ ] 2.1 Write a test that shows a refusing event's handler returning a refusal raised as
      that event's own exception
- [ ] 2.2 Write a test that shows a refusing event's handler returning nothing letting the
      value through
- [ ] 2.3 Write a test that shows an amending event's handler returning a value handing it
      on
- [ ] 2.4 Write a test that shows an amending event's handler returning nothing leaving the
      value as it was
- [ ] 2.5 Write a test that shows two amenders chaining, the second handed what the first
      returned

## 3. Subscribing through the host

- [ ] 3.1 Write a test that shows a plugin's handler running at the event it subscribed to
- [ ] 3.2 Write a test that shows a subscription carrying the module that made it
- [ ] 3.3 Write a test that shows a subscription to an event cora does not name refused,
      naming the module and the event
- [ ] 3.4 Write a test that shows a handler that cannot be called refused at registration,
      by name

## 4. Cora's own screen is a subscriber

- [ ] 4.1 Write a test that shows cora's empty-input and length rules running as handlers
      on the screening event
- [ ] 4.2 Write a test that shows cora's own registrations listed under cora's own name
- [ ] 4.3 Write a test that shows cora's handler refusing first when a plugin's would
      refuse the same question
- [ ] 4.4 Write a guard that shows no module names a validation-rule port or a rules list,
      so screening has one door

## 5. The four events in the turn

- [ ] 5.1 Write a test that shows a screening handler's refusal ending the turn before the
      model is called
- [ ] 5.2 Write a test that shows what a brief handler returned in the brief the model
      reads
- [ ] 5.3 Write a test that shows a refused tool call not running, the model told why, and
      the turn answering
- [ ] 5.4 Write a test that shows a refused tool call costing the turn no round
- [ ] 5.5 Write a test that shows what a tool-result handler returned being what the model
      is told
- [ ] 5.6 Write a test that shows a handler that returns nothing leaving the turn unchanged
      and seeing what it subscribed to

## 6. The trace names the plugin

- [ ] 6.1 Write a test that shows the trace attributing an amendment to the plugin that
      made it
- [ ] 6.2 Write a test that shows two plugins' amendments named in the order they ran
- [ ] 6.3 Write a test that shows a handler's step surviving a checkpoint and the
      conversation store

## 7. A handler that goes wrong

- [ ] 7.1 Write a test that shows a screening handler that raises refusing the turn, with
      the trace naming the plugin
- [ ] 7.2 Write a test that shows a brief handler that raises dropped, the turn completing
      without that amendment
- [ ] 7.3 Write a test that shows an observer that raises dropped, the turn unchanged and
      the plugin named
- [ ] 7.4 Write a test that shows a tool-call handler that raises refusing that call while
      the turn answers
- [ ] 7.5 Write a test that shows what a handler was holding staying out of the refusal and
      the trace

## 8. Scope is one field and one filter

- [ ] 8.1 Write a test that shows a scoped handler not running in a different scope
- [ ] 8.2 Write a test that shows a system-wide handler running in every scope and with
      none active
- [ ] 8.3 Write a test that shows a scoped tool not offered to the model outside its scope
- [ ] 8.4 Write a test that shows scoped instructions out of the brief outside their scope
- [ ] 8.5 Write a test that shows the turn's active scopes surviving a checkpoint
- [ ] 8.6 Write a test that shows a system-wide screen refusing an injection in either
      scope and with none active

## 9. The plugins cora ships

- [ ] 9.1 Write a test that shows the security plugin registering its rule as a system-wide
      screening handler
- [ ] 9.2 Write a test that shows the fitness plugin registering instructions and tools
      under its own scope
- [ ] 9.3 Write a test that shows the fitness plugin's medical filter registered
      system-wide
- [ ] 9.4 Write a test that shows a medical question refused in another scope and with no
      scope active
- [ ] 9.5 Bring the component-map guard green again over the assembly this change rewires

## 10. The marker comes off

- [ ] 10.1 Drop 1.1's `xfail` marker and watch the outer test pass
