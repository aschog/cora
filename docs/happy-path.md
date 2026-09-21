# What happens when you ask

Four sequences, drawn out of the methods that take them. `make diagram` redraws them,
and a guard holds the walk they draw against the composition root — so a step added
without one is a red test.

## A document goes in

![A UML sequence diagram of an upload: cora.frontends calls add_file on the knowledge
base with the field the document lands in, which asks the retriever whether that field
holds these bytes already, and then either repairs the text of an upload indexed before
any text was kept, or ingests, embeds, keeps and indexes it — the text as a file under
the field's own directory, the passages as spans in the field's own
index.](assets/upload-map.svg)

An upload names the field it lands in — the default one where it names none — and every
step is asked within it: `add_file`
hashes the bytes, asks whether that field already holds them, and otherwise ingests,
embeds, keeps the cleaned text as a file under the field's directory, and adds the
passages as spans to that field's index. The text is kept before the index, so a citable
passage always opens onto something. One document in two fields is two copies.

## A turn, as a frontend asks for one

![A UML sequence diagram of a turn: a frontend calls answer on the agent, the agent runs
the thread on the graph runner, reports each new step to the caller as the states arrive,
asks whether the turn stopped to ask, and records the turn before handing back a
ChatResult.](assets/turn-map.svg)

A frontend calls `Agent.answer`. The agent runs the thread on the graph runner, reports
each step as the states arrive, asks the runner whether the turn stopped to ask — raising
`TurnPaused` if it did — records the turn, and hands back a `ChatResult`.

The walk is named steps, named where they are wired in the composition root: `screen`
admits the question, `route` reads which field it belongs to, `focus` states what cora is
under that field, `work` is where a field's plugin may take the question and otherwise
where the rounds are spent, `answer` settles what the reader gets.

- `screen` runs before `route` deliberately: a question cora will not accept is refused
  before any model reads it. cora's own screening is registered through the same door a
  plugin uses.
- `route` settles the field four ways, in order: the conversation's pin, scopes a caller
  named, the single field a deployment offers, then the question itself read by the
  model — which costs a call only in that last case. Every way ends in the same key, so
  only the trace says which was taken.
- A question the model reads as belonging to two fields is put to the reader at `focus`,
  not at `route`, because a stopped step is replayed from its first line: reading again
  on the way back could answer in a field nobody chose.

## A round, inside the graph

![A UML sequence diagram of one turn inside the graph: the runner takes the screen, route
and focus steps and then the work step, loops over the model step and the router, and on
the router's answer either takes the round to the gate and on to its tools, stops to put a
decision to the reader before the gate, or leaves the loop for the answer
step.](assets/round-map.svg)

Every round is model → router → gate → tools, and the ask route leads into the gate as
well — which is what makes the gate the only path from the model to the tools. A round
proposing no effect still costs the gate's superstep, which the sizing allows for.

- The rounds are entered only where nothing has answered the turn. A plugin may take the
  question at `work` — the first handler answering with text has answered it — and a
  turn taken there goes from the marker straight to `answer`: the model is never asked,
  what the plugin wrote is the round the turn ended on, and the fork is drawn where the
  runner declares it.

- The gate is a step of the core, not a point a plugin subscribes to, and it runs no
  tool — which is what makes it free to replay. It puts each proposed effect on its own,
  settles every one before the tools run, and answers a declined call with a tool
  message, so the tools need no notion of approval.
- Filling a call in happens there too, ahead of the proposals: a tool declaring `asks`
  is handed the arguments the model wrote and answers with a card. The gate puts it,
  writes what the reader filled in over those arguments, and re-issues the call — so a
  call that both asks and acts is approved as it will really be made.
- Cora asks on its own account through two tools of its own: `ask_user`, a fork between
  values it holds twice, and `ask_user_for`, a form of two values or more that it holds
  not at all. Both are settled at the `ask` step, ahead of the round's tools — a stopped
  step is replayed from its first line, so a tool that had already run would run twice.
  The fork is put once a turn, the form as often as the round budget allows.
- A plugin's card is held to one rule: asking for exactly one writable value is refused
  and the model told to ask in prose, while asking for none still stands — what a tool
  worked out, put up for a yes.
- Whatever the turn stopped on — a fork between remembered values, a call awaiting
  approval, a form to fill — reaches the page as one `Card` of a prompt, fields and
  actions, through one pause port, and one component draws all three. A field carries the
  JSON Schema it was read out of.
- Six points in the walk are open to a plugin: the question being screened, the brief
  being settled, the question about to be worked, a tool call about to run, a tool
  result coming back, and the answer settled and not yet handed over. A handler is given
  one frozen value and answers with nothing, or with the one thing its point takes — a
  refusal at the question and at a tool call, an answer at the question about to be
  worked, an amendment at the brief, a tool result and the answer. No handler may pause
  a turn.
- `ToolStep` never knows which tool it ran: it asks the runtime for the name the model
  gave and hands back whatever came out, numbered `[n]` first where the payload can cite
  itself.

## A search, inside a call

![A UML sequence diagram of a document search: the tool runtime runs the tool, which asks
its context source to search; the knowledge base embeds the question with the same
embedder the chunks went through, reads the field the turn is running in, queries that
field's index for the nearest spans, and reads each passage's words back out of the file
its span was measured in.](assets/search-map.svg)

The round binds the turn's field and the search reads it rather than being handed it —
one rule over four readers: cora's own search, a plugin reading `Host.documents`, a
handler at any of the six points — screening reads the thread's pin, because it runs
before the field is routed — and a loop delegated from inside a call.

The index keeps the span and the file keeps the words, so a retrieved passage is cut out
of its file. A passage whose file is gone is left out rather than handed back empty.
