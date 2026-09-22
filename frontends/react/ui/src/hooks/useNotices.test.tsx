import { cleanup, render } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { useNotices } from './useNotices'
import type { Session } from '../api'

/* The rule, without a browser: a field that was written to opens its own conversation.
   The poll is driven by the fake clock rather than waited on — five seconds a case would
   be the whole tier's runtime spent sitting still. */

const FITNESS = 'fitness'
const OLDER: Session = { thread_id: 'older', opened_with: 'squats', pin: FITNESS }
const NEWER: Session = { thread_id: 'newer', opened_with: 'presses', pin: FITNESS }
const ELSEWHERE: Session = { thread_id: 'elsewhere', opened_with: 'kyoto', pin: null }

/** What each field's notice answers, in the order it is asked. The last answer stands,
 *  so a case says "nothing, then this" and the poll does the rest. */
let answers: Record<string, unknown>[] = []

function Watches({ pages, sessions, here }: { pages: string[]; sessions: Session[]; here: string }) {
  useNotices({ pages, sessions, here })
  return null
}

const asked = () => vi.mocked(globalThis.fetch).mock.calls.map(([path]) => String(path))

/** One poll: the interval fires and every request it made has settled. */
async function polled() {
  await vi.advanceTimersByTimeAsync(5000)
}

beforeEach(() => {
  vi.useFakeTimers()
  answers = [{ notice: null }]
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => {
      const said = answers.length > 1 ? answers.shift() : answers[0]
      return { ok: true, status: 200, json: async () => said } as Response
    }),
  )
  globalThis.location.hash = ''
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

test('a notice written to a field opens that field\'s conversation', async () => {
  answers = [{ notice: null }, { notice: { workout: 'running' }, at: 1000 }]

  render(<Watches pages={[FITNESS]} sessions={[NEWER]} here="elsewhere" />)
  await polled()

  expect(globalThis.location.hash).toBe('#/c/newer')
})

test('the newest conversation pinned to the field is the one opened', async () => {
  /* Newest first is the order cora lists them in, so the first match is the answer —
     asserted here because a sort added anywhere above this would break it silently. */
  answers = [{ notice: null }, { notice: {}, at: 1000 }]

  render(<Watches pages={[FITNESS]} sessions={[NEWER, OLDER]} here="elsewhere" />)
  await polled()

  expect(globalThis.location.hash).toBe('#/c/newer')
})

test('a field nothing is pinned to opens nothing', async () => {
  answers = [{ notice: null }, { notice: {}, at: 1000 }]

  render(<Watches pages={[FITNESS]} sessions={[ELSEWHERE]} here="elsewhere" />)
  await polled()

  expect(globalThis.location.hash).toBe('')
})

test('a notice naming the conversation already open moves nothing', async () => {
  answers = [{ notice: null }, { notice: {}, at: 1000 }]

  render(<Watches pages={[FITNESS]} sessions={[NEWER]} here="newer" />)
  await polled()

  expect(globalThis.location.hash).toBe('')
})

test('the notice standing when the page loads opens nothing', async () => {
  /* A notice outlives the page that wrote it. Acting on the one already there would
     drag the reader into a conversation on every reload. */
  answers = [{ notice: { workout: 'running' }, at: 1000 }]

  render(<Watches pages={[FITNESS]} sessions={[NEWER]} here="elsewhere" />)
  await polled()
  await polled()

  expect(globalThis.location.hash).toBe('')
})

test('a second notice opens the conversation again once the reader has left it', async () => {
  answers = [
    { notice: null },
    { notice: {}, at: 1000 },
    { notice: {}, at: 2000 },
  ]

  const drawn = render(<Watches pages={[FITNESS]} sessions={[NEWER]} here="elsewhere" />)
  await polled()
  expect(globalThis.location.hash).toBe('#/c/newer')

  /* The reader walked away again, and the wrist spoke a second time. */
  globalThis.location.hash = ''
  drawn.rerender(<Watches pages={[FITNESS]} sessions={[NEWER]} here="elsewhere" />)
  await polled()

  expect(globalThis.location.hash).toBe('#/c/newer')
})

test('only fields with a page are asked', async () => {
  render(<Watches pages={[FITNESS]} sessions={[NEWER]} here="elsewhere" />)
  await polled()

  expect(asked().every((path) => path.includes(FITNESS))).toBe(true)
  expect(asked().length).toBeGreaterThan(0)
})

test('a deployment where no field has a page asks for nothing', async () => {
  render(<Watches pages={[]} sessions={[NEWER]} here="elsewhere" />)
  await polled()

  expect(asked()).toEqual([])
})

test('a notice that cannot be read leaves the page alone', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('cora could not be reached.') }))

  render(<Watches pages={[FITNESS]} sessions={[NEWER]} here="elsewhere" />)
  await polled()
  await polled()

  expect(globalThis.location.hash).toBe('')
})

test('a poll torn down partway through asks no further field', async () => {
  /* The reader leaves while the first field is still answering. What the poll has not
     asked for yet it no longer needs, and a torn-down effect asking on is a request per
     remaining field for a screen nobody is looking at. */
  const KITCHEN = 'kitchen'
  let held: (() => void) | undefined
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => {
      if (String(path).includes(FITNESS)) await new Promise<void>((settle) => (held = settle))
      return { ok: true, status: 200, json: async () => ({ notice: null }) } as Response
    }),
  )

  const drawn = render(<Watches pages={[FITNESS, KITCHEN]} sessions={[NEWER]} here="elsewhere" />)
  await vi.advanceTimersByTimeAsync(0)
  drawn.unmount()
  held?.()
  await vi.advanceTimersByTimeAsync(0)

  expect(asked()).toEqual([`/api/scopes/${FITNESS}/notice`])
})

/* A tab nobody is looking at has no screen to take, and a phone in a pocket polling
   every five seconds forever is a cost with nothing on the other side of it. */
test('a hidden tab is not polled', async () => {
  const hidden = vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden')
  render(<Watches pages={[FITNESS]} sessions={[NEWER]} here="" />)
  const before = asked().length

  await polled()
  await polled()

  expect(asked().length).toBe(before)
  hidden.mockRestore()
})
