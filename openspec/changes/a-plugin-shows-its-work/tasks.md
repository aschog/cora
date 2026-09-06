## 1. The outer test

- [ ] 1.1 Write the functional test where a plugin's tool shows two lines of its own and the answered turn's trace carries both under that call, marked `@pytest.mark.xfail(strict=True)`.

## 2. The step

- [ ] 2.1 Write a test that the new kind summarises as the plugin's name and the line it was given.
- [ ] 2.2 Write a test that the detail it was given is what a reader opening it reads.
- [ ] 2.3 Write a test that a line marked as gone wrong reads as a failed step.
- [ ] 2.4 Write a test that the trace finds the new kind without it being listed anywhere.
- [ ] 2.5 Write a test that it survives a checkpoint and comes back equal to what was recorded.

## 3. What a plugin is handed

- [ ] 3.1 Write a test that `Host.show` puts a line on the trace of the turn the call is in.
- [ ] 3.2 Write a test that the line names the plugin cora loaded, not a name the plugin passed.
- [ ] 3.3 Write a test that a plugin cannot contribute a model decision or any other kind.

## 4. Where it lands

- [ ] 4.1 Write a test that lines shown during a call stand among that call's own steps.
- [ ] 4.2 Write a test that a line shown and a delegated loop's rounds stand together under one call.
- [ ] 4.3 Write a test that a line shown outside a call is dropped and nothing fails.
- [ ] 4.4 Write a test that a line shown inside `extend` does not stop the plugin loading.

## 5. Over the wire

- [ ] 5.1 Write a test that the step reaches the page as summary, detail and failed, with no frontend change.

## 6. Close it

- [ ] 6.1 Drop the outer test's `xfail` marker and watch it pass.
