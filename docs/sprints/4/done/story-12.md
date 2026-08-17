# Story 12: It says when it has nothing to answer from

**As a** user who has uploaded nothing yet · **I want** cora to say it has no documents ·
**So that** I know to give it some, instead of reading an answer it made up

> **Given** the fitness plugin loaded and an empty store
> **When** I ask a training question
> **Then** cora says it has no documents on it and asks for some, citing nothing — and a
> greeting is still answered as a greeting

Today cora does the opposite. The gate searches, drops everything under the relevance floor,
and the shipped reminder ends "give the same answer again and cite nothing"
(`fitness/__init__.py:18-23`) — so a question in the plugin's own subject is answered from
model knowledge. That wording is what lets small talk through, which is why the fix is one
sentence and not a new step.

## The shape

`GroundStep` already holds both signals, with no new collaborator: `context_source.search`
returns top-k whatever the scores, which is why `EVIDENCE_FLOOR` exists (`steps.py:31`).

```
no hits at all          the store is empty        "you haven't uploaded anything yet"
hits, none above floor  nothing covers this       "your documents don't cover it"
hits above the floor    evidence to weigh         unchanged
```

Whether the question is in scope stays the model's call, as it is today — the reminder cora
words after story 11 step 4 is the whole change.

## Test list

**Tiers:** unit unless marked — **(int)** integration.

#### First, the outer test

- [x] **(int)** fitness loaded against an empty store: a training question is answered with
      the ask-for-documents message and cites nothing, while a greeting in the same run is
      answered as a greeting — `xfail(strict=True)`

#### The gate tells the two silences apart

- [x] `GroundStep` appends "nothing uploaded yet" when the search returns no hits at all
- [x] it appends "your documents don't cover this" when hits came back and none cleared the
      floor — today both cases render as the same "no matching documents"
- [x] hits above the floor are unchanged: the passages, under the untrusted-data label

#### What cora tells the model to do about it

- [x] the reminder says to answer that it has nothing on the question when a scope was
      declared and the passages are empty, and to answer as it did otherwise
- [x] a greeting against an empty store keeps its answer and cites nothing — story 8's
      behaviour, now under the new wording

#### Nothing else changed

- [x] `README.md` says cora asks for documents rather than answering without them

#### Found while building it

- [x] a search that *broke* claims neither silence: the gate cannot tell an empty store
      from an unreachable one, and it keeps today's wording and the answer in hand
- [x] a plugin that declared no scope claims neither either — there is nothing to call a
      question inside or outside of, so the message stays the passages it always was

## Out of scope

- **Refusing outright.** The model still writes the sentence; nothing short-circuits it.
- **A scope classifier.** Which questions belong to the documents stays the model's
  judgement, read off the plugin's scope phrase.
