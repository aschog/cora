## 1. The outer test

- [x] 1.1 Write the functional test where a Markdown list uploaded to the vocab field answers a question about one of its words and cites it, marked `@pytest.mark.xfail(strict=True)`.

## 2. The plugin

- [x] 2.1 Write a test that the vocab plugin registers instructions under its own field, and no tool and no page.
- [x] 2.2 Write a test that the instructions say what the field answers from and that it cites.
- [x] 2.3 Write the guard entry that the vocab package imports nothing outside cora.

## 3. Close it

- [x] 3.1 Drop the marker and watch the outer test pass.
