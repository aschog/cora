## 1. The outer test

- [x] 1.1 Write the browser-tier test where a notice written while another conversation is on the screen opens the field's own conversation and draws its page.

## 2. Which conversation it opens

- [x] 2.1 Write a test that the newest conversation pinned to that field is the one chosen.
- [x] 2.2 Write a test that a field no conversation is pinned to opens nothing.
- [x] 2.3 Write a test that a notice naming the conversation already open leaves the address alone.

## 3. When it acts

- [x] 3.1 Write a test that the notice standing when the page loads opens nothing.
- [x] 3.2 Write a test that a second notice after the first opens the conversation again once the reader has left it.
- [x] 3.3 Write a test that a field written to for the first time acts, its answer of "no notice" having been the baseline.

## 4. What it asks

- [x] 4.1 Write a test that only fields with a page are asked for a notice.
- [x] 4.2 Write a test that a deployment where no field has a page asks for nothing.
- [x] 4.3 Write a test that a notice that cannot be read leaves the page working and raises no banner.

## 5. Close it

- [x] 5.1 The outer test was written red and made green in one sitting, so it never carried `test.fail()` and there was none to drop.

## Note

- 3.3 was discovered by the outer test failing after the hook was written: a field with no notice recorded no baseline, so the first notice it ever took was the one the poll sat through.
