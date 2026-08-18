import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'

const SEARCH = 'search_documents(query="squats") → 2 passages'
const STEPS = [
  { summary: SEARCH, detail: 'notes.md', failed: false },
  { summary: 'Decided no tool was needed', detail: '', failed: false },
]
const TURN = {
  answer: 'Sleep, not volume [1].',
  citations: [{ number: 1, document: 'notes.md', start: 0, end: 6, upload: 'u1' }],
  trace: STEPS,
}

const frame = (event: string, data: unknown) =>
  `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`

/** The answer stream, delivered in two reads so the client has to buffer. */
function answering(): Response {
  const encoder = new TextEncoder()
  const parts = [
    frame('step', STEPS[0]) + frame('step', STEPS[1]).slice(0, 12),
    frame('step', STEPS[1]).slice(12) + frame('turn', TURN),
  ]
  let next = 0
  const reader = {
    read: async () =>
      next < parts.length
        ? { done: false, value: encoder.encode(parts[next++]) }
        : { done: true, value: undefined },
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}

const served: Record<string, unknown> = {
  '/api/documents': ['notes.md'],
  '/api/plugins': ['cora.plugins.fitness'],
  '/api/memory': [{ key: 'f1', text: 'No burpees.' }],
  '/api/sessions': [],
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
})

test('a question fills the plan, renders the answer, and its citation is a button', async () => {
  render(<App />)

  expect(await screen.findByText('notes.md')).toBeTruthy()
  expect(screen.getByText('cora.plugins.fitness')).toBeTruthy()

  fireEvent.change(screen.getByPlaceholderText(/Ask in your own words/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

  expect(await screen.findByText(/Sleep, not volume/)).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Open cited source 1' })).toBeTruthy()
  expect(screen.getByText(SEARCH)).toBeTruthy()
})
