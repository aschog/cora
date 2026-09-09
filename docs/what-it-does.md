# What cora does

The behaviour a reader meets: the fields a question is answered in, the cards it stops
on, what an effect waits for, and what deleting any of it takes. How a turn runs is
[what happens when you ask](happy-path.md); what it is made of is
[what it is made of](big-picture.md).

## Fields

A field is offered because something brings it: a plugin registers one, or a deployment
names one in `CORA_SCOPES` — which is how a field holding only documents exists. Every
question is answered in exactly one of them, and a search sees the field its turn is
running in and no other.

With two fields offered, cora reads each question and answers it in the one it belongs
to — the trace says which, and a question that fits both stops the turn to ask. That is
*Chat*, above the conversation. Name one field instead — *+ Plugin* lists the ones this
deployment loaded — and every later turn is answered in it, through a reload and a
reopen: the pin is the thread's own state. A pin is set once, because a
thread that could change field is a thread whose earlier turns mean something else — a
second field is a second conversation. Loading one field leaves nothing to route
between, which is how a single-field deployment stays one.

## Cards

Everything cora stops for is one card. A question between two remembered weights, a
call it is about to make that changes something outside itself, a form it needs filled
in — the same prompt, fields and buttons, drawn by one thing on the page that knows
none of those three apart. A field carries the JSON Schema it came from and the page
draws the control that schema describes, so a plugin adds a card the page has never
seen without touching the page: the card is data cora sends, not code anybody shipped.

Cora asks for what it does not have, as one of those. Where a plugin's tool asks for the
arguments it was called without, cora asks for the values an answer turns on and nobody
has written down — the trip, the dates, the budget — naming the fields itself and putting
them as one form rather than a list of questions you answer one at a time. It is cora's
own, so a deployment with no plugin loaded asks this way too. A card whose required
fields are empty cannot be sent — you fill it in, or you leave it.

One value is not a card, though. Where a single thing is all cora is missing, it asks in
a sentence and you answer in the composer: a form of one box is a stop that the sentence
had already made, and the box costs you the turn as well. So a card is what two or more
values are worth stopping for. A card asking for exactly one is refused before it
reaches you, whichever plugin wrote it — while a card asking for none is a different
thing and stands: a call waiting on your yes, or what cora worked out put up to be
confirmed.

## Deleting what it holds

A conversation you are finished with is deleted from the list under *SESSIONS*, from the
control at the end of its row — which asks first, and says what is lost and what is not.
Deleting takes both halves of it: the turns you came back through, and the thread they
were answered on — its pin, what the model was told, and any question it stopped on.
One is not deletable without the other, because a record that is gone and a thread that
is not is a conversation listed nowhere and still there. The one you are reading offers
no delete, and neither does one cora is still answering a question in: you leave the
first, and wait for the second.

A fact under *MEMORY* goes the same way: the same control at the end of its row, the same
question first — and forgetting everything is asked about too, because it is the most
destructive thing either rail offers. What a question says is what is lost *and* what is
not: forgetting a fact leaves your documents and your conversations alone, and deleting a
conversation leaves your documents and what cora remembers alone.

A field owns its documents. Each one cora ingests is kept as a Markdown file of its
cleaned text, under a directory named for the field it was uploaded into: `travel` holds
`kyoto-8f21c0a4e9d3.md`, the upload's hash in the name so one filename uploaded twice is
two files rather than one overwritten. The index beside it keeps the embeddings and
where each passage sits in that file, and nothing else: a
passage's words are read back out of the file when it is retrieved, so the text exists
once and a citation opens onto something you can read yourself. A search sees the field
its turn is running in and no other, and the rail lists and uploads into the field it is
set to. `CORA_DOCUMENTS_PATH` moves the root; a second field is a directory under it.

A document you are finished with is deleted from the rail, from the same control the
other two rails carry — and it asks first. That takes both halves of it: its passages
out of the index, and the file its citations opened onto. The rail lists a name and the
stores keep uploads, so deleting a name takes every upload of it in that field, and the
same file in another field is left where it is. Answers already given keep their
citations and say the document is gone when you open one. Upload it again and it is
indexed again, which is the way back from a mistake.

## Effects, and the gate they wait at

And it acts, but only when you say so. A tool that declares it changes something outside
cora does not run on the model's word: the turn stops, the page shows the call — what the
tool says it does, and the arguments the model wrote — and nothing happens until you
approve it. Approve and it runs; decline and nothing outside cora has changed, the model
is told plainly, and the turn still answers. Ask travel to save the itinerary you worked
out and that is the shape of it: a card, then a file. A round that proposes two effects
stops twice and settles both before either runs, so picking the turn up never replays one
that already happened, and the trace carries the approval beside the call it authorised.

The gate is cora's own — a step of the core standing on the only path from the model to
its tools, which a plugin can neither switch off nor imitate, because no handler may stop
a turn. It covers what is declared to cora, which is every tool a plugin registered;
what a plugin's *own* code does inside a call is the trust you extend by loading it.

What an effect produces is a file you keep. It lands under `cora-output` — beside cora's
stores rather than in them, because everything in `.cora/` is bookkeeping a deployment may
delete and an itinerary you approved is not. `CORA_OUTPUT_PATH` moves it. A plugin is
handed the location rather than choosing one, and a filename that would climb out of it is
refused, so no plugin writes that check itself.

## Plugins, once they are loaded

A plugin you are finished with goes from the page as well. Its field carries the same
control the three rails carry, in the menu that lists the fields, and it asks first —
this takes more than anything else here. The plugin's files leave `.cora/plugins`, and
every field only it brought goes with them: the documents, their passages, and every
conversation pinned there. What cora remembers about you is left, and so is anything an
approved effect wrote, because those are yours rather than the field's. A symlink is
unlinked and what it points at is untouched, so a deployment that linked this repo's
plugins in loses the link and nothing else. A field the configuration named carries no
control, having no plugin behind it, and neither does one a module `CORA_PLUGINS` names
— that one is fixed at start and would be back at the next one.

A plugin keeps what it worked out. What it puts under a name of its own is there on the
next turn of that conversation, rides the same checkpoint the rest of the turn does, and
goes when the conversation is deleted — a plan it is still revising, a count it is
running, a form half filled in. That is a different thing from what cora remembers,
which is about the *user* and outlives every conversation. And its own work is on the
trace: a plugin running a loop of its own says what it just did, in a line cora signs
with the plugin's name, standing under the call it happened inside.
