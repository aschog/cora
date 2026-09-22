export type Citation = {
  number: number
  document: string
  start: number
  end: number
  upload: string
  /** The field it was ingested into, whose directory the text is kept under. A passage
   *  is opened where it was ingested, so both names are needed to read it back. */
  scope: string
}

export type Step = {
  summary: string
  detail: string
  failed: boolean
  /** 'core tool' or 'plugin tool'; empty when the step called none. */
  origin: string
  /** What the step did inside itself — a plugin's tool that ran a turn of its own. */
  steps: Step[]
}

export type Result = {
  answer: string
  citations: Citation[]
  trace: Step[]
  /** The fields it was answered in. Routing settles them inside the turn, so this is
   *  the only thing that says which — an unpinned conversation is answered in a field
   *  the page never chose. A turn that names one is a turn the rail can follow. */
  scopes: string[]
}

export type Turn = { question: string; result: Result }

/** One value on a card. `schema` is the JSON Schema the control is drawn from — the
 *  same schema a tool declares its parameters in. `editable` is false for a call put up
 *  to be read rather than filled. */
export type Asked = {
  name: string
  schema: Record<string, unknown>
  value: unknown
  editable: boolean
  required: boolean
}

/** One way off a card. `answer` is what travels back when it is taken, and `null` is the
 *  way out — a decline, or none of them. `needs_valid` holds it closed until every
 *  required field holds a value, and `settled` is what the card says once it was taken —
 *  blank where the action has nothing of its own to say. */
export type Offered = {
  label: string
  answer: string | null
  note: string
  needs_valid: boolean
  settled: string
}

/** What a stopped turn puts to the reader, whichever way it stopped. One shape over a
 *  decision, a proposal and a form to fill: the page draws it from this alone and knows
 *  nothing of what stopped the turn. */
export type Card = { prompt: string; fields: Asked[]; actions: Offered[] }

/** A turn parked on something the reader has to settle, with the question that opened
 *  it — a paused turn is in no store, so this is the only thing a card can be drawn
 *  under. */
export type Pending = { asked: string; card: Card }

/** How a turn ends: with an answer, or with something for the reader to settle. */
export type Reply = Result | Pending

/* Read off `asked`, which only a parked turn carries. */
export const paused = (reply: Reply): reply is Pending => 'asked' in reply

export type Fact = { key: string; text: string }

/** One conversation in the list, and the field it is fixed to — `null` where it is
 *  fixed to nothing. The pin rather than the fields its turns were answered in: the
 *  first is a decision about the conversation, the second a reading of one question. */
export type Session = {
  thread_id: string
  opened_with: string
  pin: string | null
}

/** The fields this deployment offers, the one a question belonging to none is answered
 *  in, and where the page of a field that brought one is served. A deployment with no
 *  field is a bare cora and has nothing to pin, and a field with no page is absent from
 *  `pages` rather than named with nothing. */
export type Scopes = {
  available: string[]
  default: string
  pages: Record<string, string>
}

/** One loaded plugin, as the page reads the listing. Both answers are cora's rather
 *  than the page's reading of them: only a plugin in the plugins folder can be deleted,
 *  and `going` is the fields deleting it would take — which is not every field it
 *  registered, because one something else also brings stays. The question a reader
 *  answers has to say what deleting takes, so it is not derived here twice. */
export type Plugin = {
  name: string
  scopes: string[]
  deletable: boolean
  going: string[]
}

const UNREADABLE = 'cora could not be reached.'
const NO_CONTENT = 204

async function read<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) throw new Error(await failure(response))
  return (await response.json()) as T
}

async function failure(response: Response): Promise<string> {
  try {
    const said = await response.json()
    return said?.error ?? UNREADABLE
  } catch {
    return UNREADABLE
  }
}

/* Every read takes the signal of the thing that wanted it. A page the reader has moved
   past is a page whose requests are still on the wire: the answers were always dropped,
   and this is what stops them being fetched at all. A write takes none — a delete the
   reader asked for is not undone by them looking elsewhere. */
export const documents = (scope: string, signal?: AbortSignal) =>
  read<string[]>(`/api/documents?scope=${encodeURIComponent(scope)}`, { signal })
export const scopes = (signal?: AbortSignal) => read<Scopes>('/api/scopes', { signal })
export const memory = (signal?: AbortSignal) => read<Fact[]>('/api/memory', { signal })
export const sessions = (signal?: AbortSignal) =>
  read<Session[]>('/api/conversations', { signal })
export const plugins = (signal?: AbortSignal) =>
  read<Plugin[]>('/api/plugins', { signal })
/* The one live value cora holds for a field, written by whatever is beside the reader
   rather than by this page. `at` is cora's own clock as the notice arrived; a field
   nobody has written to answers with none. */
export const notice = (scope: string, signal?: AbortSignal) =>
  read<{ notice: Record<string, unknown> | null; at?: number }>(
    `/api/scopes/${encodeURIComponent(scope)}/notice`,
    { signal },
  )
/* Every thread reaching a path is escaped on the way in — here, and in the three below
   that take one. The router already refuses an address that could mean a different path,
   and this is the same guard at the other end: one place every caller routes through,
   rather than a rule each new one has to know. */
export const turns = (thread: string, signal?: AbortSignal) =>
  read<Turn[]>(`/api/conversations/${encodeURIComponent(thread)}`, { signal })

export const passage = (scope: string, upload: string, signal?: AbortSignal) =>
  read<{ text: string }>(
    `/api/uploads/${encodeURIComponent(scope)}/${encodeURIComponent(upload)}`,
    { signal },
  ).then((kept) => kept.text)

/* The files a field keeps of its own, which are not its documents: nothing indexes,
   searches or cites them, and what the text means is that field's plugin's business.
   The name is one plain name, and cora refuses one that is not. */
export const fieldFiles = (scope: string, signal?: AbortSignal) =>
  read<{ names: string[] }>(
    `/api/scopes/${encodeURIComponent(scope)}/files`,
    { signal },
  ).then((held) => held.names)

export const fieldFile = (scope: string, name: string, signal?: AbortSignal) =>
  read<{ name: string; text: string }>(
    `/api/scopes/${encodeURIComponent(scope)}/files/${encodeURIComponent(name)}`,
    { signal },
  ).then((held) => held.text)

/** Write one of a field's own files, replacing what was under that name. Whoever writes
 *  sends the whole of it: merging is what the text means, which cora does not read. */
export const keepFieldFile = (scope: string, name: string, text: string) =>
  read<{ name: string; text: string }>(
    `/api/scopes/${encodeURIComponent(scope)}/files/${encodeURIComponent(name)}`,
    {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text }),
    },
  )

/** Delete one document from one field: its passages out of the index, and the file its
 *  citations opened onto. The name is what the field lists, and one name may be several
 *  uploads — all of them go, because the one entry is what the reader deleted. */
export const deleteDocument = (scope: string, name: string) =>
  discard(`/api/documents/${encodeURIComponent(scope)}/${encodeURIComponent(name)}`)

/** Delete one conversation: the turns recorded under it, and the thread they were
 *  answered on. One request, because a conversation whose record is gone and whose
 *  thread is not still holds a pin, a transcript and possibly a turn nobody can see. */
export const deleteSession = (thread: string) =>
  discard(`/api/conversations/${encodeURIComponent(thread)}`)

/** Delete one plugin: its entry in the plugins folder, the documents and passages of
 *  every field only it brought, and every conversation pinned to one of them. The name
 *  is the one the listing gives it, and cora resolves it against what it loaded. */
export const deletePlugin = (name: string) =>
  discard(`/api/plugins/${encodeURIComponent(name)}`)

export const forget = (key: string) =>
  discard(`/api/memory/${encodeURIComponent(key)}`)

export const forgetEverything = () => discard('/api/memory')

/**
 * A write whose success carries no body. The empty 204 is not parsed — reading it as
 * JSON would throw, and a blanket catch around that would swallow the 503 that says the
 * store went away, leaving the page to report the write as done.
 */
async function discard(path: string): Promise<void> {
  const response = await fetch(path, { method: 'DELETE' })
  if (response.status === NO_CONTENT) return
  if (!response.ok) throw new Error(await failure(response))
}

export async function upload(
  file: File,
  scope: string,
): Promise<{ document: string; chunks: number; scope: string }> {
  const carried = new FormData()
  carried.append('file', file)
  carried.append('scope', scope)
  return read('/api/documents', { method: 'POST', body: carried })
}

/**
 * One turn, read as it arrives. A question is a POST, which `EventSource` cannot send,
 * so the stream is a `fetch` body read frame by frame — and a frame can be split across
 * two reads, which is what the buffer is for.
 *
 * `onText` is what the model writes as it writes it. A turn may take several rounds and
 * only the last of them is the answer, so `onAside` says that the pieces before it were
 * a round that ended in a tool call — the pieces since the last one are the answer. The
 * turn this resolves with still carries it whole: the pieces are what the reader
 * watches, the whole is what the page keeps.
 *
 * A turn that stopped to ask resolves with a `Pending` instead of a `Result`, which is
 * not a failure: `resume` is what finishes it.
 *
 * `pin` is the field this conversation is fixed to, sent on every question while it holds
 * one: the pin lives in the thread's state and only a turn writes it there.
 */
export async function ask(
  question: string,
  thread: string,
  onStep: (step: Step) => void,
  onText: (piece: string) => void = () => {},
  onAside: () => void = () => {},
  pin: string | null = null,
): Promise<Reply> {
  return streamed(
    await post('/api/ask', {
      question,
      thread_id: thread,
      ...(pin === null ? {} : { pin }),
    }),
    onStep,
    onText,
    onAside,
  )
}

/**
 * The rest of a turn that stopped, on the action the reader took and what they wrote.
 * A second request rather than an answer written back up the first one: a stream only
 * goes one way, and the pause is parked where the turn was left.
 *
 * One call over every kind of card. `action` is the taken action's own `answer`, and
 * `null` is the way out; `values` is what the writable fields hold, and a card of none
 * settles on the action alone.
 */
export async function resume(
  thread: string,
  action: string | null,
  values: Record<string, unknown> = {},
  onStep: (step: Step) => void = () => {},
  onText: (piece: string) => void = () => {},
  onAside: () => void = () => {},
): Promise<Reply> {
  return streamed(
    await post('/api/resume', { thread_id: thread, answer: action, values }),
    onStep,
    onText,
    onAside,
  )
}

/** Which field a conversation is pinned to, or nothing. The pin is a key of the thread's
 *  own state, so this is what a reloaded page reads it back from. */
export const pinned = (thread: string, signal?: AbortSignal) =>
  read<{ pin: string | null }>(`/api/conversations/${encodeURIComponent(thread)}/scope`, {
    signal,
  }).then(
    (held) => held.pin,
  )

/** What a conversation is waiting on, or nothing. A page that arrived after the pause
 *  has nowhere else to look: the turn is recorded only once it has an answer. */
export const pending = (thread: string, signal?: AbortSignal) =>
  read<Pending | null>(`/api/conversations/${encodeURIComponent(thread)}/pending`, { signal })

const post = (path: string, body: unknown) =>
  fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

async function streamed(
  response: Response,
  onStep: (step: Step) => void,
  onText: (piece: string) => void,
  onAside: () => void,
): Promise<Reply> {
  if (!response.ok || !response.body) throw new Error(await failure(response))
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffered = ''
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffered += decoder.decode(value, { stream: true })
      let end: number
      while ((end = buffered.indexOf('\n\n')) >= 0) {
        const [event, data] = parsed(buffered.slice(0, end))
        buffered = buffered.slice(end + 2)
        if (event === 'step') onStep(data as Step)
        if (event === 'text') onText((data as { text: string }).text)
        if (event === 'aside') onAside()
        if (event === 'turn') return data as Result
        if (event === 'paused') return data as Pending
        if (event === 'error') throw new Error((data as { error: string }).error)
      }
    }
    throw new Error('The answer ended before it arrived.')
  } finally {
    /* The turn is the last thing on the wire, so returning at it leaves the reader
       holding a body nobody will read again. */
    await reader.cancel().catch(() => undefined)
  }
}

function parsed(frame: string): [string, unknown] {
  let event = ''
  let data = 'null'
  for (const line of frame.split('\n')) {
    const at = line.indexOf(': ')
    if (at < 0) continue
    const field = line.slice(0, at)
    if (field === 'event') event = line.slice(at + 2)
    if (field === 'data') data = line.slice(at + 2)
  }
  return [event, JSON.parse(data)]
}
