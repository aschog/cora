
#### Found by the branch review (`ai-code-reviewer`, PR #35)

- [x] a passage found in one upload still reads that upload's text after the same
      filename is uploaded again with other text in it — the kept text is keyed by the
      upload, and a hit carries the upload it was cut from
- [x] a document whose text cannot be kept is never left searchable: `keep` is written
      before the index will hand the passage out
- [x] every number in a run — `[1][2]` — becomes its own button, the rule `cited_numbers`
      already read by
- [x] a bracketed number inside a tag is left alone; substitution runs over the text of
      the rendered HTML, not its attributes
- [x] an image in an answer fetches nothing — the renderer has images disabled, so a
      document cannot make the reader's browser call out
- [x] the live-model citation check reads the answer, not the Sources panel, so it can
      fail again
- [x] a passage whose text was never kept says so under its document's heading, told
      apart from a number belonging to no answer in the thread
- [x] closing the pane gives the conversation its full width back — the column split
      goes, not just the pane's contents
