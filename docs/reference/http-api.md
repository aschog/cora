# The HTTP surface

What the React shell's server answers, route by route. Running it is in
[run the React shell](../how-to/run-the-react-shell.md); the Streamlit page calls the
same `App` in process and has no surface of its own.

## The routes

| Route | Method | Answers |
|---|---|---|
| `/api/documents` | `GET` | the filenames cora holds |
| `/api/documents` | `POST` | a multipart upload: `{"document": …, "chunks": n}`, and `chunks: 0` for a file already uploaded |
| `/api/ask` | `POST` | one turn, as an event stream |
| `/api/resume` | `POST` | the label chosen for a question cora asked, as the same stream |
| `/api/uploads/{upload}` | `GET` | `{"text": …}` — the cleaned text a citation opens onto, `404` when the document was never kept |
| `/api/sessions` | `GET` | every conversation, newest first |
| `/api/sessions/{thread_id}` | `GET` | that conversation's turns, oldest first |
| `/api/sessions/{thread_id}/pending` | `GET` | the question a parked run stopped on, or nothing |
| `/api/memory` | `GET` | every fact kept about the user |
| `/api/memory` | `DELETE` | `204`, everything forgotten |
| `/api/memory/{key}` | `DELETE` | `204`, that fact forgotten |
| `/api/plugins` | `GET` | the plugins this deployment named |

A deployment with no memory or no conversations slot answers `[]` rather than failing:
what is missing is missing from the page too. Forgetting what was never kept is already
done, so a `DELETE` still answers `204`.

## A turn arrives as it happens

`POST /api/ask` and `POST /api/resume` answer `text/event-stream`, unbuffered. Each event
is a name and one JSON line:

| Event | Carries |
|---|---|
| `step` | one trace step, the moment it lands |
| `text` | one piece of the reply, as the model writes it |
| `aside` | that a round the model wrote in ended in a tool call |
| `turn` | the finished turn — the answer, its citations and its trace |
| `paused` | the question cora stopped to ask, and the ways out of it |
| `error` | one sentence, when the turn was refused |

A turn may take several rounds and only the last of them is the answer, so it is the
`text` pieces since the last `aside` that are the same text arriving early; the ones
before it were the model writing its way to a tool call, and a client drops them.

## What it refuses

`POST /api/documents` bounds the request before a byte of it is read, because the cap on
a *document* is applied only once the whole of it is in memory: `413` past 10 MB and the
framing a multipart body costs, and `411` for a body that declares no length at all — a
ceiling a client can step around by chunking is not a ceiling. `POST /api/ask` bounds its
own body on the reading instead, so it needs no declared length.

Every refusal the shell models arrives as `{"error": "<one sentence>"}` under the code and
headers it was raised with — cora's own (`400`), a store that went away (`503`), the form
parser's and Starlette's alike. `204` and `304` carry no body. A failure nobody modelled
is still the server's plain-text 500.
