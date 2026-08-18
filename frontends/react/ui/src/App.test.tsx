import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from './App'

/**
 * The steps that arrive *while* the turn runs say something the finished turn does not.
 * Sharing one summary between them would let the assertion pass off the turn's own
 * trace, with nothing streamed and nothing observed.
 */
const LIVE = [
  { summary: 'Reading your documents', detail: '', failed: false, origin: '' },
  {
    summary: 'Weighing the last 21 days',
    detail: 'training_log',
    failed: false,
    origin: 'plugin tool',
  },
]
const TURN = {
  answer: 'Sleep, not volume [1].',
  citations: [{ number: 1, document: 'notes.md', start: 0, end: 6, upload: 'u1' }],
  trace: [{ summary: 'Wrote the answer', detail: '', failed: false, origin: '' }],
}

const frame = (event: string, data: unknown) =>
  `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`

const held = () => {
  let release = () => {}
  const until = new Promise<void>((resolve) => (release = resolve))
  return { until, release: () => release() }
}

/** Renewed per test: a spec that fails before releasing must not hang the next one. */
let turn = held()

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

afterEach(() => {
  turn.release()
  cleanup()
})

beforeEach(() => {
  turn = held()
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
})

const KEPT = 'Sleep, not volume. The rest of the document follows.'


test('the plan fills while the turn runs, then the answer lands with its citation', async () => {
  render(<App />)

  expect(await screen.findByText('notes.md')).toBeTruthy()

  // The badge names the shell's plugin; the menu names the module it was loaded from.
  fireEvent.click(screen.getByRole('button', { name: /fitness/ }))
  expect(screen.getByText('cora.plugins.fitness')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: /fitness/ }))

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

  // The question and both steps are on the page before the answer exists at all.
  expect(await screen.findByText('Why am I stalling?')).toBeTruthy()
  expect(await screen.findByText(/Working/)).toBeTruthy()
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
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'anything' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()

  await screen.findByText(TURN.trace[0].summary)
  expect(screen.queryByText(broken.error)).toBeNull()
})

test('each rail folds away and comes back, and its toggle says which it is', async () => {
  render(<App />)
  expect(await screen.findByText('notes.md')).toBeTruthy()

  const documents = screen.getByRole('button', { name: 'Documents' })
  const rail = screen.getByRole('button', { name: 'Plan & memory' })
  expect(documents.getAttribute('aria-pressed')).toBe('true')

  fireEvent.click(documents)
  expect(screen.queryByText('notes.md')).toBeNull()
  expect(screen.getByRole('tab', { name: 'PLAN' })).toBeTruthy()
  expect(documents.getAttribute('aria-pressed')).toBe('false')

  fireEvent.click(rail)
  expect(screen.queryByRole('tab', { name: 'PLAN' })).toBeNull()
  expect(rail.getAttribute('aria-pressed')).toBe('false')

  fireEvent.click(documents)
  fireEvent.click(rail)
  expect(screen.getByText('notes.md')).toBeTruthy()
  expect(screen.getByRole('tab', { name: 'PLAN' })).toBeTruthy()
})


test('a document the answer cited opens in the source panel, marked at the passage', async () => {
  const { container } = render(<App />)

  expect(await screen.findByText('notes.md')).toBeTruthy()
  const inTheRail = screen.getByRole('button', { name: 'notes.md' })
  expect(inTheRail.hasAttribute('disabled')).toBe(true)

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  // Cited now, so the rail opens it — into SOURCE, marked where the citation falls.
  expect(inTheRail.hasAttribute('disabled')).toBe(false)
  fireEvent.click(inTheRail)

  expect(screen.getByRole('tab', { name: 'SOURCE' }).getAttribute('aria-selected')).toBe(
    'true',
  )
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(screen.getByText('1 cited passage · highlighted')).toBeTruthy()
  expect(container.querySelector('.doc-passage')?.textContent).toBe(
    KEPT.slice(0, 6),
  )
})

test('a document cited in an earlier turn is not marked for this one', async () => {
  render(<App />)
  await screen.findByText('notes.md')

  const ask = async () => {
    turn = held()
    fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
      target: { value: 'Why?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
    turn.release()
  }

  await ask()
  await screen.findByText(/Sleep, not volume/)

  // A second turn that rests on nothing: the panel speaks for the answer being read.
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return uncited()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  await ask()
  await screen.findByText(/Nothing in your documents/)

  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  expect(screen.getByText('not cited in this answer')).toBeTruthy()

  // Still openable: the text is there to read, with nothing marked in it.
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(document.querySelector('.doc-passage')).toBeNull()
})

/** A turn that cites nothing. */
function uncited(): Response {
  const encoder = new TextEncoder()
  const body = frame('turn', {
    answer: 'Nothing in your documents covers that.',
    citations: [],
    trace: [],
  })
  let sent = false
  const reader = {
    read: async () =>
      sent
        ? { done: true, value: undefined }
        : ((sent = true), { done: false, value: encoder.encode(body) }),
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}
