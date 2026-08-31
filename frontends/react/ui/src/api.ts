export type Citation = {
  number: number
  document: string
  start: number
  end: number
  upload: string
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

export type Result = { answer: string; citations: Citation[]; trace: Step[] }

export type Turn = { question: string; result: Result }

export type Option = { label: string; note: string }

/** What cora stopped to have settled, in its own words. */
export type Decision = { question: string; options: Option[]; decline: string }

/** A turn parked on a decision, with the question that opened it — a paused turn is in
 *  no store, so this is the only thing the card can be drawn under. */
export type Pending = { asked: string; decision: Decision }

/** How a turn ends: with an answer, or with a question for the reader. */
export type Reply = Result | Pending

export const paused = (reply: Reply): reply is Pending => 'decision' in reply

export type Fact = { key: string; text: string }

export type Session = { thread_id: string; opened_with: string }

/** The fields this deployment offers, and the one a question belonging to none is
 *  answered in. A deployment with no field is a bare cora and has nothing to pin. */
export type Scopes = { available: string[]; default: string }

/** One registration as the menu draws it. `scope: null` is a claim on every turn. */
export type Contribution = { kind: string; name: string; scope: string | null }

export type Plugin = {
  name: string
  source: string
  scopes: string[]
  contributions: Contribution[]
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

export const documents = () => read<string[]>('/api/documents')
export const plugins = () => read<Plugin[]>('/api/plugins')
export const scopes = () => read<Scopes>('/api/scopes')
export const memory = () => read<Fact[]>('/api/memory')
export const sessions = () => read<Session[]>('/api/sessions')
export const turns = (thread: string) => read<Turn[]>(`/api/sessions/${thread}`)

export const passage = (upload: string) =>
  read<{ text: string }>(`/api/uploads/${upload}`).then((kept) => kept.text)

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

export async function upload(file: File): Promise<{ document: string; chunks: number }> {
  const carried = new FormData()
  carried.append('file', file)
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
