import { beforeEach, expect, test, vi } from 'vitest'
import { ask, forget, forgetEverything } from './api'

const answering = (status: number, body?: unknown) =>
  vi.fn(
    async () =>
      ({
        ok: status >= 200 && status < 300,
        status,
        json: async () => {
          if (body === undefined) throw new SyntaxError('Unexpected end of JSON input')
          return body
        },
      }) as unknown as Response,
  )

beforeEach(() => vi.unstubAllGlobals())

test('a fact forgotten answers with no body, and that is not a failure', async () => {
  vi.stubGlobal('fetch', answering(204))

  await expect(forget('f1')).resolves.toBeUndefined()
  await expect(forgetEverything()).resolves.toBeUndefined()
})

test('a store that cannot be written says so rather than reporting success', async () => {
  /* The page shows the fact still in the list; if the rejection is swallowed the reader
     is never told why it did not go. */
  vi.stubGlobal(
    'fetch',
    answering(503, { error: 'The document service is temporarily unavailable.' }),
  )

  await expect(forget('f1')).rejects.toThrow(/temporarily unavailable/)
  await expect(forgetEverything()).rejects.toThrow(/temporarily unavailable/)
})


test('the body is released once the answer has arrived', async () => {
  /* The turn is the last thing on the wire, so the reader returns at it — and a reader
     that returns without cancelling holds a response body nobody will read again. */
  let released = false
  const encoder = new TextEncoder()
  const frames = [
    'event: step\ndata: {"summary":"a","detail":"","failed":false,"origin":""}\n\n',
    'event: turn\ndata: {"answer":"done","citations":[],"trace":[]}\n\n',
    'event: step\ndata: {"summary":"never read","detail":"","failed":false,"origin":""}\n\n',
  ]
  let next = 0
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      body: {
        getReader: () => ({
          cancel: async () => {
            released = true
          },
          read: async () =>
            next === frames.length
              ? { done: true, value: undefined }
              : { done: false, value: encoder.encode(frames[next++]) },
        }),
      },
    }) as unknown as Response),
  )

  const result = await ask('why?', 't1', () => {})

  expect(result.answer).toBe('done')
  expect(released).toBe(true)
})

test('each piece of the answer is reported as it arrives, and the turn still resolves', async () => {
  const encoder = new TextEncoder()
  const frames = [
    'event: step\ndata: {"summary":"a","detail":"","failed":false,"origin":""}\n\n',
    'event: text\ndata: {"text":"Sleep, "}\n\n',
    'event: text\ndata: {"text":"not volume."}\n\n',
    'event: turn\ndata: {"answer":"Sleep, not volume.","citations":[],"trace":[]}\n\n',
  ]
  let next = 0
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      body: {
        getReader: () => ({
          cancel: async () => {},
          read: async () =>
            next === frames.length
              ? { done: true, value: undefined }
              : { done: false, value: encoder.encode(frames[next++]) },
        }),
      },
    }) as unknown as Response),
  )
  const written: string[] = []

  const result = await ask('why?', 't1', () => {}, (piece) => written.push(piece))

  expect(written).toEqual(['Sleep, ', 'not volume.'])
  expect(result.answer).toBe('Sleep, not volume.')
})
