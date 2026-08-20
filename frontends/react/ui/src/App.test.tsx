import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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

/** Everything already queued has run — used where what is asserted is that something did
 *  *not* happen, and there is no observable arrival to wait for. */
const flushed = () => new Promise((settle) => setTimeout(settle, 0))

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
  globalThis.sessionStorage?.clear()
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
  expect(screen.getByRole('tab', { name: 'STEPS' })).toBeTruthy()
  expect(documents.getAttribute('aria-pressed')).toBe('false')

  fireEvent.click(rail)
  expect(screen.queryByRole('tab', { name: 'STEPS' })).toBeNull()
  expect(rail.getAttribute('aria-pressed')).toBe('false')

  fireEvent.click(documents)
  fireEvent.click(rail)
  expect(screen.getByText('notes.md')).toBeTruthy()
  expect(screen.getByRole('tab', { name: 'STEPS' })).toBeTruthy()
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
  expect(screen.getByRole('heading', { name: 'notes.md' })).toBeTruthy()
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
  await flushed()

  expect(screen.getByText(OLDER.result.answer)).toBeTruthy()
  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()
  expect(screen.queryByText('Why am I stalling?')).toBeNull()

  /* And the panels the answer would have steered are left alone too: a document the
     abandoned turn cited is not this conversation's to show, and showing it says
     something false about it — that its text was never kept, when the truth is that
     nothing here cites it. */
  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  const panels = document.querySelector('.rail-panels') as HTMLElement
  expect(within(panels).queryByText('notes.md')).toBeNull()
  expect(within(panels).queryByRole('heading', { name: 'notes.md' })).toBeNull()
})

test('the conversation follows what just happened, answered or failed', async () => {
  /* happy-dom lays nothing out, so what is observable is the scroll the effect asks
     for — enough to catch the newest turn being left below the fold.

     Awaited rather than read once: the scroll is a passive effect, which React flushes
     after the commit that `findByText` is already satisfied by. Reading it on the next
     line asserts that the effect has *already* run, which is a race the test never meant
     to make — and the assertion is the same either way, because it must still reach the
     bottom. */
  const { container } = render(<App />)
  await screen.findByText('notes.md')
  const scroller = container.querySelector('.scroller') as HTMLElement
  atTheBottom(scroller)

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)
  await waitFor(() => expect(scroller.scrollTop).toBe(5000))

  turn.release()
  await screen.findByText(/Sleep, not volume/)
  await waitFor(() => expect(scroller.scrollTop).toBe(5000))
})

/** A scroller the reader is at the bottom of, which happy-dom lays out as nothing at all:
 *  it reports every box as zero, so both the room and the reader's place in it are said
 *  here rather than measured. */
function atTheBottom(scroller: HTMLElement): void {
  Object.defineProperty(scroller, 'scrollHeight', { value: 5000, configurable: true })
  Object.defineProperty(scroller, 'clientHeight', { value: 800, configurable: true })
  scroller.scrollTop = 4200
}

/** The same scroller, with the reader some way up it. */
function scrolledUp(scroller: HTMLElement): void {
  atTheBottom(scroller)
  scroller.scrollTop = 0
  fireEvent.scroll(scroller)
}

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
  atTheBottom(scroller)

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)

  /* The turn it replaces was already scrolled to; a failure that lands in its place
     changes neither the count of turns nor any answer, so nothing follows it down. */
  scroller.scrollTop = 4200
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
  /* The panel shows the steps behind what is on screen. A turn the reader walked away
     from is another conversation's work: it must neither go on filling this panel nor
     leave behind what it had already filled. */
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
  await flushed()

  fireEvent.click(screen.getByRole('tab', { name: 'STEPS' }))
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
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(document.querySelector('.doc-passage')?.textContent).toBe(KEPT.slice(0, 6))

  turn = held()
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'And next?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText('And next?')

  // Back to the passage while cora works: the answer above it has not changed.
  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
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
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(document.querySelector('.doc-passage')?.textContent).toBe(KEPT.slice(0, 6))

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
  await flushed()

  recorded = true
  turn.release()

  expect(await screen.findByText(/Sleep, not volume/)).toBeTruthy()
  // Once in the conversation — the other one on the page is the session it names.
  expect([...document.querySelectorAll('.said')].map((each) => each.textContent)).toEqual(
    ['Why am I stalling?'],
  )
})

test('a conversation that loads late does not overwrite the one the reader is in', async () => {
  /* Every load of a conversation is a race with the reader: they can open another one
     while it is in flight, or the same one again, and the response that arrives last is
     not the conversation they asked for last. Putting one thread's turns under another
     thread's name is what the whole guard around a reply exists to prevent. */
  vi.stubGlobal('crypto', { randomUUID: () => 'here' })
  const slow = held()
  let recorded = false
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions')
        return body([
          { thread_id: 'old', opened_with: OLDER.question },
          { thread_id: 'here', opened_with: 'Why am I stalling?' },
        ])
      if (path === '/api/sessions/here') {
        // The re-read that follows the answer is the one held open.
        if (recorded) await slow.until
        return body(recorded ? [{ question: 'Why am I stalling?', result: TURN }] : [])
      }
      if (path === '/api/sessions/old') return body([OLDER])
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(LIVE[0].summary)

  const sessions = () => {
    fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
    return screen
  }
  fireEvent.click(await sessions().findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)
  fireEvent.click(await screen.findByRole('button', { name: 'Why am I stalling?' }))
  await flushed()

  // The answer lands, so the thread is re-read from the store — and while that is in
  // flight the reader opens the other conversation.
  recorded = true
  turn.release()
  await flushed()
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)

  slow.release()
  await flushed()

  expect(screen.getByText(OLDER.result.answer)).toBeTruthy()
  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()
  // And it is the conversation the reader is in: the panel disables the current one.
  expect(
    screen.getByRole('button', { name: OLDER.question }).hasAttribute('disabled'),
  ).toBe(true)
})

const EARLIER = {
  question: 'An earlier question in this thread',
  result: { answer: 'An earlier answer.', citations: [], trace: [] },
}

test('the question in flight stays with the conversation it was asked in', async () => {
  /* A turn is not one of the turns the store has — it is a question being asked in a
     thread. Leaving that conversation and coming back re-read the store, which does not
     know about it yet: the reader found a thread where they had asked nothing, no plan,
     and a composer they could not type in, for as long as the model took. */
  vi.stubGlobal('crypto', { randomUUID: () => 'here' })
  let recorded = false
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions')
        return body([
          { thread_id: 'old', opened_with: OLDER.question },
          { thread_id: 'here', opened_with: EARLIER.question },
        ])
      // The store has the turn once the turn is over, and not before.
      if (path === '/api/sessions/here')
        return body(
          recorded
            ? [EARLIER, { question: 'Why am I stalling?', result: TURN }]
            : [EARLIER],
        )
      if (path === '/api/sessions/old') return body([OLDER])
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(LIVE[0].summary)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)

  // In the other conversation the running turn is not on the page at all: it is not
  // this conversation's question, and it is not being asked here.
  expect([...document.querySelectorAll('.said')].map((each) => each.textContent)).toEqual(
    [OLDER.question],
  )
  expect(screen.queryByText(/Working/)).toBeNull()

  fireEvent.click(await screen.findByRole('button', { name: EARLIER.question }))
  await screen.findByText(EARLIER.result.answer)

  // Back in the conversation the turn is running in: its question, its plan, and a
  // composer whose disabling the plan explains.
  expect([...document.querySelectorAll('.said')].map((each) => each.textContent)).toEqual(
    [EARLIER.question, 'Why am I stalling?'],
  )
  expect(screen.getByText(/Working/)).toBeTruthy()
  expect(screen.queryByText(/still answering/)).toBeNull()
  fireEvent.click(screen.getByRole('tab', { name: 'STEPS' }))
  expect(screen.getByText(LIVE[0].summary)).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Ask' }).hasAttribute('disabled')).toBe(true)

  recorded = true
  turn.release()

  expect(await screen.findByText(/Sleep, not volume/)).toBeTruthy()
  expect([...document.querySelectorAll('.said')].map((each) => each.textContent)).toEqual(
    [EARLIER.question, 'Why am I stalling?'],
  )
})

test('the header offers a way to start a new session', async () => {
  render(<App />)
  await screen.findByText('notes.md')

  expect(screen.getByRole('button', { name: 'New session' })).toBeTruthy()
})

test('starting a new session takes the conversation off the page', async () => {
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  expect(screen.queryByText('Why am I stalling?')).toBeNull()
  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()
})

test('the question asked after a new session runs on another thread', async () => {
  /* A new session that reused the thread would go on appending to the conversation the
     reader just left — off the page, but in the store, and in the model's context. */
  const asked: string[] = []
  /* Named here rather than left to the environment: another spec pins `randomUUID` to a
     constant, and a thread that never changes is exactly what this asserts against. */
  let minted = 0
  vi.stubGlobal('crypto', { randomUUID: () => `t${++minted}` })
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/ask') {
        asked.push(JSON.parse(String(init?.body)).thread_id)
        return answering()
      }
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  const ask = async (question: string) => {
    turn = held()
    fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
      target: { value: question },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
    turn.release()
    await screen.findByText(/Sleep, not volume/)
  }

  await ask('Why am I stalling?')
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  await ask('And now?')

  expect(asked).toHaveLength(2)
  expect(asked[0]).toBeTruthy()
  expect(asked[1]).not.toBe(asked[0])
})

test('the new session is not offered while the conversation is already new', async () => {
  /* Nothing to start: the page is already an empty conversation on an unused thread, and
     a control that changes nothing is not a control. A question in flight is a
     conversation — asked and unanswered is something to leave. */
  render(<App />)
  await screen.findByText('notes.md')
  const start = screen.getByRole('button', { name: 'New session' })
  const unavailable = () => start.getAttribute('aria-disabled') === 'true'
  expect(unavailable()).toBe(true)

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)
  expect(unavailable()).toBe(false)

  turn.release()
  await screen.findByText(/Sleep, not volume/)
  expect(unavailable()).toBe(false)

  fireEvent.click(start)
  expect(unavailable()).toBe(true)
})

test('the panels afterwards speak for the new session, not the one left behind', async () => {
  /* The plan panel shows the steps behind what is on screen, and the source panel marks
     what this answer rested on. With the conversation gone, both would be speaking for a
     turn the reader can no longer see. */
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)
  expect(screen.getByText(TURN.trace[0].summary)).toBeTruthy()
  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  const panels = document.querySelector('.rail-panels') as HTMLElement
  expect(within(panels).queryByRole('heading', { name: 'notes.md' })).toBeNull()
  fireEvent.click(screen.getByRole('tab', { name: 'STEPS' }))
  expect(screen.queryByText(TURN.trace[0].summary)).toBeNull()
  expect(panels.querySelector('.plan-step')).toBeNull()
})

test('an answer to the conversation left behind does not land on the new session', async () => {
  /* Starting over mid-turn is leaving that conversation: the turn is recorded on the
     thread it was asked in, and the reader can reopen it under SESSIONS. What it must
     never do is arrive in the empty conversation they moved to. */
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  expect(screen.queryByText('Why am I stalling?')).toBeNull()

  turn.release()
  await flushed()

  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()
  expect(screen.queryByText('Why am I stalling?')).toBeNull()
})

test('the conversation left behind is listed under SESSIONS', async () => {
  /* Starting over is not throwing away: what was asked is checkpointed under its own
     thread, and the only way back to it is the sessions list. */
  let minted = 0
  vi.stubGlobal('crypto', { randomUUID: () => `t${++minted}` })
  let recorded = false
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      // The store has the conversation once its first turn is over, and not before.
      if (path === '/api/sessions')
        return body(recorded ? [{ thread_id: 't1', opened_with: 'Why am I stalling?' }] : [])
      if (path.startsWith('/api/uploads/'))
        return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  recorded = true
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))

  const listed = await screen.findByRole('button', { name: 'Why am I stalling?' })
  // Reopenable: the conversation is no longer the one the reader is in.
  expect(listed.hasAttribute('disabled')).toBe(false)
})

test('a reopen still loading when a new session starts does not land on it', async () => {
  /* Changing which conversation the page is in is a race with the store: `loads` exists
     so the reader's last choice wins. A new session that did not enter that race was
     undone by a reopen resolving after it — dropping the reader back into the
     conversation they had just left, on its thread, with the next question appending
     to it. */
  const slow = held()
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions/old') {
        await slow.until
        return body([OLDER])
      }
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  slow.release()
  await flushed()

  expect(screen.queryByText(OLDER.result.answer)).toBeNull()
  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()
})

test('a turn left running says so where the question would be typed, and lands in its own conversation', async () => {
  /* cora answers one question at a time, so starting over mid-turn leaves a page whose
     composer cannot be typed in — with the question, the plan and the banner all
     belonging to the conversation left behind, there was nothing on screen to say why,
     and nothing to say the answer was not lost. */
  let minted = 0
  vi.stubGlobal('crypto', { randomUUID: () => `t${++minted}` })
  let recorded = false
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions')
        return body(
          recorded ? [{ thread_id: 't1', opened_with: 'Why am I stalling?' }] : [],
        )
      if (path === '/api/sessions/t1')
        return body(recorded ? [{ question: 'Why am I stalling?', result: TURN }] : [])
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)
  // Asked here, so nothing says it was asked elsewhere.
  expect(screen.queryByText(/still answering/)).toBeNull()

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  // The page is empty and cannot be asked in, and it says which of those is why.
  expect(screen.getByRole('button', { name: 'Ask' }).hasAttribute('disabled')).toBe(true)
  expect(screen.getByText(/still answering .* conversation you left/)).toBeTruthy()

  recorded = true
  turn.release()

  await screen.findByRole('tab', { name: 'SESSIONS' })
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Ask' }).hasAttribute('disabled')).toBe(
      false,
    ),
  )
  expect(screen.queryByText(/still answering/)).toBeNull()

  // Nothing was thrown away: the answer is in the conversation it was asked in.
  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Why am I stalling?' }))
  expect(await screen.findByText(/Sleep, not volume/)).toBeTruthy()
})

test('a banner raised by the conversation left behind does not follow the new session', async () => {
  /* The banner speaks for one load of one conversation. Carried into a new session it is
     a failure the reader cannot act on, about a page it did not happen to. */
  const unreachable = 'The conversation store is temporarily unavailable.'
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions/old')
        return {
          ok: false,
          status: 503,
          json: async () => ({ error: unreachable }),
        } as unknown as Response
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  expect(await screen.findByText(unreachable)).toBeTruthy()

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  await waitFor(() => expect(screen.queryByText(unreachable)).toBeNull())
})

test('the control is reachable while it is unavailable, and clicking it then changes nothing', async () => {
  /* A `disabled` button is out of the accessibility tree — the same reason the rail's
     documents explain themselves on the page rather than in a tooltip. Unavailable is
     something to be told, so the control stays reachable and does nothing. */
  const asked: string[] = []
  let minted = 0
  vi.stubGlobal('crypto', { randomUUID: () => `t${++minted}` })
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/ask') {
        asked.push(JSON.parse(String(init?.body)).thread_id)
        return answering()
      }
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  const start = screen.getByRole('button', { name: 'New session' })
  expect(start.getAttribute('aria-disabled')).toBe('true')
  expect(start.hasAttribute('disabled')).toBe(false)

  // Unavailable, and it says why rather than leaving a dead control to guess at.
  const why = document.getElementById(start.getAttribute('aria-describedby') ?? '')
  expect(why?.textContent).toMatch(/already in a new session/)

  fireEvent.click(start)
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  // The thread the page opened with: the click minted nothing.
  expect(asked).toEqual(['t1'])
  // And with something to leave, the control carries no reason not to.
  expect(start.hasAttribute('aria-describedby')).toBe(false)
})

test('a conversation load that lost the race says nothing about it', async () => {
  /* The banner speaks for the page. A load the reader walked away from has nothing to
     tell them: it reported a failure they cannot act on, about a conversation that is not
     on screen — the other half of the property above, in the order where the failure
     arrives last. */
  const unreachable = 'The conversation store is temporarily unavailable.'
  const slow = held()
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions/old') {
        await slow.until
        return {
          ok: false,
          status: 503,
          json: async () => ({ error: unreachable }),
        } as unknown as Response
      }
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  slow.release()
  await flushed()

  expect(screen.queryByText(unreachable)).toBeNull()
})

test('a question left running that fails says so, rather than never arriving', async () => {
  /* The reader was told the answer would be listed under SESSIONS when it lands. A turn
     that fails is recorded nowhere, so nothing would ever be listed and nothing would
     ever be said: they wait for an answer that no longer exists. */
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return failing()
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  turn.release()

  expect(await screen.findByText(/conversation you left.*cora is away\./)).toBeTruthy()
  // Said about the conversation, not *in* the empty one: the failed turn is not dragged
  // onto a page it was never asked on.
  expect(screen.queryByText('Why am I stalling?')).toBeNull()
  expect(document.querySelector('.turn')).toBeNull()

  // Until the reader asks the next question, which is them moving on from it.
  turn = held()
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'And now?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

  expect(screen.queryByText(/conversation you left.*cora is away\./)).toBeNull()
})

test('a turn that fails while a reopen is loading is not swallowed by it', async () => {
  /* A failure is appended to the conversation on screen — but a load already in flight
     replaces that conversation wholesale, and takes the failure with it. `here.current`
     says where the last load *put* the reader, not what they have asked for next. */
  const slow = held()
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return failing()
      if (path === '/api/sessions/old') {
        await slow.until
        return body([OLDER])
      }
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  turn.release()
  await flushed()
  slow.release()

  expect(await screen.findByText(OLDER.result.answer)).toBeTruthy()
  expect(screen.getByText(/conversation you left.*cora is away\./)).toBeTruthy()
})

test('the failure of a question you left is not still said once you are back in it', async () => {
  /* "In the conversation you left" is a claim about where the reader is. Reopening that
     conversation makes it false, and it stood until the next question was asked. */
  let minted = 0
  vi.stubGlobal('crypto', { randomUUID: () => `t${++minted}` })
  let asks = 0
  let recorded = false
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      // The first question is answered and checkpointed; the second one fails.
      if (path === '/api/ask') return asks++ === 0 ? answering() : failing()
      if (path === '/api/sessions')
        return body(recorded ? [{ thread_id: 't1', opened_with: 'First question' }] : [])
      if (path === '/api/sessions/t1')
        return body(recorded ? [{ question: 'First question', result: TURN }] : [])
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  const ask = (question: string) => {
    turn = held()
    fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
      target: { value: question },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  }

  ask('First question')
  recorded = true
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  ask('And now?')
  await screen.findByText(/Working/)
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  turn.release()
  expect(await screen.findByText(/conversation you left.*cora is away\./)).toBeTruthy()

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: 'First question' }))

  await screen.findByText(/Sleep, not volume/)
  expect(screen.queryByText(/conversation you left/)).toBeNull()
})

test('a turn that fails in the conversation on screen says so there, whatever else is loading', async () => {
  /* A load on the wire is not a load that will replace this conversation: one that has
     already lost its race replaces nothing. Reading "a load exists" as "what I append is
     about to be overwritten" sent the failure to a sentence that is not drawn while the
     reader is in the conversation it names — so it was said nowhere at all. */
  const slow = held()
  let asks = 0
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return asks++ === 0 ? answering() : failing()
      if (path === '/api/sessions/old') {
        await slow.until
        return body([OLDER])
      }
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  const ask = (question: string) => {
    turn = held()
    fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
      target: { value: question },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  }

  ask('Why am I stalling?')
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  // A reopen that can never land: the new session below is a later claim on the page.
  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  ask('And now?')
  await screen.findByText(/Working/)
  turn.release()

  // Where the answer would have been, in the conversation that asked it.
  expect(await screen.findByText('cora is away.')).toBeTruthy()
  expect(screen.getByText('And now?')).toBeTruthy()
  slow.release()
})

test('the page says both of its sentences at once, in one order', async () => {
  /* Two facts with two lifetimes: a load that failed, cleared by the next one that goes
     through, and a question left running that will not be answered, which stands until the
     reader asks the next one. They are drawn from one place so that order is a decision
     rather than whatever the two `&&`s happened to be. */
  const unreachable = 'The conversation store is temporarily unavailable.'
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return failing()
      if (path === '/api/sessions/old')
        return {
          ok: false,
          status: 503,
          json: async () => ({ error: unreachable }),
        } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  turn.release()
  await screen.findByText(/conversation you left/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(unreachable)

  /* Resolved through the role, and named: the documents rail carries a live region of its
     own for what an upload did, so a bare role would find two. The name is what tells the
     two apart — and what a screen reader says before the sentence, rather than announcing
     it bare. */
  const banners = screen.getByRole('status', { name: 'Notices' })
  expect([...banners.children].map((each) => each.textContent)).toEqual([
    unreachable,
    'In the conversation you left: cora is away.',
  ])
})

/** A 200 whose body is not a list of turns: the read went through, what came back cannot
 *  be drawn. A proxy or a version skew is enough. */
const NONSENSE = 'not a list of turns at all'

test('a conversation that cannot be drawn says so, and does not read as a failed turn', async () => {
  /* Reading and drawing fail differently. The read is what the store answered for; what
     the page does with it is the page's own fault, and reported as neither the store being
     unreachable nor — inside a turn — as that turn having failed. */
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions/old') return body(NONSENSE)
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))

  // Said on the page, rather than thrown where nobody sees it.
  expect(await screen.findByText(/could not be read/)).toBeTruthy()
  expect(screen.queryByText(/is not a function/)).toBeNull()
})

test('a turn that succeeded is not drawn as failed by the re-read that follows it', async () => {
  /* When the store's own list of turns lands while a turn is running, the answer is taken
     from a re-read rather than appended. A re-read that cannot be drawn was reaching the
     reader as that turn having failed, with an internal message where the answer belongs. */
  let minted = 0
  vi.stubGlobal('crypto', { randomUUID: () => `t${++minted}` })
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  let reads = 0
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return answering()
      if (path === '/api/sessions')
        return body([
          { thread_id: 'old', opened_with: OLDER.question },
          { thread_id: 't1', opened_with: 'Why am I stalling?' },
        ])
      // Readable on the way back into the conversation, nonsense on the re-read after.
      if (path === '/api/sessions/t1') return body(reads++ === 0 ? [] : NONSENSE)
      if (path === '/api/sessions/old') return body([OLDER])
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(LIVE[0].summary)

  // Away and back, so the answer arrives to a conversation the store has re-read.
  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)
  fireEvent.click(await screen.findByRole('button', { name: 'Why am I stalling?' }))
  await screen.findByText(/Working/)

  turn.release()

  // The answer is on the page, from the turn in hand rather than from the re-read.
  expect(await screen.findByText(/Sleep, not volume/)).toBeTruthy()
  expect(screen.queryByText(/is not a function/)).toBeNull()
  expect(screen.queryByText(/conversation you left/)).toBeNull()
  // Once in the conversation — the other one on the page is the session it names.
  expect([...document.querySelectorAll('.said')].map((each) => each.textContent)).toEqual(
    ['Why am I stalling?'],
  )
})

test('a conversation that cannot be drawn does not half-move the page into it', async () => {
  /* Reopening changes three things at once: which thread the page is in, which turns it
     shows, and which document it reads. Where the turns are what cannot be drawn, the
     other two had already moved — so the reader sat in one conversation looking at
     another's, and their next question was asked on the thread they could not see. */
  const asked: string[] = []
  let minted = 0
  vi.stubGlobal('crypto', { randomUUID: () => `t${++minted}` })
  const body = (data: unknown) =>
    ({ ok: true, json: async () => data }) as unknown as Response
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/ask') {
        asked.push(JSON.parse(String(init?.body)).thread_id)
        return answering()
      }
      if (path === '/api/sessions/old') return body(NONSENSE)
      if (path.startsWith('/api/uploads/')) return body({ text: KEPT })
      return body(served[path] ?? [])
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  const ask = (question: string) => {
    turn = held()
    fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
      target: { value: question },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
    turn.release()
  }

  ask('Why am I stalling?')
  await screen.findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  expect(await screen.findByText(/could not be read/)).toBeTruthy()

  // Still in the conversation on screen, and still asking in it.
  expect(screen.getByText(/Sleep, not volume/)).toBeTruthy()
  ask('And now?')
  await screen.findByText('And now?')
  expect(asked).toEqual(['t1', 't1'])
})

/**
 * A stream of the given frames. Everything from `held` on waits until the test releases
 * it — including the end of the stream, so a turn can be left in flight — which is what
 * makes "this was on the page before the turn was" assertable.
 */
function streaming(parts: string[], held = parts.length - 1): Response {
  const encoder = new TextEncoder()
  let next = 0
  const reader = {
    cancel: async () => {},
    read: async () => {
      if (next === held) await turn.until
      if (next === parts.length) return { done: true, value: undefined }
      return { done: false, value: encoder.encode(parts[next++]) }
    },
  }
  return { ok: true, body: { getReader: () => reader } } as unknown as Response
}

/** A turn that writes its answer in pieces, its final step and its `turn` withheld. */
function writing(pieces: string[]): Response {
  const parts = [
    frame('step', LIVE[0]),
    ...pieces.map((piece) => frame('text', { text: piece })),
    frame('step', TURN.trace[0]),
    frame('turn', TURN),
  ]
  return streaming(parts, parts.length - 2)
}

/** The page over a stream of the given frames, asked one question. */
async function asked(parts: string[], held?: number): Promise<void> {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return streaming(parts, held)
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
}

/* The outer test of story 19. Held under `test.fails` — vitest's strict xfail — while
   the list was worked through, so leaving the marker behind was not possible. */
test(
  'the answer arrives as it is written, and its citation is clickable once it lands',
  async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (path: string) => {
        if (path === '/api/ask') return writing(['Sleep, ', 'not volume [1].'])
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

    // Written, before the turn that carries it exists — so `[1]` is still literal text.
    expect(await screen.findByText(/Sleep, not volume \[1\]\./)).toBeTruthy()
    expect(screen.queryByText(/Working/)).toBeNull()
    expect(screen.queryByRole('button', { name: 'Open cited source 1' })).toBeNull()

    turn.release()

    const cite = await screen.findByRole('button', { name: 'Open cited source 1' })
    fireEvent.click(cite)
    expect(await screen.findByRole('dialog')).toBeTruthy()
  },
)


test('a turn still being written shows what has been written, not Working', async () => {
  await asked([
    frame('step', LIVE[0]),
    frame('text', { text: 'Sleep, ' }),
    frame('text', { text: 'not volume.' }),
    frame('turn', TURN),
  ])

  expect(await screen.findByText('Sleep, not volume.')).toBeTruthy()
  expect(screen.queryByText(/Working/)).toBeNull()
})

test('a turn with nothing written yet still says Working', async () => {
  await asked([frame('step', LIVE[0]), frame('turn', TURN)])

  expect(await screen.findByText(LIVE[0].summary)).toBeTruthy()
  expect(screen.getByText(/Working/)).toBeTruthy()
})

test('the answer after an aside starts clean', async () => {
  /* A model may write before it calls a tool. That text is the trace's — it is already
     kept as the step's detail — and letting the next round append to it would leave the
     reader an answer with the model's aside glued to the front of it. The stream says
     which is which, so the page no longer infers it from the shape of the steps. */
  await asked([
    frame('text', { text: 'Let me check the log. ' }),
    frame('aside', {}),
    frame('step', LIVE[0]),
    frame('step', LIVE[1]),
    frame('text', { text: 'Sleep, ' }),
    frame('text', { text: 'not volume.' }),
    frame('turn', TURN),
  ])

  expect(await screen.findByText('Sleep, not volume.')).toBeTruthy()
  expect(screen.queryByText(/Let me check the log/)).toBeNull()
})

test('an aside puts the turn back to Working, rather than reading as the answer', async () => {
  /* Between the aside and the round that answers, the page has nothing to show but that
     it is still working. Leaving the superseded sentence there presents the model's note
     to itself as cora's answer for the whole of a tool round — and if the turn then
     fails, that is the last thing the reader was told. */
  const parts = [
    frame('text', { text: 'Let me check your notes. ' }),
    frame('aside', {}),
    frame('step', LIVE[0]),
    frame('text', { text: 'Sleep, not volume [1].' }),
    frame('turn', TURN),
  ]
  await asked(parts, 3)

  expect(await screen.findByText(LIVE[0].summary)).toBeTruthy()
  expect(screen.queryByText(/Let me check your notes/)).toBeNull()
  expect(screen.getByText(/Working/)).toBeTruthy()

  turn.release()

  expect(
    await screen.findByRole('button', { name: 'Open cited source 1' }),
  ).toBeTruthy()
  expect(screen.getByText(/Sleep, not volume/)).toBeTruthy()
  expect(screen.queryByText(/Working/)).toBeNull()
})

test('a step arriving does not on its own clear what has been written', async () => {
  /* The step that ends a round arrives after the text written in it and before the turn
     that carries it, so a page that cleared on the step would blank the finished answer
     for the frame between the two. The aside is what clears, and a final round sends
     none. */
  const parts = [frame('text', { text: 'Sleep, not volume.' }), frame('step', LIVE[0])]
  await asked(parts, parts.length)

  expect(await screen.findByText(LIVE[0].summary)).toBeTruthy()
  expect(screen.getByText('Sleep, not volume.')).toBeTruthy()
})

test('a turn that fails after writing shows the error in place of what was written', async () => {
  const parts = [
    frame('text', { text: 'Sleep, ' }),
    frame('error', { error: 'The model is busy. Please try again.' }),
  ]
  await asked(parts, parts.length - 1)

  expect(await screen.findByText('Sleep,')).toBeTruthy()

  turn.release()

  expect(await screen.findByText(/The model is busy/)).toBeTruthy()
  expect(screen.queryByText('Sleep,')).toBeNull()
})

test('an answer written into a conversation the reader left does not land on the page', async () => {
  const parts = [
    frame('text', { text: 'Sleep, ' }),
    frame('text', { text: 'not volume.' }),
    frame('turn', TURN),
  ]
  await asked(parts, 1)

  expect(await screen.findByText('Sleep,')).toBeTruthy()

  fireEvent.click(screen.getByRole('button', { name: /New session/i }))
  turn.release()
  await flushed()

  expect(screen.queryByText(/Sleep/)).toBeNull()
})

test('the conversation follows the answer down as it is written', async () => {
  const parts = [
    frame('text', { text: 'Sleep, ' }),
    frame('text', { text: 'not volume.' }),
    frame('turn', TURN),
  ]
  await asked(parts, parts.length - 1)
  const scroller = document.querySelector('.scroller') as HTMLElement
  await screen.findByText('Sleep, not volume.')

  atTheBottom(scroller)
  turn.release()

  await screen.findByRole('button', { name: 'Open cited source 1' })
  await waitFor(() => expect(scroller.scrollTop).toBe(5000))
})

test('a reader who has scrolled up is left there as the answer grows', async () => {
  /* The scroll effect runs once per piece now, so a reader who goes back to re-read an
     earlier turn during a thirty-second answer was yanked to the bottom on the next
     one — the conversation could not be read while it was being written. */
  const parts = [
    frame('text', { text: 'Sleep, ' }),
    frame('text', { text: 'not volume.' }),
    frame('turn', TURN),
  ]
  await asked(parts, 1)
  const scroller = document.querySelector('.scroller') as HTMLElement
  await screen.findByText('Sleep,')
  scrolledUp(scroller)

  turn.release()
  await screen.findByRole('button', { name: 'Open cited source 1' })
  await flushed()

  expect(scroller.scrollTop).toBe(0)
})

test('a conversation reopened shows its newest turn, however the reader had scrolled', async () => {
  /* Following is this conversation's, not the page's: leaving one halfway up it is no
     statement about the next, which opens on the turn it left off at like any other. */
  render(<App />)
  await screen.findByText('notes.md')
  const scroller = document.querySelector('.scroller') as HTMLElement
  scrolledUp(scroller)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)

  await waitFor(() => expect(scroller.scrollTop).toBe(5000))
})

test('a reader who scrolls back to the bottom is followed again', async () => {
  const parts = [
    frame('text', { text: 'Sleep, ' }),
    frame('text', { text: 'not volume.' }),
    frame('turn', TURN),
  ]
  await asked(parts, 1)
  const scroller = document.querySelector('.scroller') as HTMLElement
  await screen.findByText('Sleep,')
  scrolledUp(scroller)
  scroller.scrollTop = 4200
  fireEvent.scroll(scroller)

  turn.release()
  await screen.findByRole('button', { name: 'Open cited source 1' })

  await waitFor(() => expect(scroller.scrollTop).toBe(5000))
})

test('asking a question scrolls to it from wherever the reader had scrolled to', async () => {
  /* Following is the reader's to give up, and asking is them giving it back: the question
     they just typed is the one thing that belongs on screen. */
  await asked([frame('turn', TURN)], 1)
  const scroller = document.querySelector('.scroller') as HTMLElement
  await screen.findByText(/Working/)
  scrolledUp(scroller)

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'And now?' },
  })
  turn.release()
  await screen.findByRole('button', { name: 'Open cited source 1' })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

  await waitFor(() => expect(scroller.scrollTop).toBe(5000))
})

/* The outer tests of story 21. Held under `test.fails` — vitest's strict xfail — while
   the list was worked through, so leaving the marker behind was not possible. */

const GROWN = {
  answer: 'Sleep is the lever.\n\nNot volume and not intensity [1].',
  citations: TURN.citations,
  trace: TURN.trace,
}

test(
  'a paragraph the reader is reading is the same node when the answer finishes',
  async () => {
    /* A selection lives on the nodes it was made in, and it is those nodes the fix keeps:
       happy-dom's Selection outlives their removal where a browser's collapses, so the
       node is what can be asserted here — the reader's copy is what it buys. */
    await asked(
      [
        frame('text', { text: 'Sleep is the lever.\n\n' }),
        frame('text', { text: 'Not volume ' }),
        frame('text', { text: 'and not intensity [1].' }),
        frame('turn', GROWN),
      ],
      2,
    )
    const read = await screen.findByText('Sleep is the lever.')
    const words = read.firstChild

    turn.release()
    await screen.findByRole('button', { name: 'Open cited source 1' })

    expect(screen.getByText('Sleep is the lever.')).toBe(read)
    expect(read.firstChild).toBe(words)
  },
)

/** The rail's file input, which has no label of its own — the label is the button. */
const upload = (name: string) => {
  const picker = document.querySelector('input[type="file"]') as HTMLInputElement
  fireEvent.change(picker, { target: { files: [new File(['notes'], name)] } })
}

test('a file uploaded twice is added, and then said to be there already', async () => {
  const counts = [12, 0]
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/documents' && init?.method === 'POST')
        return {
          ok: true,
          json: async () => ({ document: 'notes.md', chunks: counts.shift() }),
        } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  upload('notes.md')
  expect(await screen.findByText('Added “notes.md” — 12 passages.')).toBeTruthy()

  upload('notes.md')
  expect(
    await screen.findByText('“notes.md” is already in your documents.'),
  ).toBeTruthy()
})

/** The page with a rail whose uploads are answered in turn: a chunk count, or a refusal. */
async function ready(outcomes: (number | { error: string })[]): Promise<void> {
  const answers = [...outcomes]
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/documents' && init?.method === 'POST') {
        const outcome = answers.shift()
        if (typeof outcome === 'number')
          return {
            ok: true,
            json: async () => ({ document: 'notes.md', chunks: outcome }),
          } as unknown as Response
        return { ok: false, json: async () => outcome } as unknown as Response
      }
      if (path === '/api/ask') return answering()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')
}

test('one passage indexed is one passage', async () => {
  await ready([1])

  upload('notes.md')

  expect(await screen.findByText('Added “notes.md” — 1 passage.')).toBeTruthy()
})

test('an upload that indexed nothing is drawn as the outcome it is', async () => {
  /* A duplicate is not the outcome the reader asked for, and not the one a document added
     gets: the reader tells the two apart by looking at them. The store answering "already
     there" before "added" cannot happen — the order is arbitrary because only the drawing
     is under test. */
  await ready([0, 12])

  upload('notes.md')
  const duplicate = await screen.findByText('“notes.md” is already in your documents.')
  expect(duplicate.closest('.upload-notice')?.className).toContain('wrong')

  upload('notes.md')
  const added = await screen.findByText('Added “notes.md” — 12 passages.')
  expect(added.closest('.upload-notice')?.className).not.toContain('wrong')
})

test('the reader can shut what an upload said', async () => {
  await ready([12])

  upload('notes.md')
  await screen.findByText('Added “notes.md” — 12 passages.')
  fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }))

  expect(screen.queryByText('Added “notes.md” — 12 passages.')).toBeNull()
})

test('what an upload did is drawn beside the list it changed', async () => {
  /* Not over the conversation: the sentence is about this rail, and the control that
     raised it is directly above. */
  await ready([12])

  upload('notes.md')

  const said = await screen.findByText('Added “notes.md” — 12 passages.')
  expect(said.closest('.rail-docs')).toBeTruthy()
  expect(document.querySelector('.banners')?.textContent).toBe('')
})

test('an upload that fails says so, and takes the last one’s notice away', async () => {
  await ready([12, { error: 'That upload is larger than the 5 MB cora reads.' }])

  upload('notes.md')
  await screen.findByText('Added “notes.md” — 12 passages.')
  upload('huge.pdf')

  expect(
    await screen.findByText('That upload is larger than the 5 MB cora reads.'),
  ).toBeTruthy()
  expect(screen.queryByText('Added “notes.md” — 12 passages.')).toBeNull()
})

test('a notice for an upload the reader walked away from is not drawn', async () => {
  /* Ingestion takes seconds and nothing stops the reader leaving while it runs, so the
     notice would land on a conversation the upload never happened in — where nothing can
     take it away again, `New session` having nothing left to leave. */
  const ingesting = held()
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/documents' && init?.method === 'POST') {
        await ingesting.until
        return {
          ok: true,
          json: async () => ({ document: 'notes.md', chunks: 12 }),
        } as unknown as Response
      }
      if (path === '/api/ask') return answering()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')
  /* A conversation to leave, so `New session` is live. */
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByRole('button', { name: 'Open cited source 1' })

  upload('notes.md')
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  ingesting.release()
  await flushed()

  expect(screen.queryByText('Added “notes.md” — 12 passages.')).toBeNull()
})

test('starting a new session takes the last upload’s notice away', async () => {
  /* The notice is news about what the reader just handed the page. Left standing over a
     conversation opened after it, it is a banner with nothing behind it — and nothing
     else ever takes it away. */
  await ready([12])

  upload('notes.md')
  await screen.findByText('Added “notes.md” — 12 passages.')
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByRole('button', { name: 'Open cited source 1' })
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))

  await waitFor(() =>
    expect(screen.queryByText('Added “notes.md” — 12 passages.')).toBeNull(),
  )
})

test('reopening an earlier conversation takes the notice away too', async () => {
  /* The same boundary as a new session: the reader has moved to a conversation the upload
     had not happened in yet. */
  await ready([12])

  upload('notes.md')
  await screen.findByText('Added “notes.md” — 12 passages.')
  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)

  await waitFor(() =>
    expect(screen.queryByText('Added “notes.md” — 12 passages.')).toBeNull(),
  )
})

test('a notice stands while the reader asks their next question', async () => {
  /* Every load that goes through clears the banner about a load — an upload's outcome is
     not one, and a question in between is not the reader being told twice. */
  await ready([12])

  upload('notes.md')
  await screen.findByText('Added “notes.md” — 12 passages.')
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByRole('button', { name: 'Open cited source 1' })

  expect(screen.getByText('Added “notes.md” — 12 passages.')).toBeTruthy()
})

/** Every sentence story 22 deleted. Kept as one list so a paragraph reintroduced anywhere
 *  in the rail fails here, whichever panel it lands in. */
const EXPLANATIONS = [
  /fixed pipeline/,
  /steps cora takes will appear/,
  /Greyed documents are indexed/,
  /Nothing indexed yet/,
  /passage an answer cites/,
  /will be listed here/,
  /carries between sessions/,
  /tell cora something about yourself/,
  /the agent stays the same/,
  /CORA_PLUGINS/,
]

const nothingExplains = () =>
  EXPLANATIONS.forEach((said) => expect(screen.queryByText(said)).toBeNull())

test('a full page explains none of its own panels', async () => {
  /* Documents, steps, facts, a plugin and a past conversation — every panel with something
     in it, and the reader is told about none of them. */
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)
  expect(screen.getByText(TURN.trace[0].summary)).toBeTruthy()

  fireEvent.click(screen.getByRole('button', { name: 'notes.md' }))
  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(screen.getByRole('heading', { name: 'notes.md' })).toBeTruthy()
  expect(screen.queryByText(/cited passage/)).toBeNull()

  for (const panel of ['STEPS', 'SESSIONS', 'MEMORY']) {
    fireEvent.click(screen.getByRole('tab', { name: panel }))
    nothingExplains()
  }
  fireEvent.click(screen.getByRole('button', { name: /fitness/ }))
  nothingExplains()
})

test('a page with nothing in it yet draws the controls and no prose', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => [] }) as unknown as Response),
  )
  render(<App />)
  await screen.findByText('Add a document')

  for (const panel of ['STEPS', 'SOURCE', 'SESSIONS', 'MEMORY']) {
    fireEvent.click(screen.getByRole('tab', { name: panel }))
    nothingExplains()
  }
  expect(screen.getByPlaceholderText(/Ask a question/)).toBeTruthy()
})

test('an upload that failed in a conversation left behind keeps this one’s notice', async () => {
  /* The success path is stamped with the conversation the upload was started in; the
     failure path was not, and `setNotice(null)` reaches into state the reader's *current*
     conversation owns. The rejection is still drawn — a document is refused wherever the
     reader is — but it may not take away news about an upload that worked here. */
  const refusing = held()
  let first = true
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/documents' && init?.method === 'POST') {
        if (first) {
          first = false
          await refusing.until
          return {
            ok: false,
            json: async () => ({ error: 'That upload is larger than the 5 MB cora reads.' }),
          } as unknown as Response
        }
        return {
          ok: true,
          json: async () => ({ document: 'notes.md', chunks: 12 }),
        } as unknown as Response
      }
      if (path === '/api/ask') return answering()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  /* A conversation to leave, so `New session` is live. */
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByRole('button', { name: 'Open cited source 1' })

  upload('huge.pdf')
  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  upload('notes.md')
  await screen.findByText('Added “notes.md” — 12 passages.')

  refusing.release()
  expect(
    await screen.findByText('That upload is larger than the 5 MB cora reads.'),
  ).toBeTruthy()
  expect(screen.getByText('Added “notes.md” — 12 passages.')).toBeTruthy()
})


// ── a question waiting on the reader ──

const DECISION = {
  question: 'Which bodyweight should I treat as current?',
  options: [
    { label: '77 kg', note: 'intake form, 17 Aug' },
    { label: '75 kg', note: 'coach notes, February' },
  ],
  decline: 'Do not use any of them',
}
const PAUSED = { asked: 'What is my BMR?', decision: DECISION }
const WEIGHED = {
  answer: 'At 75 kg your BMR is about 1,730 kcal.',
  citations: [],
  trace: [],
}

const stream = (...parts: string[]): Response => {
  const encoder = new TextEncoder()
  let next = 0
  return {
    ok: true,
    body: {
      getReader: () => ({
        cancel: async () => {},
        read: async () =>
          next === parts.length
            ? { done: true, value: undefined }
            : { done: false, value: encoder.encode(parts[next++]) },
      }),
    },
  } as unknown as Response
}

type Sent = { path: string; body: Record<string, unknown> }

/** A stream whose last frame is withheld until the test lets it go, so what is asserted
 *  before that can only be what the page does while a turn is still running. */
const holding = (gate: { until: Promise<void> }, ...parts: string[]): Response => {
  const encoder = new TextEncoder()
  let next = 0
  return {
    ok: true,
    body: {
      getReader: () => ({
        cancel: async () => {},
        read: async () => {
          if (next === parts.length) return { done: true, value: undefined }
          if (next === parts.length - 1) await gate.until
          return { done: false, value: encoder.encode(parts[next++]) }
        },
      }),
    },
  } as unknown as Response
}

/** A page whose every turn stops to ask, and whose resume answers. What comes back is
 *  what the page sent, so a test can say which of the two requests it made. */
const stopping = (
  pending: unknown = null,
  gate?: { until: Promise<void> },
): Sent[] => {
  const sent: Sent[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (init?.body && typeof init.body === 'string')
        sent.push({ path, body: JSON.parse(init.body) })
      if (path === '/api/ask') return stream(frame('paused', PAUSED))
      if (path === '/api/resume')
        return gate
          ? holding(gate, frame('turn', WEIGHED))
          : stream(frame('turn', WEIGHED))
      if (path.endsWith('/pending'))
        return { ok: true, json: async () => pending } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  return sent
}

const askAbout = (question = 'What is my BMR?') => {
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: question },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
}

const card = () => screen.findByRole('group', { name: /Paused/ })

const stopped = async () => {
  render(<App />)
  await screen.findByText('notes.md')
  askAbout()
  return card()
}

const of = (sent: Sent[], path: string) => sent.filter((each) => each.path === path)

test('a turn that stops to ask draws the question and every way out of it', async () => {
  stopping()

  const asked = await stopped()

  expect(within(asked).getByText(DECISION.question)).toBeTruthy()
  expect(within(asked).getByRole('button', { name: /77 kg/ })).toBeTruthy()
  expect(within(asked).getByRole('button', { name: /75 kg/ })).toBeTruthy()
  expect(within(asked).getByRole('button', { name: DECISION.decline })).toBeTruthy()
})

test('an option says where it came from, beside the value itself', async () => {
  stopping()

  const asked = await stopped()

  expect(within(asked).getByText('coach notes, February')).toBeTruthy()
})

test('picking an option finishes the turn, and the answer takes the card away', async () => {
  const sent = stopping()
  const asked = await stopped()

  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))

  expect(await screen.findByText(/1,730 kcal/)).toBeTruthy()
  expect(of(sent, '/api/resume')[0].body.answer).toBe('75 kg')
  expect(screen.queryByText(DECISION.question)).toBeNull()
})

test('the line left behind names what was chosen', async () => {
  stopping()
  const asked = await stopped()

  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))

  expect(await screen.findByText(/You chose 75 kg/)).toBeTruthy()
})

test('a card that has been answered is not still called paused', async () => {
  stopping()
  const asked = await stopped()

  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))
  await screen.findByText(/You chose 75 kg/)

  expect(screen.getByRole('group', { name: /Settled/ })).toBeTruthy()
  expect(screen.queryByRole('group', { name: /Paused/ })).toBeNull()
  expect(screen.queryByText(/needs your decision/)).toBeNull()
})

test('a card put back up is waiting again, and says so', async () => {
  stopping()
  const asked = await stopped()
  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))
  await screen.findByText(/You chose 75 kg/)

  fireEvent.click(screen.getByRole('button', { name: 'Change' }))

  expect(await screen.findByRole('group', { name: /Paused/ })).toBeTruthy()
})

test('choosing none of them is sent as choosing nothing, and still answers', async () => {
  const sent = stopping()
  const asked = await stopped()

  fireEvent.click(within(asked).getByRole('button', { name: DECISION.decline }))

  expect(await screen.findByText(/1,730 kcal/)).toBeTruthy()
  expect(of(sent, '/api/resume')[0].body.answer).toBeNull()
  expect(screen.getByText(/You chose none of them/)).toBeTruthy()
})

test('changing a decision puts the options back', async () => {
  stopping()
  const asked = await stopped()
  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))
  await screen.findByText(/You chose 75 kg/)

  fireEvent.click(screen.getByRole('button', { name: 'Change' }))

  expect(await screen.findByRole('button', { name: /77 kg/ })).toBeTruthy()
})

test('picking again after a change asks, rather than answering a turn that has gone on', async () => {
  const sent = stopping()
  const asked = await stopped()
  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))
  await screen.findByText(/You chose 75 kg/)
  fireEvent.click(screen.getByRole('button', { name: 'Change' }))

  fireEvent.click(await screen.findByRole('button', { name: /77 kg/ }))

  await waitFor(() => expect(of(sent, '/api/ask')).toHaveLength(2))
  expect(of(sent, '/api/resume')).toHaveLength(1)
  expect(of(sent, '/api/ask')[1].body.question).toBe('Use 77 kg instead.')
})

test('a card left open comes back when the page does', async () => {
  stopping(PAUSED)
  await stopped()

  cleanup()
  render(<App />)

  expect(await screen.findByText(DECISION.question)).toBeTruthy()
})

test('a card the conversation moved past does not come back', async () => {
  stopping(null)
  const asked = await stopped()
  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))
  await screen.findByText(/1,730 kcal/)

  cleanup()
  render(<App />)
  await screen.findByText('notes.md')

  expect(screen.queryByText(DECISION.question)).toBeNull()
})

test('the composer says why it is unavailable while a card waits', async () => {
  stopping()
  const asked = await stopped()

  expect(screen.getByText(/waiting on the decision/)).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Ask' })).toHaveProperty('disabled', true)

  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))
  await screen.findByText(/1,730 kcal/)

  expect(screen.queryByText(/waiting on the decision/)).toBeNull()
})

test('a card arriving brings the conversation down to it', async () => {
  stopping()
  render(<App />)
  await screen.findByText('notes.md')
  const scroller = document.querySelector('.scroller') as HTMLElement
  atTheBottom(scroller)

  askAbout()
  await card()

  await waitFor(() => expect(scroller.scrollTop).toBe(5000))
})


test('a resume in the conversation on screen is not called work you left behind', async () => {
  /* The note is about a question running in a conversation the reader is no longer in.
     A resume has no entry in flight to name its thread, and saying it of the turn on
     screen tells them to wait for it under SESSIONS, where it will never appear. */
  const gate = held()
  stopping(null, gate)
  const asked = await stopped()

  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))
  await flushed()

  expect(screen.queryByText(/conversation you left/)).toBeNull()

  gate.release()
  expect(await screen.findByText(/1,730 kcal/)).toBeTruthy()
})

test('an answer to a decision does not land on the conversation the reader moved to', async () => {
  /* Ids repeat across conversations — every reopened thread numbers its turns from -1 —
     so a restored card and another conversation's first turn can carry the same one. */
  const gate = held()
  stopping(PAUSED, gate)
  await stopped()

  cleanup()
  render(<App />)
  const restored = await screen.findByRole('group', { name: /Paused/ })
  fireEvent.click(within(restored).getByRole('button', { name: /75 kg/ }))

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)
  gate.release()
  await flushed()

  expect(screen.getByText(OLDER.result.answer)).toBeTruthy()
  expect(screen.queryByText(/1,730 kcal/)).toBeNull()
})

test('starting over leaves the parked card behind', async () => {
  stopping(PAUSED)
  await stopped()

  fireEvent.click(screen.getByRole('button', { name: 'New session' }))
  await flushed()
  cleanup()
  render(<App />)
  await screen.findByText('notes.md')

  expect(screen.queryByText(DECISION.question)).toBeNull()
})


test('a card parked in an unrecorded conversation is not lost by reading another', async () => {
  /* A thread parked on its *first* question has answered nothing, so it is listed under
     no session: forgetting it while reading a different conversation would leave the
     card reachable by no route at all. */
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return stream(frame('paused', PAUSED))
      // Only the parked conversation is waiting on anything; the older one is not.
      if (path === '/api/sessions/old/pending')
        return { ok: true, json: async () => null } as unknown as Response
      if (path.endsWith('/pending'))
        return { ok: true, json: async () => PAUSED } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  await stopped()

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)

  cleanup()
  render(<App />)

  expect(await screen.findByText(DECISION.question)).toBeTruthy()
})

test('a decision that could not be sent is still answerable, and says what went wrong', async () => {
  const sent: Sent[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (init?.body && typeof init.body === 'string')
        sent.push({ path, body: JSON.parse(init.body) })
      if (path === '/api/ask') return stream(frame('paused', PAUSED))
      if (path === '/api/resume')
        return {
          ok: false,
          status: 503,
          json: async () => ({ error: 'cora is having a moment.' }),
        } as unknown as Response
      if (path.endsWith('/pending'))
        return { ok: true, json: async () => PAUSED } as unknown as Response
      return { ok: true, json: async () => served[path] ?? [] } as unknown as Response
    }),
  )
  const asked = await stopped()

  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))

  expect(await screen.findByText('cora is having a moment.')).toBeTruthy()
  expect(screen.queryByText(/You chose 75 kg/)).toBeNull()
  expect(screen.getByRole('button', { name: /75 kg/ })).toBeTruthy()

  fireEvent.click(screen.getByRole('button', { name: /75 kg/ }))

  await waitFor(() => expect(of(sent, '/api/resume')).toHaveLength(2))
})
