## 1. The outer test

- [x] 1.1 Write the test that a name uploaded twice reads back both texts, oldest first, over the API, marked `@pytest.mark.xfail(strict=True)`.

## 2. The knowledge base

- [x] 2.1 Write the test that the knowledge base hands back a name's uploads with their texts, oldest first, and nothing for a name never uploaded.
- [x] 2.2 Write the test that an upload whose file is gone is left out of the answer.
- [x] 2.3 Write the test that another field's document of that name is not answered.

## 3. The route

- [ ] 3.1 Write the test that a name nothing was uploaded under answers 404 with a sentence.
- [ ] 3.2 Write the test that a field nobody loaded is refused, naming the fields there are.

## 4. Close it

- [ ] 4.1 Drop the marker and watch the outer test pass.
