import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import answerCss from './components/Answer.module.css'
import appCss from './App.module.css'
import bodyCss from './components/DocumentBody.module.css'

/**
 * The steps that arrive *while* the turn runs say something the finished turn does not.
 * Sharing one summary between them would let the assertion pass off the turn's own
 * trace, with nothing streamed and nothing observed.
 */
const LIVE = [
  { summary: 'Reading your documents', detail: '', failed: false, origin: '', steps: [] },
  {
    summary: 'Weighing the last 21 days',
    detail: 'training_log',
    failed: false,
    origin: 'plugin tool',
    steps: [],
  },
]
const TURN = {
  answer: 'Sleep, not volume [1].',
  citations: [
    { number: 1, document: 'notes.md', start: 0, end: 6, upload: 'u1', scope: 'cora' },
  ],
  trace: [
    { summary: 'Wrote the answer', detail: '', failed: false, origin: '', steps: [] },
  ],
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
  '/api/scopes': { available: ['fitness', 'travel'], default: 'cora', pages: {} },
  '/api/memory': [{ key: 'f1', text: 'No burpees.' }],
  '/api/conversations': [{ thread_id: 'old', opened_with: OLDER.question, pin: null }],
  '/api/conversations/old': [OLDER],
}

const BARE = { available: ['fitness', 'travel'], default: 'cora', pages: {} }

/** The fields listing with a page for fitness, as a deployment carrying one answers. */
const bringsAPage = () => {
  served['/api/scopes'] = { ...BARE, pages: { fitness: '/pages/fitness/' } }
}

afterEach(() => {
  /* A fixture one spec rewrote is a fixture every later one inherits. */
  served['/api/scopes'] = BARE
  served['/api/conversations'] = [{ thread_id: 'old', opened_with: OLDER.question, pin: null }]
  turn.release()
  step.release()
  cleanup()
  globalThis.sessionStorage?.clear()
  /* The address outlives a render, so a conversation one test opened would be the one
     the next test's page opens in — every spec here starts nowhere in particular. */
  globalThis.history.replaceState(null, '', globalThis.location.pathname)
})

beforeEach(() => {
  turn = held()
  step = held()
  /* A pin sent with a question is read back off the thread afterwards, as the real API
     does: the page draws the control from what the thread holds, so a fake that forgot
     the pin would show every conversation as unpinned however it was asked. */
  let taken: string | null = null
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path === '/api/ask') {
        taken = JSON.parse((init?.body as string) ?? '{}').pin ?? taken
        return answering()
      }
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      if (path.endsWith('/scope') && !(path in served)) {
        /* A thread the listing knows carries its own pin; one it does not is the
           conversation on the page, whose pin is whatever was last asked with. */
        const thread = path.split('/')[3]
        /* One spec serves a listing the panel cannot read, so this cannot assume one. */
        const listed = served['/api/conversations']
        const known = Array.isArray(listed)
          ? listed.find((each) => each.thread_id === thread)
          : undefined
        return {
          ok: true,
          json: async () => ({ pin: known ? known.pin : taken }),
        } as unknown as Response
      }
      return { ok: true, json: async () => served[route(path)] ?? [] } as unknown as Response
    }),
  )
})

const KEPT = 'Sleep, not volume. The rest of the document follows.'

/** The route a request names, without the field it asked the route for. The listing is
 *  per field now, and the fixture serves one set of documents whichever is asked for. */
const route = (path: string) => path.split('?')[0]

/** Naming a field is two clicks: the segment that asks which, then the plugin. */
const pickPlugin = (name: string) => {
  fireEvent.click(screen.getByRole('button', { name: 'Plugin' }))
  fireEvent.click(within(screen.getByRole('list')).getByRole('button', { name }))
}

/** The field the rail says it lists and uploads into, or `null` where it names none.
 *  Read off the heading row, because that is where a reader reads it: the heading names
 *  the list and the field follows it, with no ARIA in between. `null` rather than an
 *  empty string, so a field drawn with nothing in it is not read as no field drawn. */
test('the plan fills while the turn runs, then the answer lands with its citation', async () => {
  render(<App />)

  expect(await screen.findByText('notes.md')).toBeTruthy()

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
  expect(container.querySelector(`.${bodyCss.docPassage}`)?.textContent).toBe(
    KEPT.slice(0, 6),
  )
})

/** A turn that cites nothing. */
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

  fireEvent.click(screen.getByRole('tab', { name: 'CONVERSATIONS' }))
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
     something false about it — that cora cannot open it, when the truth is that
     nothing here cites it. */
  fireEvent.click(screen.getByRole('tab', { name: 'SOURCE' }))
  const panels = document.querySelector(`.${appCss.railPanels}`) as HTMLElement
  expect(within(panels).queryByText('notes.md')).toBeNull()
  expect(within(panels).queryByRole('heading', { name: 'notes.md' })).toBeNull()
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
      return { ok: true, json: async () => served[route(path)] ?? [] } as unknown as Response
    }),
  )
  const { container } = render(<App />)
  await screen.findByText('notes.md')
  const scroller = container.querySelector(`.${answerCss.scroller}`) as HTMLElement
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

/** A stream carrying one finished turn and nothing held back. */
/** A turn whose second step is held back, so a reopen can happen between the two. */
test('the conversation left behind is listed under CONVERSATIONS', async () => {
  /* Starting over is not throwing away: what was asked is checkpointed under its own
     thread, and the only way back to it is the conversations list. */
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
      if (path === '/api/conversations')
        return body(recorded ? [{ thread_id: 't1', opened_with: 'Why am I stalling?' }] : [])
      if (path.startsWith('/api/uploads/'))
        return body({ text: KEPT })
      return body(served[route(path)] ?? [])
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

  fireEvent.click(screen.getByRole('button', { name: 'New conversation' }))
  fireEvent.click(screen.getByRole('tab', { name: 'CONVERSATIONS' }))

  const listed = await screen.findByRole('button', { name: 'Why am I stalling?' })
  // Reopenable: the conversation is no longer the one the reader is in.
  expect(listed.hasAttribute('disabled')).toBe(false)
})

test('the start control names a conversation, and refuses while there is nothing to leave', async () => {
  render(<App />)
  await screen.findByText('notes.md')

  const start = screen.getByRole('button', { name: 'New conversation' })
  expect(start.getAttribute('aria-disabled')).toBe('true')
  expect(screen.getByText('You are already in a new conversation.')).toBeTruthy()

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  expect(start.getAttribute('aria-disabled')).toBe('false')
  expect(screen.queryByText('You are already in a new conversation.')).toBeNull()
})

test('a turn still landing elsewhere is said to be listed under CONVERSATIONS', async () => {
  render(<App />)
  await screen.findByText('notes.md')
  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText('Why am I stalling?')

  fireEvent.click(screen.getByRole('button', { name: 'New conversation' }))

  expect(screen.getByText(/listed under CONVERSATIONS when it lands/)).toBeTruthy()

  /* And once it has landed, there is nothing elsewhere to speak of. */
  turn.release()
  await waitFor(() =>
    expect(screen.queryByText(/listed under CONVERSATIONS when it lands/)).toBeNull(),
  )
})

/** A 200 whose body is not a list of turns: the read went through, what came back cannot
 *  be drawn. A proxy or a version skew is enough. */
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
/** The page over a stream of the given frames, asked one question. */
async function asked(parts: string[], held?: number): Promise<void> {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (path === '/api/ask') return streaming(parts, held)
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      if (path.endsWith('/scope') && !(path in served))
        return { ok: true, json: async () => ({ pin: null }) } as unknown as Response
      return { ok: true, json: async () => served[route(path)] ?? [] } as unknown as Response
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

/* The outer tests of story 21. Held under `test.fails` — vitest's strict xfail — while
   the list was worked through, so leaving the marker behind was not possible. */

/** The rail's file input, which has no label of its own — the label is the button. */
const upload = (name: string) => {
  const picker = document.querySelector('input[type="file"]') as HTMLInputElement
  fireEvent.change(picker, { target: { files: [new File(['notes'], name)] } })
}

test('a file uploaded twice is added quietly, and then said to be there already', async () => {
  const counts = [12, 0]
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (route(path) === '/api/documents' && init?.method === 'POST')
        return {
          ok: true,
          json: async () => ({ document: 'notes.md', chunks: counts.shift() }),
        } as unknown as Response
      return { ok: true, json: async () => served[route(path)] ?? [] } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  upload('notes.md')
  /* Nothing is *drawn* about the one that worked: the rail lists it, and a sentence
     saying so is the same news twice. It is read out, though — a list is not something
     a screen reader is told changed. */
  await waitFor(() =>
    expect(screen.getByRole('status', { name: 'Indexing' }).textContent).toBe(''),
  )
  expect(screen.queryByText(/passages\./)).toBeNull()
  const said = screen.getByRole('status', { name: 'Last upload' })
  await waitFor(() => expect(said.textContent).toContain('is indexed'))

  upload('notes.md')
  expect(
    await screen.findByText('“notes.md” is already in your documents.'),
  ).toBeTruthy()
})

/** The page with a rail whose uploads are answered in turn: a chunk count, or a refusal. */
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

  EXPLANATIONS.forEach((said) => expect(screen.queryByText(said)).toBeNull())

// ── a question waiting on the reader ──

/** A decision as the backend puts it: no fields, one action per option, and the way out
 *  as an action like the rest. Written out here rather than imported, because what the
 *  page is tested against is the payload and not the code that builds it. */
const asks = (
  prompt: string,
  options: { label: string; note?: string }[],
  decline: string,
) => ({
  prompt,
  fields: [],
  actions: [
    ...options.map((each) => ({
      label: each.label,
      answer: each.label,
      note: each.note ?? '',
      needs_valid: false,
      settled: '',
    })),
    {
      label: decline,
      answer: null,
      note: '',
      needs_valid: false,
      settled: 'You chose none of them.',
    },
  ],
})

const DECISION = asks(
  'Which bodyweight should I treat as current?',
  [
    { label: '77 kg', note: 'intake form, 17 Aug' },
    { label: '75 kg', note: 'coach notes, February' },
  ],
  'Do not use any of them',
)
const PAUSED = { asked: 'What is my BMR?', card: DECISION }
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
  answered: unknown = WEIGHED,
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
          ? holding(gate, frame('turn', answered))
          : stream(frame('turn', answered))
      if (path.endsWith('/pending'))
        return { ok: true, json: async () => pending } as unknown as Response
      return { ok: true, json: async () => served[route(path)] ?? [] } as unknown as Response
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

  expect(within(asked).getByText(DECISION.prompt)).toBeTruthy()
  expect(within(asked).getByRole('button', { name: /77 kg/ })).toBeTruthy()
  expect(within(asked).getByRole('button', { name: /75 kg/ })).toBeTruthy()
  expect(within(asked).getByRole('button', { name: DECISION.actions[2].label })).toBeTruthy()
})

test('picking an option finishes the turn, and the card stops offering any', async () => {
  /* The prompt stays: a settled card that no longer says what it was about is a line
     of an answer with nothing to read it against. What goes is the choosing. */
  const sent = stopping()
  const asked = await stopped()

  fireEvent.click(within(asked).getByRole('button', { name: /75 kg/ }))

  expect(await screen.findByText(/1,730 kcal/)).toBeTruthy()
  expect(of(sent, '/api/resume')[0].body.answer).toBe('75 kg')
  expect(screen.getByText(DECISION.prompt)).toBeTruthy()
  expect(screen.queryByRole('button', { name: /77 kg/ })).toBeNull()
})

test('a conversation is pinned to a field, and keeps it', async () => {
  const sent = () =>
    (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls
      .filter(([path]) => path === '/api/ask')
      .map(([, init]) => JSON.parse((init as RequestInit).body as string))

  render(<App />)
  await screen.findByText('notes.md')

  /* Unpinned, cora reads every question. The pick binds what comes next, so it is the
     next question that carries it. */
  pickPlugin('fitness')
  expect(screen.getByText(/next question/)).toBeTruthy()

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  turn.release()
  await screen.findByText(/Sleep, not volume/)

  expect(sent()).toEqual([
    { question: 'Why am I stalling?', thread_id: expect.any(String), pin: 'fitness' },
  ])
  /* The pin is in the thread's state now, so the control stops being a choice: a second
     field is a second conversation, and the reason is on the page for a screen reader. */
  expect(screen.queryByRole('list')).toBeNull()
  expect(screen.getByLabelText('Answer in').textContent).toBe('fitness')
  /* And the reason is read rather than clipped. It stands where the promise it replaces
     stood: a control that has become a fact owes the reader the fact, and a description
     hung off an unfocusable name reaches nobody either way. */
  const why = screen.getByText(/Start a new one/)
  expect(why.classList.contains('told-not-shown')).toBe(false)
})

test('the rail lists and uploads into the field it is set to', async () => {
  /* One field is what a turn can cite, so the rail shows the field it uploads into: a
     list of documents no turn in this field could reach would be a list that lies. */
  const held: Record<string, string[]> = { cora: ['notes.md'], travel: ['kyoto.md'] }
  let into: string | null = null
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (route(path) === '/api/documents' && init?.method === 'POST') {
        into = (init.body as FormData).get('scope') as string
        const added = { document: 'kyoto.md', chunks: 3 }
        return { ok: true, json: async () => added } as unknown as Response
      }
      if (route(path) === '/api/documents') {
        const asked = new URL(path, 'http://x').searchParams.get('scope') ?? 'cora'
        return { ok: true, json: async () => held[asked] ?? [] } as unknown as Response
      }
      const body = served[route(path)] ?? []
      return { ok: true, json: async () => body } as unknown as Response
    }),
  )
  render(<App />)
  await screen.findByText('notes.md')

  pickPlugin('travel')

  expect(await screen.findByText('kyoto.md')).toBeTruthy()
  expect(screen.queryByText('notes.md')).toBeNull()

  upload('kyoto.md')
  /* The row it indexes under is drawn in the field it was uploaded into, and the request
     carried that field. */
  await waitFor(() =>
    expect(screen.getByRole('status', { name: 'Indexing' }).textContent).toContain(
      'kyoto.md',
    ),
  )
  expect(into).toBe('travel')
})

// ── an effect waiting on the reader's word ──

/** A proposal as the backend puts it: the call laid out as fields nobody may write, and
 *  a yes carrying the call's own id so two effects cannot settle each other. */
const proposes = (
  call_id: string,
  tool: string,
  does: string,
  args: Record<string, unknown>,
) => ({
  prompt: does,
  fields: [
    { name: 'tool', schema: {}, value: tool, editable: false, required: false },
    ...Object.entries(args).map(([name, value]) => ({
      name,
      schema: {},
      value,
      editable: false,
      required: false,
    })),
  ],
  actions: [
    {
      label: 'Approve',
      answer: call_id,
      note: '',
      needs_valid: false,
      settled: 'You approved it.',
    },
    {
      label: 'Decline',
      answer: null,
      note: '',
      needs_valid: false,
      settled: 'You declined it. Nothing outside cora was changed.',
    },
  ],
})

const PROPOSAL = proposes(
  'c1',
  'save_itinerary',
  'Save an itinerary as a Markdown file the user keeps.',
  { title: 'Kyoto, three days' },
)
const PROPOSED = { asked: 'Save the Kyoto days.', card: PROPOSAL }
const SAVED = {
  answer: 'Saved it to cora-output/kyoto-three-days.md.',
  citations: [],
  trace: [],
}

/** A page whose turn proposes an effect, and whose approval finishes it. */
const proposing = (pending: unknown = null): Sent[] => {
  const sent: Sent[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (init?.body && typeof init.body === 'string')
        sent.push({ path, body: JSON.parse(init.body) })
      if (path === '/api/ask') return stream(frame('paused', PROPOSED))
      if (path === '/api/resume') return stream(frame('turn', SAVED))
      if (path.endsWith('/pending'))
        return { ok: true, json: async () => pending } as unknown as Response
      return {
        ok: true,
        json: async () => served[route(path)] ?? [],
      } as unknown as Response
    }),
  )
  return sent
}

const proposed = async () => {
  render(<App />)
  await screen.findByText('notes.md')
  askAbout('Save the Kyoto days.')
  return card()
}

test('a turn that proposes an effect draws what it would do and the call itself', async () => {
  proposing()

  const asked = await proposed()

  expect(within(asked).getByText(PROPOSAL.prompt)).toBeTruthy()
  expect(within(asked).getByText('save_itinerary')).toBeTruthy()
  expect(within(asked).getByText('Kyoto, three days')).toBeTruthy()
  expect(within(asked).getByRole('button', { name: 'Approve' })).toBeTruthy()
  expect(within(asked).getByRole('button', { name: 'Decline' })).toBeTruthy()
})

test('approving names the call it answers, and the turn finishes', async () => {
  const sent = proposing()
  const asked = await proposed()

  fireEvent.click(within(asked).getByRole('button', { name: 'Approve' }))

  expect(await screen.findByText(/kyoto-three-days\.md/)).toBeTruthy()
  expect(of(sent, '/api/resume')[0].body).toEqual({
    thread_id: expect.any(String),
    answer: 'c1',
    values: {},
  })
})

/** A round that proposes two effects: answering the first puts the second up. */
const GONE = { thread_id: 'gone', opened_with: 'A question asked twice' }
/** Two conversations, and what is served about them once one of them is deleted. */
const listing = (deleted: string[]): Record<string, unknown> => ({
  ...served,
  '/api/conversations': [
    { thread_id: 'old', opened_with: OLDER.question },
    GONE,
  ].filter((session) => !deleted.includes(session.thread_id)),
})

const deletable = (
  answer: (path: string) => Response | null = () => null,
): { deleted: string[] } => {
  const deleted: string[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        const said = answer(path)
        if (said) return said
        deleted.push(path)
        return { ok: true, status: 204 } as unknown as Response
      }
      if (path === '/api/ask') return answering()
      if (path.startsWith('/api/uploads/'))
        return { ok: true, json: async () => ({ text: KEPT }) } as unknown as Response
      const body = listing(deleted.map((each) => each.split('/').pop()!))[route(path)]
      return { ok: true, json: async () => body ?? [] } as unknown as Response
    }),
  )
  return { deleted }
}

const deleteControl = () =>
  screen.getByRole('button', { name: `Delete ${GONE.opened_with}` })

const confirm = () =>
  fireEvent.click(screen.getByRole('button', { name: 'Delete conversation' }))

test('a conversation deleted from the list leaves the list', async () => {
  const asked = deletable()
  render(<App />)
  fireEvent.click(screen.getByRole('tab', { name: 'CONVERSATIONS' }))
  await screen.findByRole('button', { name: GONE.opened_with })

  fireEvent.click(deleteControl())

  // The control asks, naming what it would delete; nothing has been asked of cora yet.
  expect(screen.getByRole('dialog', { name: 'DELETE CONVERSATION' })).toBeTruthy()
  expect(asked.deleted).toEqual([])

  confirm()

  await waitFor(() =>
    expect(screen.queryByRole('button', { name: GONE.opened_with })).toBeNull(),
  )
  expect(asked.deleted).toEqual(['/api/conversations/gone'])
  expect(screen.getByRole('button', { name: OLDER.question })).toBeTruthy()
  expect(screen.queryByRole('dialog')).toBeNull()
})

const FACT = { key: 'f1', text: 'No burpees.' }

/** The memory rail's own fixture: what cora holds, minus whatever has been forgotten,
 *  so a rail that says a fact is gone is a rail the store agrees with. */
const remembering = (...facts: { key: string; text: string }[]) => {
  let held = facts
  const asked: string[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        asked.push(path)
        held =
          path === '/api/memory'
            ? []
            : held.filter((fact) => fact.key !== path.slice('/api/memory/'.length))
        return { ok: true, status: 204 } as unknown as Response
      }
      if (route(path) === '/api/memory')
        return { ok: true, json: async () => held } as unknown as Response
      return { ok: true, json: async () => served[route(path)] ?? [] } as unknown as Response
    }),
  )
  return { asked }
}

const forgetting = (fact: { text: string }) =>
  screen.getByRole('button', { name: `Delete ${fact.text}` })

test('a fact is forgotten only once i have said so', async () => {
  const memory = remembering(FACT)
  render(<App />)
  fireEvent.click(screen.getByRole('tab', { name: 'MEMORY' }))
  await screen.findByText(FACT.text)

  // The control asks; nothing has been asked of cora yet.
  fireEvent.click(forgetting(FACT))
  expect(screen.getByRole('dialog')).toBeTruthy()
  expect(memory.asked).toEqual([])

  // Keeping it leaves the fact exactly where it was.
  fireEvent.click(screen.getByRole('button', { name: 'Keep it' }))
  expect(memory.asked).toEqual([])
  expect(screen.getByText(FACT.text)).toBeTruthy()

  fireEvent.click(forgetting(FACT))
  fireEvent.click(screen.getByRole('button', { name: 'Forget it' }))

  await waitFor(() => expect(memory.asked).toEqual(['/api/memory/f1']))
  await waitFor(() => expect(screen.queryByText(FACT.text)).toBeNull())
})

test('the conversation being read is named in the address', async () => {
  /* A conversation the reader is in should be one they can link to, come back to, and
     press back out of — none of which is possible while every conversation has the same
     address. */
  render(<App />)

  fireEvent.click(screen.getByRole('tab', { name: 'CONVERSATIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  await screen.findByText(OLDER.result.answer)

  expect(globalThis.location.hash).toBe('#/c/old')
})

/** The address changing under the page, which is what the back button does to it. */
/* ── deleting a plugin ──────────────────────────────────────────────────────────── */

/** Three fields, one of each kind a picker can hold: `fitness` brought by a plugin in
 *  the plugins folder, `travel` named by the configuration with no plugin behind it, and
 *  `birds` brought by a module the environment names, which is fixed at start. */
const LOADED = [
  {
    name: 'coach',
    scopes: ['fitness', 'travel'],
    /* `travel` is not here: the other plugin brings it too, so it stays behind. What
       cora says goes is what the question says goes. */
    going: ['fitness'],
    deletable: true,
  },
  { name: 'watching', scopes: ['birds', 'travel'], going: ['birds'], deletable: false },
]

const pluginFetch = (): { deleted: string[]; read: string[] } => {
  const deleted: string[] = []
  const read: string[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        deleted.push(path)
        return { ok: true, status: 204 } as unknown as Response
      }
      if (path === '/api/ask') return answering()
      read.push(route(path))
      const gone = deleted.length > 0
      const listings: Record<string, unknown> = {
        ...served,
        '/api/scopes': {
          available: gone ? ['travel', 'birds'] : ['fitness', 'travel', 'birds'],
          default: 'cora',
          /* The plugin under deletion brings its field a page, so what a delete does
             to the screen is what the listing does to this. */
          pages: gone ? {} : { fitness: '/pages/fitness/' },
        },
        '/api/plugins': gone ? LOADED.slice(1) : LOADED,
      }
      return {
        ok: true,
        json: async () => listings[route(path)] ?? [],
      } as unknown as Response
    }),
  )
  return { deleted, read }
}

const openMenu = async () => {
  await screen.findByRole('button', { name: 'Plugin' })
  fireEvent.click(screen.getByRole('button', { name: 'Plugin' }))
  return screen.getByRole('list')
}

test('a plugin confirmed away takes its field out of the picker', async () => {
  const asked = pluginFetch()
  render(<App />)
  const fields = await openMenu()
  fireEvent.click(
    within(fields).getByRole('button', { name: 'Delete the fitness plugin' }),
  )

  asked.read.length = 0
  fireEvent.click(screen.getByRole('button', { name: 'Delete plugin' }))

  await waitFor(() => expect(asked.deleted).toEqual(['/api/plugins/coach']))
  /* What went through is confirmed by reading the listings again rather than by the
     page's own account of what a delete changed — and a plugin's delete changes three
     of them. */
  await waitFor(() =>
    expect(new Set(asked.read)).toEqual(
      new Set([
        '/api/scopes',
        '/api/plugins',
        '/api/documents',
        '/api/conversations',
        '/api/memory',
      ]),
    ),
  )
  expect(screen.queryByRole('dialog')).toBeNull()
  const left = await openMenu()
  expect(within(left).queryByRole('button', { name: 'fitness' })).toBeNull()
  // The field the other plugin also brings is still offered, and still holds what it held.
  expect(within(left).getByRole('button', { name: 'travel' })).toBeTruthy()
})

/* The outer test of the page-in-the-centre story. Held under `test.fails` — vitest's
   strict xfail — while the list was worked through, so leaving the marker behind was not
   possible. */
test('a field with a page is worked in it, with the conversation beside', async () => {
  const frame = await opened()

  expect(frame.getAttribute('src')).toBe('/pages/fitness/')
  expect(within(rail()).getByPlaceholderText(/Ask a question/)).toBeTruthy()
})

/* ── a page in the centre ── */

/** The rail the panels live in, which is where the conversation goes beside a page. */
const rail = () =>
  document.querySelector('.' + appCss.railPanels) as HTMLElement

/** The region the screen is about — the page where one is drawn, the conversation where
 *  none is. One landmark either way, so a reader lands on what they came for. */
const centre = () => screen.getByRole('main')

const opened = async () => {
  bringsAPage()
  render(<App />)
  await screen.findByText('notes.md')
  pickPlugin('fitness')
  const frame = (await screen.findByTitle('fitness')) as HTMLIFrameElement
  /* The conversation is the conversations panel's other state, so that is where it is. */
  fireEvent.click(within(rail()).getByRole('tab', { name: 'CONVERSATIONS' }))
  return frame
}

const ask = (where: HTMLElement, said: string) => {
  fireEvent.change(within(where).getByPlaceholderText(/Ask a question/), {
    target: { value: said },
  })
  fireEvent.click(within(where).getByRole('button', { name: 'Ask' }))
  /* The fixture holds the turn open until it is let go, which is how the specs above
     watch a turn while it runs. These are about where it is drawn, not when. */
  turn.release()
}

test('the frame is the plugin’s own: named for its field, allowed the camera, contained in nothing', async () => {
  const frame = await opened()

  expect(frame.getAttribute('src')).toBe('/pages/fitness/')
  expect(frame.getAttribute('allow')).toContain('camera')
  /* Not sandboxed: an opaque origin would cost the page both cora's API and the camera,
     and a containment that holds neither is worse than saying there is none. */
  expect(frame.hasAttribute('sandbox')).toBe(false)
})

test('a fixed field with no page leaves the conversation in the middle', async () => {
  bringsAPage()
  render(<App />)
  await screen.findByText('notes.md')

  pickPlugin('travel')

  expect(screen.queryByTitle('travel')).toBeNull()
  expect(within(centre()).getByPlaceholderText(/Ask a question/)).toBeTruthy()
})

test('with a page drawn the conversation is in the rail and not in the middle', async () => {
  await opened()

  expect(within(rail()).getByPlaceholderText(/Ask a question/)).toBeTruthy()
  expect(within(centre()).queryByPlaceholderText(/Ask a question/)).toBeNull()
})

test('a question asked in the rail is answered there', async () => {
  await opened()

  ask(rail(), 'How many sets?')

  expect(await within(rail()).findByText(/Sleep, not volume/)).toBeTruthy()
  expect(within(rail()).getAllByText('How many sets?').length).toBeGreaterThan(0)
})

test('the region the screen is about holds the page, and the conversation where there is none', async () => {
  await opened()
  expect(within(centre()).getByTitle('fitness')).toBeTruthy()
  expect(screen.getAllByRole('main')).toHaveLength(1)

  cleanup()
  render(<App />)
  await screen.findByText('notes.md')

  expect(within(centre()).getByPlaceholderText(/Ask a question/)).toBeTruthy()
})

test('folding the rail and unfolding it draws the conversation with its turns', async () => {
  await opened()
  ask(rail(), 'How many sets?')
  await within(rail()).findByText(/Sleep, not volume/)

  fireEvent.click(screen.getByRole('button', { name: /Plan & memory/ }))
  expect(within(rail()).queryByPlaceholderText(/Ask a question/)).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: /Plan & memory/ }))

  expect(await within(rail()).findByText(/Sleep, not volume/)).toBeTruthy()
})

test('a page that asks for the screen has it while both rails are folded', async () => {
  await opened()
  const wants = (wanted: boolean, origin = window.location.origin) =>
    fireEvent(
      window,
      new MessageEvent('message', { data: { cora: 'screen', wanted }, origin }),
    )
  const alone = () =>
    (document.querySelector('.' + appCss.columns) as HTMLElement).classList.contains(
      appCss.alone,
    )
  const fold = (named: RegExp) => fireEvent.click(screen.getByRole('button', { name: named }))

  /* Asked beside an open rail the frame stays where it was; with both folded the rails
     go unseen and it has the screen; let go, they are back. */
  wants(true)
  expect(alone(), 'beside an open rail').toBe(false)
  fold(/Documents/)
  fold(/Plan & memory/)
  expect(alone(), 'with both rails folded').toBe(true)
  wants(false)
  expect(alone(), 'let go').toBe(false)

  /* Only cora's own origin is heard: the trainer embeds a foreign player whose messages
     reach this window too. */
  wants(true, 'https://www.youtube.com')
  expect(alone(), 'asked from another origin').toBe(false)

  /* The shell's own way back: the rails are unreachable while the page has the screen,
     so a page that asks and never lets go is not a page the reader is stuck in. */
  wants(true)
  expect(alone()).toBe(true)
  fireEvent.keyDown(window, { key: 'Escape' })
  expect(alone(), 'after Escape').toBe(false)

  /* The asking goes with the page: back to plain chat and fixed to the field again, the
     frame drawn the second time has not asked. */
  wants(true)
  expect(alone()).toBe(true)
  fold(/Plan & memory/)
  fireEvent.click(screen.getByRole('button', { name: 'Chat' }))
  expect(alone(), 'with no page').toBe(false)
  pickPlugin('fitness')
  await screen.findByTitle('fitness')
  fold(/Plan & memory/)
  expect(alone(), 'fixed to the page again').toBe(false)
})

/** A render that throws is a sentence on the page and a line on the console. The spy
 *  keeps React's own report out of the suite's output, which is otherwise a wall. */
const quietly = async (draw: () => Promise<void>) => {
  const said = vi.spyOn(console, 'error').mockImplementation(() => {})
  try {
    await draw()
  } finally {
    said.mockRestore()
  }
}

test('a panel that cannot be drawn is a sentence, and the page still stands', async () => {
  await quietly(async () => {
    /* A listing the panel cannot read, which is the shape the frontend spec names. Set
       before the page reads it: the read is held, and a fixture changed afterwards is
       one nothing asks for again. */
    served['/api/conversations'] = {} as unknown as []
    await opened()

    back()

    expect(await within(rail()).findByText('This panel could not be drawn.')).toBeTruthy()
    expect(screen.getByTitle('fitness')).toBeTruthy()
  })
})
test('the conversation in the rail is a region of its own, inside no second main', async () => {
  await opened()

  /* A region of its own, named for what it is — which conversation it holds is the
     heading the panel puts over it. */
  const talk = within(rail()).getByRole('region', { name: 'Conversation' })
  expect(within(talk).getByPlaceholderText(/Ask a question/)).toBeTruthy()
  expect(screen.getAllByRole('main')).toHaveLength(1)
  expect(
    within(centre()).queryByRole('region', { name: 'Conversation' }),
  ).toBeNull()
})

test('deleting the plugin of the fixed field returns the conversation to the middle', async () => {
  /* The listings are held from the moment the delete goes out, so what is asserted is
     what the reader's own act did and not what the read that follows would have done
     anyway. In a browser that difference is a page left standing over a field that is
     gone until the network answers. */
  const reread = held()
  const deleted: string[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        deleted.push(path)
        return { ok: true, status: 204 } as unknown as Response
      }
      if (deleted.length > 0) await reread.until
      const listings: Record<string, unknown> = {
        ...served,
        '/api/scopes': {
          available: ['fitness', 'travel', 'birds'],
          default: 'cora',
          pages: { fitness: '/pages/fitness/' },
        },
        '/api/plugins': LOADED,
      }
      return {
        ok: true,
        json: async () => listings[route(path)] ?? [],
      } as unknown as Response
    }),
  )
  render(<App />)
  const fields = await openMenu()
  fireEvent.click(within(fields).getByRole('button', { name: 'fitness' }))
  expect(await screen.findByTitle('fitness')).toBeTruthy()

  /* Pinned, the segment that opens the picker is named for the field rather than for
     the act — so this is the same menu, reached the way a reader reaches it. */
  fireEvent.click(screen.getByRole('button', { name: 'fitness' }))
  fireEvent.click(
    within(screen.getByRole('list')).getByRole('button', {
      name: 'Delete the fitness plugin',
    }),
  )
  fireEvent.click(screen.getByRole('button', { name: 'Delete plugin' }))

  /* The reader's own act puts it back, and not the read that follows it: asserted
     before any listing could have been asked for again, so a page still up here is one
     waiting on the network to take it down. */
  await flushed()
  expect(screen.queryByTitle('fitness')).toBeNull()
  expect(within(centre()).getByPlaceholderText(/Ask a question/)).toBeTruthy()
})

/* The outer test of the chat-in-the-rail story. Held under `test.fails` — vitest's
   strict xfail — while the list was worked through, so leaving it behind was not
   possible. */
test('a fixed field\u2019s conversation is chatted in the rail, the others one click behind', async () => {
  bringsAPage()
  served['/api/conversations'] = [
    { thread_id: 'old', opened_with: OLDER.question, pin: 'fitness' },
  ]
  render(<App />)
  await screen.findByText('notes.md')
  pickPlugin('fitness')
  await screen.findByTitle('fitness')

  /* The rail is the conversation, not a list with a conversation under it. */
  expect(within(rail()).getByRole('heading', { name: /New conversation/ })).toBeTruthy()
  expect(within(rail()).getByPlaceholderText(/Ask a question/)).toBeTruthy()

  fireEvent.click(within(rail()).getByRole('button', { name: /Back to other conversations/i }))

  /* And the others are behind it, each marked for the field it belongs to. */
  const listed = within(rail()).getByRole('button', { name: OLDER.question })
  expect(listed).toBeTruthy()
  expect(within(rail()).queryByPlaceholderText(/Ask a question/)).toBeNull()
})

/** The conversations panel, with a conversation of a page-bringing field open in it. */
const chatting = async (
  sessions: { thread_id: string; opened_with: string; pin: string | null }[] = [
    { thread_id: 'old', opened_with: OLDER.question, pin: 'fitness' },
  ],
) => {
  bringsAPage()
  served['/api/conversations'] = sessions
  render(<App />)
  await screen.findByText('notes.md')
  pickPlugin('fitness')
  await screen.findByTitle('fitness')
  fireEvent.click(within(rail()).getByRole('tab', { name: 'CONVERSATIONS' }))
}

const back = () =>
  fireEvent.click(within(rail()).getByRole('button', { name: /Back to other conversations/i }))

test('a conversation of a field with a page is marked in the list, and others are not', async () => {
  await chatting([
    { thread_id: 'old', opened_with: OLDER.question, pin: 'fitness' },
    { thread_id: 'plain', opened_with: 'Where to start investing', pin: null },
    { thread_id: 'trip', opened_with: 'A week in Lisbon', pin: 'travel' },
  ])

  back()

  /* The mark says the rail will chat it, which is the page and not the pin: travel is
     pinned too and brings no page. */
  expect(within(rail()).getByLabelText(`${OLDER.question} opens as a chat here`)).toBeTruthy()
  expect(within(rail()).queryByLabelText('A week in Lisbon opens as a chat here')).toBeNull()
  expect(
    within(rail()).queryByLabelText('Where to start investing opens as a chat here'),
  ).toBeNull()
  expect(within(rail()).getByText(/opens as a chat in this rail/i)).toBeTruthy()
})

test('the chat is headed by what opened the conversation, its field and its length', async () => {
  await chatting()

  expect(within(rail()).getByRole('heading', { name: /New conversation/ })).toBeTruthy()

  ask(rail(), 'How many sets?')
  await within(rail()).findByText(/Sleep, not volume/)

  /* Headed by the question it was opened with. Which field it is in is the page it is
     drawn beside, and how long it is, is the scroll. */
  expect(within(rail()).getByRole('heading', { name: 'How many sets?' })).toBeTruthy()
})

test('the way back shows the list, and opening a marked one chats it', async () => {
  await chatting()
  back()

  expect(within(rail()).queryByPlaceholderText(/Ask a question/)).toBeNull()
  fireEvent.click(within(rail()).getByRole('button', { name: OLDER.question }))

  expect(await within(rail()).findByRole('heading', { name: OLDER.question })).toBeTruthy()
  expect(within(rail()).getByPlaceholderText(/Ask a question/)).toBeTruthy()
  /* And the page was never disturbed by any of it. */
  expect(screen.getByTitle('fitness')).toBeTruthy()
})

test('a turn asked in the rail leaves the panels on the conversations tab', async () => {
  await chatting()

  ask(rail(), 'How many sets?')
  await within(rail()).findByText(/Sleep, not volume/)

  expect(within(rail()).getByRole('tab', { name: 'CONVERSATIONS' }).getAttribute('aria-selected')).toBe(
    'true',
  )
})

test('a turn asked from the middle still moves the panels to the steps', async () => {
  render(<App />)
  await screen.findByText('notes.md')

  ask(centre(), 'Why am I stalling?')
  await within(centre()).findByText(/Sleep, not volume/)

  expect(within(rail()).getByRole('tab', { name: 'STEPS' }).getAttribute('aria-selected')).toBe(
    'true',
  )
})

test('opening a conversation fixed to nothing returns it to the middle', async () => {
  await chatting([
    { thread_id: 'old', opened_with: OLDER.question, pin: 'fitness' },
    { thread_id: 'plain', opened_with: 'Where to start investing', pin: null },
  ])
  back()

  fireEvent.click(within(rail()).getByRole('button', { name: 'Where to start investing' }))

  /* Fixed to nothing is drawn where every conversation without a page is drawn, and the
     rail goes back to being the list of them. */
  await waitFor(() =>
    expect(within(centre()).getByPlaceholderText(/Ask a question/)).toBeTruthy(),
  )
  expect(screen.queryByTitle('fitness')).toBeNull()
  expect(within(rail()).getByRole('button', { name: OLDER.question })).toBeTruthy()
})

test('a conversation fixed to nothing draws no chat in the rail at all', async () => {
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.click(within(rail()).getByRole('tab', { name: 'CONVERSATIONS' }))

  expect(within(centre()).getByPlaceholderText(/Ask a question/)).toBeTruthy()
  expect(within(rail()).queryByPlaceholderText(/Ask a question/)).toBeNull()
  expect(within(rail()).getByRole('button', { name: OLDER.question })).toBeTruthy()
})

test('the rail does not name the field at all: the page beside it is the field', async () => {
  await chatting()
  ask(rail(), 'How many sets?')
  await within(rail()).findByText(/Sleep, not volume/)

  /* The head already says which conversation this is and which field it is in, so the
     strip that says the same under it is a second answer to a question nobody asked
     twice — and the sentence explaining that a pin is for good is two lines of a rail
     that has none to spare. */
  expect(within(rail()).queryByRole('group', { name: 'Answer in' })).toBeNull()
  expect(within(rail()).queryByText(/keeps the field it is pinned to/)).toBeNull()
  expect(within(rail()).queryByText(/fitness/)).toBeNull()
})

test('a pinned conversation in the middle still says which field it is in', async () => {
  /* Nothing else names it there, so the strip is the only answer. */
  render(<App />)
  await screen.findByText('notes.md')
  pickPlugin('travel')

  ask(centre(), 'A week in Lisbon?')
  await within(centre()).findByText(/Sleep, not volume/)

  expect(within(centre()).getByRole('group', { name: 'Answer in' })).toBeTruthy()
  expect(within(centre()).getByText(/keeps the field it is pinned to/)).toBeTruthy()
})
