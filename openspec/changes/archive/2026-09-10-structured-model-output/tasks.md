# Tasks

Every item is one failing test, driven through the public API with hand-written fakes;
the model is the one boundary that gets stubbed.

The plan this list was first written against put the shape on the model port. Mapping the
seam showed the round it named runs only when a loop has already failed, so the shape
became a tool the loop is offered instead — `design.md` carries the argument, and the
list below is the one that was built.

## 1. The story, end to end

- [x] 1.1 Write the outer test, `xfail(strict=True)`: a plugin tool delegating a loop
      with a declared shape is handed the value, and parses nothing.

## 2. The shape is a tool the loop is offered

- [x] 2.1 Write a test that a shaped loop is offered `answer` beside cora's search, with
      the shape as its parameters.
- [x] 2.2 Write a test that an unshaped loop is offered no `answer`, and its rounds are
      the ones they were.
- [x] 2.3 Write a test that a tool passed to `delegate` named `answer` is refused, as one
      named for cora's search already is.

## 3. A shape has to be worth holding to

- [x] 3.1 Write a test that a shape which is not valid JSON Schema refuses before a round
      is spent.
- [x] 3.2 Write a test that a shape requiring nothing refuses before a round is spent.

## 4. What the loop answers with

- [x] 4.1 Write a test that a clean `answer` call ends the loop and returns its arguments
      as a value.
- [x] 4.2 Write a test that the value spends no round an unshaped loop would not have
      spent.
- [x] 4.3 Write a test that arguments failing the shape are told to the loop, which
      answers again in a round it already had.
- [x] 4.4 Write a test that a loop writing prose where a shape was asked for refuses,
      saying so.
- [x] 4.5 Write a test that a shaped loop spending its allowance refuses instead of
      writing up what it had.
- [x] 4.6 Write a test that a citation number inside a string of the value is stripped,
      as it is from prose.
- [x] 4.7 Write a test that the loop's own `answer` call is on the trace, under the call
      that ran it.

## 5. The planner asks for its days

- [x] 5.1 Write a test that the planner receives its days as a value, with no JSON found
      in prose.
- [x] 5.2 Write a test that a day whose date cannot be read is dropped, because a schema
      saying `date` does not parse one.
- [x] 5.3 Write a test that days that came back empty still revise, and a refusal ends
      the call instead.

## 6. The outer test

- [x] 6.1 Drop the `xfail` marker from 1.1 and watch it pass.
