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

export type Option = { label: string; note: string }

/** What cora stopped to have settled, in its own words. */
export type Decision = { question: string; options: Option[]; decline: string }

/** One call cora is about to make that would change something outside it: what the tool
 *  says it does, and the arguments the model wrote, so what is approved is this call and
 *  not the idea of it. `call_id` is what an answer is bound to — a round may propose two
 *  effects, and neither may be settled by the other's yes. */
export type Proposal = {
  call_id: string
  tool: string
  does: string
  arguments: Record<string, unknown>
}

/** A turn parked on something the reader has to settle, with the question that opened
 *  it — a paused turn is in no store, so this is the only thing a card can be drawn
 *  under. Exactly one of the two is filled: a thread stops one way at a time, and which
 *  way it stopped is which card the page draws. */
export type Pending = {
  asked: string
  decision: Decision | null
  proposal: Proposal | null
}

/** How a turn ends: with an answer, or with something for the reader to settle. */
export type Reply = Result | Pending

/* Read off `asked`, which only a parked turn carries: the other two keys are each filled
   in one kind of pause and null in the other, so neither of them tells the two apart. */
export const paused = (reply: Reply): reply is Pending => 'asked' in reply

export type Fact = { key: string; text: string }

export type Session = { thread_id: string; opened_with: string }

/** The fields this deployment offers, and the one a question belonging to none is
 *  answered in. A deployment with no field is a bare cora and has nothing to pin. */
export type Scopes = { available: string[]; default: string }

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

export const documents = (scope: string) =>
  read<string[]>(`/api/documents?scope=${encodeURIComponent(scope)}`)
export const scopes = () => read<Scopes>('/api/scopes')
export const memory = () => read<Fact[]>('/api/memory')
export const sessions = () => read<Session[]>('/api/sessions')
export const turns = (thread: string) => read<Turn[]>(`/api/sessions/${thread}`)

export const passage = (scope: string, upload: string) =>
  read<{ text: string }>(
    `/api/uploads/${encodeURIComponent(scope)}/${encodeURIComponent(upload)}`,
  ).then((kept) => kept.text)

/** Delete one conversation: the turns recorded under it, and the thread they were
 *  answered on. One request, because a conversation whose record is gone and whose
 *  thread is not still holds a pin, a transcript and possibly a turn nobody can see. */
export const deleteSession = (thread: string) => discard(`/api/sessions/${thread}`)

export const forget = (key: string) => discard(`/api/memory/${key}`)

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
 * The rest of a turn that stopped to ask, on the label the reader picked — or on `null`,
 * which is declining. A second request rather than an answer written back up the first
 * one: a stream only goes one way, and the pause is parked where the turn was left.
 */
export async function resume(
  thread: string,
  answer: string | null,
  onStep: (step: Step) => void,
  onText: (piece: string) => void = () => {},
  onAside: () => void = () => {},
): Promise<Reply> {
  return streamed(
    await post('/api/resume', { thread_id: thread, answer }),
    onStep,
    onText,
    onAside,
  )
}

/**
 * The rest of a turn that stopped to propose an effect, on the reader's yes or no. The
 * call is named, because the answer is bound to it and not to whichever effect happened
 * to be outstanding.
 */
export async function approve(
  thread: string,
  call: string,
  approved: boolean,
  onStep: (step: Step) => void,
  onText: (piece: string) => void = () => {},
  onAside: () => void = () => {},
): Promise<Reply> {
  return streamed(
    await post('/api/approve', { thread_id: thread, call_id: call, approved }),
    onStep,
    onText,
    onAside,
  )
}

/** Which field a conversation is pinned to, or nothing. The pin is a key of the thread's
 *  own state, so this is what a reloaded page reads it back from. */
export const pinned = (thread: string) =>
  read<{ pin: string | null }>(`/api/sessions/${thread}/scope`).then((held) => held.pin)

/** What a conversation is waiting on, or nothing. A page that arrived after the pause
 *  has nowhere else to look: the turn is recorded only once it has an answer. */
export const pending = (thread: string) =>
  read<Pending | null>(`/api/sessions/${thread}/pending`)

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
