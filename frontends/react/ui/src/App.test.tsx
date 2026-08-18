import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
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
let step = held()

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
    cancel: async () => {},
    read: async () => {
      if (next === parts.length) return { done: true, value: undefined }
      if (next === parts.length - 1) await turn.until
      return { done: false, value: encoder.encode(parts[next++]) }
    },
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}

const OLDER = {
  question: 'An older question',
  result: { answer: 'An older answer.', citations: [], trace: [] },
}

const served: Record<string, unknown> = {
  '/api/documents': ['notes.md'],
  '/api/plugins': ['cora.plugins.fitness'],
  '/api/memory': [{ key: 'f1', text: 'No burpees.' }],
  '/api/sessions': [{ thread_id: 'old', opened_with: OLDER.question }],
  '/api/sessions/old': [OLDER],
}

afterEach(() => {
  turn.release()
  step.release()
  cleanup()
})

beforeEach(() => {
  turn = held()
  step = held()
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

  // The answer replaced the turn that was waiting rather than following it.
  expect(screen.queryByText(/Working/)).toBeNull()
  expect(screen.queryAllByText('Why am I stalling?')).toHaveLength(1)
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
  /* A disabled button is out of the accessibility tree and its tooltip is unreliable,
     so the reason is on the page rather than on the control it explains. */
  expect(screen.getByText(/not cited in this conversation/)).toBeTruthy()

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  // Cited now, so the rail opens it — into SOURCE, marked where the citation falls.
  expect(inTheRail.hasAttribute('disabled')).toBe(false)
  expect(screen.queryByText(/not cited in this conversation/)).toBeNull()
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
    cancel: async () => {},
    read: async () =>
      sent
        ? { done: true, value: undefined }
        : ((sent = true), { done: false, value: encoder.encode(body) }),
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}


test('an answer never lands on a conversation that was replaced while it ran', async () => {
  /* A turn takes tens of seconds and only the Ask button is disabled while it does, so
     opening an earlier conversation mid-turn is ordinary use. Replacing "the last
     entry" would then delete that conversation's last turn and show, inside it, an
     answer computed on a thread the reader has left. */
  turn = held()
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  /* Released in the same tick as the reopen, because two responses landing in one task
     batch is ordinary — and a guard that reads a thread React has not committed yet
     would let the abandoned answer through exactly then. */
  turn.release()
  expect(await screen.findByText(OLDER.result.answer)).toBeTruthy()
  await new Promise((settle) => setTimeout(settle, 0))

  expect(screen.getByText(OLDER.result.answer)).toBeTruthy()
  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()
  expect(screen.queryByText('Why am I stalling?')).toBeNull()

  /* And the panels the answer would have steered are left alone too: a document the
     abandoned turn cited is not this conversation's to show, and showing it says
     something false about it — that its text was never kept, when the truth is that
     nothing here cites it. */
  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  const rail = within(document.querySelector('.rail-panels') as HTMLElement)
  expect(rail.queryByText('notes.md')).toBeNull()
  expect(rail.getByText(/passage an answer cites/)).toBeTruthy()
})

test('the conversation follows what just happened, answered or failed', async () => {
  /* happy-dom lays nothing out, so what is observable is the scroll the effect asks
     for — enough to catch the newest turn being left below the fold. */
  const { container } = render(<App />)
  await screen.findByText('notes.md')
  const scroller = container.querySelector('.scroller') as HTMLElement
  Object.defineProperty(scroller, 'scrollHeight', { value: 5000, configurable: true })
  scroller.scrollTop = 0

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)
  expect(scroller.scrollTop).toBe(5000)

  scroller.scrollTop = 0
  turn.release()
  await screen.findByText(/Sleep, not volume/)
  expect(scroller.scrollTop).toBe(5000)
})

/** A turn that takes a step and then fails, the failure held back until released. */
function failing(): Response {
  const encoder = new TextEncoder()
  const parts = [
    frame('step', LIVE[0]),
    frame('error', { error: 'cora is away.' }),
  ]
  let next = 0
  const reader = {
    cancel: async () => {},
    read: async () => {
      if (next === parts.length) return { done: true, value: undefined }
      if (next === parts.length - 1) await turn.until
      return { done: false, value: encoder.encode(parts[next++]) }
    },
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}

test('a turn that fails says so where the answer would have been, and is scrolled to', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return failing()
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  const { container } = render(<App />)
  await screen.findByText('notes.md')
  const scroller = container.querySelector('.scroller') as HTMLElement
  Object.defineProperty(scroller, 'scrollHeight', { value: 5000, configurable: true })

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)

  /* The turn it replaces was already scrolled to; a failure that lands in its place
     changes neither the count of turns nor any answer, so nothing follows it down. */
  scroller.scrollTop = 0
  turn.release()

  expect(await screen.findByText('cora is away.')).toBeTruthy()
  expect(screen.queryByText(/Working/)).toBeNull()
  expect(screen.queryAllByText('Why am I stalling?')).toHaveLength(1)
  expect(scroller.scrollTop).toBe(5000)
})

test('a citation wrapped in a link the model wrote opens the passage, not the link', async () => {
  /* The answer is written over documents cora read, so a link around a citation is a
     link the reader never chose. Letting the anchor fire navigates the tab away on a
     click the page itself invited. */
  const linked = {
    answer: 'See [the log [1]](#elsewhere).',
    citations: TURN.citations,
    trace: TURN.trace,
  }
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return oneTurn(linked)
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

  /* A fragment rather than a URL: the click's default action is what this is about,
     and a unit test has no business dialling a host to find that out. */
  const cite = await screen.findByRole('button', { name: 'Open cited source 1' })
  const click = new MouseEvent('click', { bubbles: true, cancelable: true })
  cite.dispatchEvent(click)

  expect(click.defaultPrevented).toBe(true)
  expect(await screen.findByRole('dialog')).toBeTruthy()
})

/** A stream carrying one finished turn and nothing held back. */
function oneTurn(result: unknown): Response {
  const encoder = new TextEncoder()
  let sent = false
  const reader = {
    cancel: async () => {},
    read: async () =>
      sent
        ? { done: true, value: undefined }
        : ((sent = true), { done: false, value: encoder.encode(frame('turn', result)) }),
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}


/** A turn whose second step is held back, so a reopen can happen between the two. */
function steppingSlowly(): Response {
  const encoder = new TextEncoder()
  const parts = [
    frame('step', { ...LIVE[0], summary: 'Before the reopen' }),
    frame('step', { ...LIVE[1], summary: 'After the reopen' }),
    frame('turn', TURN),
  ]
  let next = 0
  const reader = {
    cancel: async () => {},
    read: async () => {
      if (next === parts.length) return { done: true, value: undefined }
      if (next === 1) await step.until
      if (next === 2) await turn.until
      return { done: false, value: encoder.encode(parts[next++]) }
    },
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}

test('a conversation shows its own plan, not the plan of a turn left behind', async () => {
  /* The panel's own footer says cora chose these steps — for what is on screen. A turn
     the reader walked away from is another conversation's work: it must neither go on
     filling this panel nor leave behind what it had already filled. */
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return steppingSlowly()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  expect(await screen.findByText('Before the reopen')).toBeTruthy()

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)
  step.release()
  await new Promise((settle) => setTimeout(settle, 0))

  fireEvent.click(screen.getByRole('tab', { name: 'PLAN' }))
  expect(screen.queryByText('After the reopen')).toBeNull()
  expect(screen.queryByText('Before the reopen')).toBeNull()
  // The request is still in flight, so cora is still answering one question.
  expect(screen.getByRole('button', { name: 'Ask' }).hasAttribute('disabled')).toBe(true)
})

const FIRST = 'Older, and nobody is reading this copy now.'
const SECOND = 'Newer, and this is the copy the answer cited.'

test('a filename uploaded twice is read at the upload this answer cited', async () => {
  /* A span means nothing without the text it was measured in, and one filename can name
     two uploads — the rail lists names, the store keeps text per upload. Taking the
     upload from one citation and the offsets from another marks passages that were
     never cited, in a copy of the document nobody asked about. */
  const copies = [
    {
      answer: 'From the first copy [1].',
      citations: [{ number: 1, document: 'notes.md', start: 0, end: 5, upload: 'u1' }],
      trace: [],
    },
    {
      answer: 'From the second copy [1].',
      citations: [{ number: 1, document: 'notes.md', start: 0, end: 5, upload: 'u2' }],
      trace: [],
    },
  ]
  let asked = 0
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return oneTurn(copies[asked++] ?? copies[1])
      if (path === '/api/uploads/u1')
        return { ok: true, json: async () => ({ text: FIRST }) } as unknown as Response
      if (path === '/api/uploads/u2')
        return { ok: true, json: async () => ({ text: SECOND }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  const { container } = render(<App />)
  await screen.findByText('notes.md')

  const ask = async (question: string) => {
    fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
      target: { value: question },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  }

  await ask('Which copy?')
  await screen.findByText(/From the first copy/)
  await ask('And now?')
  await screen.findByText(/From the second copy/)

  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))

  expect(await screen.findByText(/the copy the answer cited/)).toBeTruthy()
  expect(screen.queryByText(/nobody is reading this copy/)).toBeNull()
  expect(container.querySelector('.doc-passage')?.textContent).toBe(SECOND.slice(0, 5))
})

test('a question in flight does not un-cite the answer still on screen', async () => {
  /* A turn takes tens of seconds, and the answer being read is still the answer being
     read. The question joins the thread the moment it is asked and carries no citations
     yet — reading that as "this answer" strips the marks off the one on the page and
     says it rests on nothing. */
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  expect(await screen.findByText('1 cited passage · highlighted')).toBeTruthy()

  turn = held()
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'And next?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText('And next?')

  // Back to the passage while cora works: the answer above it has not changed.
  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(screen.getByText('1 cited passage · highlighted')).toBeTruthy()
  expect(document.querySelector('.doc-passage')?.textContent).toBe(KEPT.slice(0, 6))
})

test('a turn that failed does not un-cite the answer still on screen', async () => {
  /* The other half of the same criterion: a failure lands where the answer would have
     been and carries no citations, and it carries no `pending` flag either. Reading it as
     "this answer" tells the reader that the answer above it — the one with the marks —
     rests on nothing, about a turn that produced no answer at all. */
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  expect(await screen.findByText('1 cited passage · highlighted')).toBeTruthy()

  turn = held()
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return failing()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'And next?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText('cora is away.')

  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(screen.getByText('1 cited passage · highlighted')).toBeTruthy()
  expect(document.querySelector('.doc-passage')?.textContent).toBe(KEPT.slice(0, 6))
})

test('an answer returning to the conversation it was asked in is not dropped', async () => {
  /* Leaving a conversation mid-turn drops the reply — that turn is another
     conversation's now. Coming *back* to it is not leaving it: the thread guard passes,
     but the reopen renumbered the entries, so the turn matched nothing and landed
     nowhere. The reader had to open the conversation a third time to find it. */
  vi.stubGlobal('crypto', { randomUUID: () => 'here' })
  let recorded = false
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions')
        return {
          ok: true,
          json: async () => [
            { thread_id: 'old', opened_with: OLDER.question },
            { thread_id: 'here', opened_with: 'Why am I stalling?' },
          ],
        } as unknown as Response
      // The store has the turn once the turn is over, and not before.
      if (path === '/api/sessions/here')
        return {
          ok: true,
          json: async () =>
            recorded ? [{ question: 'Why am I stalling?', result: TURN }] : [],
        } as unknown as Response
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(LIVE[0].summary)

  // Away, and straight back — both while the turn is still running.
  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)
  fireEvent.click(await screen.findByRole('button', { name: 'Why am I stalling?' }))
  await new Promise((settle) => setTimeout(settle, 0))

  recorded = true
  turn.release()

  expect(await screen.findByText(/Sleep, not volume/)).toBeTruthy()
  // Once in the conversation — the other one on the page is the session it names.
  expect([...document.querySelectorAll('.said')].map((each) => each.textContent)).toEqual(
    ['Why am I stalling?'],
  )
})
