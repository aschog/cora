import { beforeEach, expect, test, vi } from 'vitest'
import { forget, forgetEverything } from './api'

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
