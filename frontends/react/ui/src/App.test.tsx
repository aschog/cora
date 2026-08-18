import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from './App'

/**
 * The steps that arrive *while* the turn runs say something the finished turn does not.
 * Sharing one summary between them would let the assertion pass off the turn's own
 * trace, with nothing streamed and nothing observed.
 */
const LIVE = [
  { summary: 'Reading your documents', detail: '', failed: false },
  { summary: 'Weighing the last 21 days', detail: 'training_log', failed: false },
]
const TURN = {
  answer: 'Sleep, not volume [1].',
  citations: [{ number: 1, document: 'notes.md', start: 0, end: 6, upload: 'u1' }],
  trace: [{ summary: 'Wrote the answer', detail: '', failed: false }],
}

const frame = (event: string, data: unknown) =>
  `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`

const held = () => {
  let release = () => {}
  const until = new Promise<void>((resolve) => (release = resolve))
  return { until, release: () => release() }
}

const turn = held()

/**
 * The answer stream, read in three parts. The second step is split across two reads, so
 * a client that drops what it has buffered loses it — and the turn is withheld until
 * the test lets it go, so anything asserted before that can only have been streamed.
 */
function answering(): Response {
  const encoder = new TextEncoder()
  const second = frame('step', LIVE[1])
  const cut = 20
  const parts = [
    frame('step', LIVE[0]) + second.slice(0, cut),
    second.slice(cut),
    frame('turn', TURN),
  ]
  let next = 0
  const reader = {
    read: async () => {
      if (next === parts.length) return { done: true, value: undefined }
      if (next === parts.length - 1) await turn.until
      return { done: false, value: encoder.encode(parts[next++]) }
    },
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}

const served: Record<string, unknown> = {
  '/api/documents': ['notes.md'],
  '/api/plugins': ['cora.plugins.fitness'],
  '/api/memory': [{ key: 'f1', text: 'No burpees.' }],
  '/api/sessions': [],
}

afterEach(cleanup)

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
})

test('the plan fills while the turn runs, then the answer lands with its citation', async () => {
  render(<App />)

  expect(await screen.findByText('notes.md')).toBeTruthy()
  expect(screen.getByText('cora.plugins.fitness')).toBeTruthy()

  fireEvent.change(screen.getByPlaceholderText(/Ask in your own words/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

  // Both steps are on the page before the answer exists at all.
  expect(await screen.findByText(LIVE[0].summary)).toBeTruthy()
  expect(await screen.findByText(LIVE[1].summary)).toBeTruthy()
  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()

  turn.release()

  expect(await screen.findByText(/Sleep, not volume/)).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Open cited source 1' })).toBeTruthy()
  expect(screen.getByText(TURN.trace[0].summary)).toBeTruthy()
})

test('a panel that could not be read says so, and stops saying it once it can', async () => {
  const broken = { error: 'The knowledge base is temporarily unavailable.' }
  let reachable = false
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/documents' && !reachable)
        return {
          ok: false,
          status: 503,
          json: async () => broken,
        } as unknown as Response
      if (path === '/api/ask') return answering()
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )

  render(<App />)

  expect(await screen.findByText(broken.error)).toBeTruthy()

  reachable = true
  fireEvent.change(screen.getByPlaceholderText(/Ask in your own words/), {
    target: { value: 'anything' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

  await screen.findByText(TURN.trace[0].summary)
  expect(screen.queryByText(broken.error)).toBeNull()
})
