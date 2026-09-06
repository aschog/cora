Written alongside the code rather than ahead of it: this change was retrofitted onto work
already done and reviewed, so the list is a record of the tests that hold it. Every item
names a test that exists and fails if its behaviour is removed.

## 1. The outer test

- [x] 1.1 Write the functional test where a fact the reader confirms forgetting leaves the rail before the store has answered.

## 2. Taking the row away

- [x] 2.1 Write a test that the row goes while the request is still in flight.
- [x] 2.2 Write a test that the rows beside it are left where they are.

## 3. Putting it back

- [x] 3.1 Write a test that a delete the store refuses lists the row again.
- [x] 3.2 Write a test that the sentence saying why arrives with it.
- [x] 3.3 Write a test that a conversation delete that fails leaves the conversation listed and says so.
- [x] 3.4 Write a test that a document delete that fails leaves the document listed and says so.

## 4. What the store confirms

- [x] 4.1 Write a test that the listing is read again after a delete, however it answered.
- [x] 4.2 Write a test that the re-read does not clear the sentence a refused delete wrote.

## 5. The outer test again

- [x] 5.1 Drop the marker and watch the outer test pass.
