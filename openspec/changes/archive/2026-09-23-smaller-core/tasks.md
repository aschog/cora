## 1. The outer test

- [x] 1.1 Write `tests/acceptance/test_smaller_core.py`, `xfail(strict=True)`: a bare cora offers read, write and a command and nothing else, writes and reads a field file without stopping; with `ask`, `memory` and `documents` loaded an upload is searched and cited, a fork is settled through the gate, and a fact asked for briefs the next conversation.

## 2. The field's own tools

- [x] 2.1 Write a test that the read tool returns a field file's text and a missing name reads as not there.
- [x] 2.2 Write a test that the write tool keeps text under a plain name and the field lists it.
- [x] 2.3 Write a test that a name with a separator is refused by both and nothing outside the field changes.
- [x] 2.4 Write a test that the subprocess shell runs a command with the field's directory as its working directory.
- [x] 2.5 Write a test that a command naming a parent or an absolute path is refused before it runs.
- [x] 2.6 Write a test that output past the cap is cut and the result says so.
- [x] 2.7 Write a test that a command past the time is stopped and the result says so.
- [x] 2.8 Write a test that the read and the command results reach the model behind the untrusted label.
- [x] 2.9 Write a test that a turn writing a file and running a command never stops for the reader.
- [x] 2.10 Write a test that a bare app offers the three tools beside what it still offers, and its brief names them.

## 3. Asking leaves the engine

- [x] 3.1 Write a test that a card naming a landing argument makes the gate write the action taken into it before the tool runs.
- [x] 3.2 Write a test that a card's way out, being an action, runs the tool with its value.
- [x] 3.3 Write a test that a card naming no argument settles on the action alone, as before.
- [x] 3.4 Write a test that `ask.extend` registers the fork, the form and a system-wide section.
- [x] 3.5 Write a test that the fork's card offers one action per option and names the landing argument, and the tool says which was taken.
- [x] 3.6 Write a test that the fork's way out makes the tool say nothing was chosen.
- [x] 3.7 Move the form's tests to the plugin: one field refused, two fields drawn, a repeated name refused, the reader's values in the result.
- [x] 3.8 Write a test that the same fork asked twice in a conversation is refused the second time through the plugin's state.
- [x] 3.9 Write a test that the router goes model, gate, tools and has no ask route, and the loop has no ask slot.
- [x] 3.10 Write a test that a round asking both ways puts two cards and runs on both answers.
- [x] 3.11 Write a test that a bare app offers nothing that asks and its brief carries no ask rule.
- [x] 3.12 Regenerate the round and turn maps and watch their guards pass without an ask node.
- [x] 3.13 Make the asks acceptance tests load the plugin through the builder and pass.

## 4. Memory leaves the engine

- [x] 4.1 Write a test that `memory.extend` with a memory registers `remember`, a system-wide section and a briefing handler.
- [x] 4.2 Write a test that `memory.extend` without a memory registers nothing and logs why.
- [x] 4.3 Write a test that the handler appends the notes under their heading and the data-not-instructions notice.
- [x] 4.4 Move the conflict tests to the plugin: three values named, agreeing notes not, one subject not.
- [x] 4.5 Write a test that an unreadable store makes the handler raise and the turn's trace says the plugin could not amend the brief.
- [x] 4.6 Move the remember tool's tests to the plugin: blank refused, too long refused, kept once, store failure refused.
- [x] 4.7 Write a test that a second plugin registering `remember` beside the memory plugin is refused naming both.
- [x] 4.8 Write a test that the focus step writes a brief with no memory section and no notes, whatever memory the app holds.
- [x] 4.9 Regenerate the domain map and watch its guard pass without `MemoryUnread`.
- [x] 4.10 Make the memory acceptance tests load the plugin through the builder and pass.

## 5. Field files hold bytes

- [x] 5.1 Write a test that the directory store writes bytes, reads them back as bytes, and reads them as text as nothing.
- [x] 5.2 Write a test that a tool call reads its field's bytes through the host's files.
- [x] 5.3 Write a test that the fake `Files` in the test helpers keeps bytes the same way.

## 6. An upload lands and is heard

- [x] 6.1 Write a test that the intake lands the file in the field and answers taken when nobody subscribed.
- [x] 6.2 Write a test that a subscribed handler is handed the name and reads the bytes of that field.
- [x] 6.3 Write a test that a sentence from a handler refuses the upload, drops the file, and is what the reader reads.
- [x] 6.4 Write a test that a raising handler refuses on cora's wording and drops the file.
- [x] 6.5 Write a test that a handler subscribed under another field does not run.
- [x] 6.7 Write a test that the listing prints an upload handler under the event's name.

## 7. The host hands an index

- [x] 7.1 Write a test that a document put in through `Host.index` in a turn of a field is found by a search of it and its citation opens onto the text.
- [x] 7.2 Write a test that an index failing to take the passages leaves none searchable.
- [x] 7.3 Write a test that `Host.index` says it holds an upload after adding it, and not in another field.
- [x] 7.4 Write a test that the second add of one upload is answered as already held and adds nothing.

## 8. The documents plugin

- [x] 8.1 Write a test that `documents.extend` registers the search tool, a section and the upload handler, all system-wide.
- [x] 8.2 Write a test that the handler indexes a Markdown upload into its field and a search finds the passage.
- [x] 8.3 Write a test that plain text and PDF are read, and another kind is refused naming the kinds read.
- [x] 8.4 Write a test that an empty document and one over the cap are refused with their sentences.
- [x] 8.5 Write a test that the same bytes uploaded twice add nothing the second time and repair a text that went missing.
- [x] 8.6 Move the chunker and cleaning tests to the plugin and watch them pass there.
- [x] 8.7 Write a test that the search tool numbers its hits to be cited and says nothing was uploaded on an empty field.
- [x] 8.8 Write a test that the depth is read from the plugin's settings and defaults to five.
- [x] 8.9 Write a test that the section names the search tool, the citing form and the empty-search rule.
- [x] 8.10 Extend the packaging guard so `pypdf` is the documents plugin's dependency and not the app's.
- [x] 8.11 Write a test that the upload route lands the file among the field's files and answers the document and the field without a count.

## 9. The engine forgets the search

- [x] 9.1 Write a test that a delegated loop is offered what was passed, cora's read, and every system-wide tool without effect or asks.
- [x] 9.2 Write a test that write, the command, a system-wide tool declaring an effect, and a tool that asks are withheld from the loop.
- [x] 9.3 Write a test that the loop reserves the answer tool's name and no other.
- [x] 9.4 Write a test that the config reads no `CORA_TOP_K` and the host carries no depth.
- [x] 9.5 Write a test that the contract is 2 and a plugin declaring 1 is refused naming both versions.
- [x] 9.6 Regenerate the upload, search and component maps and watch their guards pass.
- [x] 9.7 Make the documents, RAG, scopes and shipped-plugin acceptance tests load the plugins through the builder and pass.

## 10. The page

- [x] 10.1 Write a vitest that the reading screen offers the box, unticked keeps through the files route and ticked through the upload route.
- [x] 10.2 Write a vitest that an upload answer without a count is shown as added.

## 11. Done

- [x] 11.1 Write a test that the reserved names are the three tools and `remember`, `ask_user`, `search_documents` are free.
- [x] 11.2 Write a test that a bare app offers exactly the three tools and nothing else.
- [x] 11.3 Drop the `xfail` marker on 1.1 and watch the outer test pass.

## 12. A field's files may be its plugin's own

- [x] 12.1 Write a test that a plugin claims the files of its field, and that a claim under no field is refused.
- [x] 12.2 Write a test that a turn in a claimed field is offered none of cora's three, and one in another field all of them.
- [x] 12.3 Write a test that a turn reaching a claimed field beside an unclaimed one is offered none of them.
- [x] 12.4 Write a test that what the plugins registered still follows cora's own in what a turn is offered.
- [x] 12.5 Write a test that the vocab plugin claims its field, so the drill is the only way to a word.
- [x] 12.6 Regenerate the round and search maps and watch their guards pass.
