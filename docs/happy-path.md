# What happens when you ask

## A document goes in

![A UML sequence diagram of an upload: cora.frontends calls add_file on the knowledge
base with the field the document lands in, which asks the retriever whether that field
holds these bytes already, and then either repairs the text of an upload indexed before
any text was kept, or ingests, embeds, keeps and indexes it — the text as a file under
the field's own directory, the passages as spans in the field's own
index.](assets/upload-map.svg)

An upload names the field it lands in, and every step of the sequence is asked within it:
a field is a directory of Markdown files and a collection of spans, so the same document
uploaded into two fields is two copies and neither is reachable from the other.

## A turn, as a frontend asks for one

![A UML sequence diagram of a turn: a frontend calls answer on the agent, the agent runs
the thread on the graph runner, reports each new step to the caller as the states arrive,
asks whether the turn stopped to ask, and records the turn before handing back a
ChatResult.](assets/turn-map.svg)

## A round, as the graph walks it

A turn walks named steps: *screen* admits the question and opens the turn, *route* reads
which field the turn belongs to, *focus* states what cora is under that field, *work* is
where the rounds are spent, and *answer* settles what the user reads. The steps are named
where they are wired, so a turn that grows one grows it there.

*route* comes after *screen* and before *focus*, and both are deliberate. A question cora
will not accept is refused before the model is asked to read it, and the brief cannot be
written until the field is known. A pinned conversation is answered in its field without
reading the question at all; an unpinned one is read every turn.

A question that belongs to two fields is put to the reader, and that stop is *focus*'s
rather than *route*'s. A stopped step is replayed from its first line when the turn is
picked up, so the reading has to be a step behind the stop: read again on the way back,
a question can be read differently, and the answer would arrive in a field the reader
never chose.

Four points inside that walk are open to a plugin — the question being screened, the
brief being settled, a tool call about to run, a tool result coming back. A handler
subscribed to one is handed a frozen value and answers with a refusal, an amendment or
nothing. What a return means at each point is `cora.engine.events`, and the trace names
the plugin behind every one of them. Cora's own screening goes through the same door.

![A UML sequence diagram of one turn inside the graph: the runner takes the screen, route
and focus steps and then the work step, loops over the model step and the router, and on the router's
answer either runs the round's tools, stops to put a decision to the reader before
running them, or leaves the loop for the answer step.](assets/round-map.svg)

## The tool that reaches the documents

`ToolStep` never knows which tool it ran. It asks `ToolRuntime` for the name the model
gave, and hands back whatever came out — numbered `[n]` first if the result can cite
itself.

The round it runs in binds the turn's field, and the search reads it rather than being
handed it. That is what makes one rule out of four readers: cora's own search, a plugin
reading `Host.documents`, a handler at any of the four points, and a loop delegated from
inside a call all read the field the turn is in — and a plugin cannot see the turn it is
running in, so a parameter would be one nobody could fill.

![A UML sequence diagram of a document search: the tool runtime runs the tool, which asks
its context source to search; the knowledge base reads the field the turn is running in,
embeds the question with the same embedder the chunks went through, queries that field's
index for the nearest spans, and reads each passage's words back out of the file its span
was measured in.](assets/search-map.svg)

The index keeps the span and the file keeps the words, so what a search hands back is cut
out of the file rather than copied a second time into the index — and a passage whose
file is gone is left out rather than handed back empty.
