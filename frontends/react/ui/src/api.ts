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
}

export type Result = { answer: string; citations: Citation[]; trace: Step[] }

export type Turn = { question: string; result: Result }

export type Fact = { key: string; text: string }

export type Session = { thread_id: string; opened_with: string }

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
export const plugins = () => read<string[]>('/api/plugins')
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
 */
export async function ask(
  question: string,
  thread: string,
  onStep: (step: Step) => void,
): Promise<Result> {
  const response = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, thread_id: thread }),
  })
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
        if (event === 'turn') return data as Result
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
