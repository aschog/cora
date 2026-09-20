## 1. The outer test

- [x] 1.1 Write the functional test where the vocab plugin brings a page, a list posted the way the page posts one lands in the vocab field, and a question about one of its words is answered from that document and cites it, marked `@pytest.mark.xfail(strict=True)`.

## 2. The plugin

- [x] 2.1 Write a test that the vocab plugin registers instructions and a page under the vocab field, and registers no tool.
- [x] 2.2 Write a test that the directory it registers is the one shipped beside the module, holding an entry page.
- [x] 2.3 Write the guard entry that the vocab package imports nothing outside cora, and that its page ships in its wheel.

## 3. What the page writes

The page's own JavaScript, which only the browser tier runs: its functions are called in
the page rather than lifted out of the file.

- [x] 3.1 Write a test that rows become a heading naming the language and a two-column table, German first.
- [x] 3.2 Write a test that a row missing either word is left out of the table.
- [x] 3.3 Write a test that a word holding a pipe does not break the table it is written into.

## 4. What the reading offers

- [x] 4.1 Write a test that a recognised line becomes a row, split where the gap between the two words is.
- [x] 4.2 Write a test that a line holding one word is offered as a row with the other half empty.
- [x] 4.3 Write a test that a reading finding no text says so and leaves an empty list to type into.
- [x] 4.4 Write a test that a recognition runtime that could not be fetched says that, rather than reading as empty.

## 5. Where it lands

- [x] 5.1 Write a test that saving uploads the table into the vocab field under a name carrying its language.
- [x] 5.2 Write a test that saving a list holding no row uploads nothing.
- [x] 5.3 Write a test that an upload cora refuses is reported and the rows are left where they can be copied.

## 6. Where it reaches

- [x] 6.1 Write a test that every address in the page is cora's own or a host the plugin's own suite names.

## 7. Through the browser

- [x] 7.1 Write a browser test that the vocab page is drawn at its field, a read row is corrected, and saving puts a document in the field.

## 8. Close it

- [x] 8.1 Drop the marker and watch the outer test pass.
