# Tasks

Every item is one failing test, driven through the public API with hand-written fakes;
the model is the one boundary that gets stubbed.

## 1. The story, end to end

- [ ] 1.1 Write the outer test, `xfail(strict=True)`: a plugin tool delegating a loop
      with a declared shape is handed a value satisfying it, and parses nothing.

## 2. A round may carry a shape

- [ ] 2.1 Write a test that the model port's round carries a declared shape through to
      the model it was handed.
- [ ] 2.2 Write a test that a round carrying no shape reaches the model exactly as it
      does today.
- [ ] 2.3 Write a test that a shape crossing the port is a plain schema mapping, so the
      architecture guard still finds no provider name outside the adapters.

## 3. The adapter holds the provider to it

- [ ] 3.1 Write a test that the adapter asks the provider for the declared shape rather
      than describing it in the transcript.
- [ ] 3.2 Write a test that a provider refusing to be held to a shape raises cora's own
      model error, naming the model.
- [ ] 3.3 Write a test that an answer the provider reports as unparsed is not handed back
      as a value.

## 4. The delegated loop asks for the shape

- [ ] 4.1 Write a test that the loop's tool rounds are unchanged, and only the answering
      round carries the shape.
- [ ] 4.2 Write a test that a delegated loop with a shape hands its caller the value and
      not the prose.
- [ ] 4.3 Write a test that an answer failing the shape is asked for once more, and
      refuses the call when the second one fails too.
- [ ] 4.4 Write a test that the refusal says the shape was not satisfied, told apart from
      the loop that gathered nothing.
- [ ] 4.5 Write a test that a loop delegated with no shape still answers with prose.
- [ ] 4.6 Write a test that a shape asked for inside a loop the host bounded spends no
      round the allowance did not have.

## 5. The planner asks for its days

- [ ] 5.1 Write a test that the travel planner receives its days as a value, with no JSON
      found in prose.
- [ ] 5.2 Write a test that a day shape the model could not produce leaves the plan a
      failed call, saying why, rather than a plan with no days.
- [ ] 5.3 Write a test that the trace of that failure names the shape and not the
      checks the empty days would have failed.

## 6. The outer test

- [ ] 6.1 Drop the `xfail` marker from 1.1 and watch it pass.
