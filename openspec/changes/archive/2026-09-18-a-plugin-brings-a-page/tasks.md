## 1. The outer test

- [x] 1.1 Write the functional test where a plugin dropped into the folder brings a page, that page is served under the path its field reports, and it is gone when the plugin is, marked `@pytest.mark.xfail(strict=True)`.

## 2. Registering one

- [x] 2.1 Write a test that a registered page is kept as a directory under the field it was registered for.
- [x] 2.2 Write a test that a page registered under no field refuses the plugin by name.
- [x] 2.3 Write a test that a plugin whose page directory is not there still loads and offers its tools.
- [x] 2.4 Write a test that one plugin registering a second page for one field is refused.
- [x] 2.5 Write a test that one plugin registering a page under each of two fields keeps both.

## 3. One page per field

- [x] 3.1 Write a test that two plugins bringing one field's page refuse the composition, naming both and the field.
- [x] 3.2 Write a test that two plugins bringing a page each for their own field compose.

## 4. What the app and the listing carry

- [x] 4.1 Write a test that the composed app maps each field with a page to the directory registered for it.
- [x] 4.2 Write a test that a plugin's listing carries its page under the field it is for, and no directory.
- [x] 4.3 Write a test that the terminal listing prints that page on a line of its own, the renderer unchanged.
- [x] 4.4 Write a test that the plugins endpoint carries the page among the contributions it already sends.

## 5. Serving it

- [x] 5.1 Write a test that the path a field reports answers the entry page of its directory.
- [x] 5.2 Write a test that a script and an image beside the entry page are answered as what they are.
- [x] 5.3 Write a test that a request spelling its way above the directory is refused and serves nothing outside it.
- [x] 5.4 Write a test that the path of a field whose plugin brought no page is refused.
- [x] 5.5 Write a test that the path of a field nothing loaded is refused.
- [x] 5.6 Write a test that a page whose directory went away after it loaded is refused rather than raising.
- [x] 5.7 Write a test that a plugin symlinked into the folder has its page served.
- [x] 5.9 Write a test that a symlink inside a page directory is not followed out of it.
- [x] 5.8 Write a test that cora's own page still answers at the root with a page route before it.

## 6. Served as it stands

- [x] 6.1 Write a test that an edited page file is answered as it now stands.
- [x] 6.2 Write a test that a served file asks to be revalidated before it is reused.

## 7. Live with the plugin

- [x] 7.1 Write a test that a plugin dropped into the folder has its page served with nothing restarted.
- [x] 7.2 Write a test that the page of a plugin taken out of the folder is refused on the next request.

## 8. Which fields have a page

- [x] 8.1 Write a test that the fields on offer name the path a field's page is served under.
- [x] 8.2 Write a test that a field whose plugin brought no page is offered with none claimed for it.
- [x] 8.3 Write a test that a field a plugin brought only a page for is still among the fields offered.
- [x] 8.4 Write a test that a field whose name a URL would read as syntax is reported at an address that answers.

## 9. Close it

- [x] 9.1 Drop the outer test's `xfail` marker and watch it pass.
