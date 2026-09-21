## 1. The outer test

- [x] 1.1 Write the functional test where a field holding two lists refuses a word until one is chosen, then puts words from that list alone for the rest of the conversation, marked `@pytest.mark.xfail(strict=True)`.

## 2. Refusing until chosen

- [x] 2.1 Write a test that a word asked for with two lists and nothing chosen is refused.
- [x] 2.2 Write a test that the refusal names every list the field holds.
- [x] 2.3 Write a test that choosing a list the field does not hold is refused, naming the ones it does.

## 3. Drilling what was chosen

- [x] 3.1 Write a test that a word comes from the chosen list and never from the other.
- [x] 3.2 Write a test that choosing all of them puts words from both.
- [x] 3.3 Write a test that a field holding one list puts a word with nothing chosen.

## 4. The choice lasts the conversation

- [x] 4.1 Write a test that a second word needs no second choice.
- [x] 4.2 Write a test that another conversation is refused until it chooses too.
- [x] 4.3 Write a test that choosing again in one conversation replaces what was chosen.

## 5. Close it

- [x] 5.1 Drop the marker and watch the outer test pass.
