import { afterEach, beforeEach, expect, test, vi } from 'vitest'

/* The module memoises the fetched reader for the life of the page, so each test gets
   its own copy of it — otherwise one test's memo decides the next test's answer. */
const load = async () => {
  vi.resetModules()
  return import('./reading')
}

type Worker = {
  recognize: (image: Blob) => Promise<{ data: { text: string } }>
  terminate: () => Promise<void>
}

const stand = (text: string) => {
  const made = vi.fn(async (): Promise<Worker> => ({
    recognize: async () => ({ data: { text } }),
    terminate: async () => undefined,
  }))
  ;(window as unknown as { Tesseract: unknown }).Tesseract = { createWorker: made }
  return made
}

const shot = () => new File([new Uint8Array([1])], 'words.png', { type: 'image/png' })

/** Scripts appended while this is on, each answering as the caller says. */
const scriptsThat = (answer: 'load' | 'error') => {
  const seen: HTMLScriptElement[] = []
  const made = document.createElement.bind(document)
  vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
    const element = made(tag) as HTMLScriptElement
    if (tag === 'script') {
      seen.push(element)
      queueMicrotask(() =>
        answer === 'load'
          ? element.onload?.(new Event('load'))
          : element.onerror?.(new Event('error')),
      )
    }
    return element
  })
  return seen
}

beforeEach(() => {
  delete (window as unknown as { Tesseract?: unknown }).Tesseract
})

afterEach(() => {
  vi.restoreAllMocks()
})

test('an image is read into the text recognised in it', async () => {
  const { read } = await load()
  stand('Hilfe  help')

  expect(await read(shot())).toBe('Hilfe  help')
})

/* The reader is megabytes of WebAssembly and trained data. A second photo in the same
   session uses the one already there rather than fetching it again. */
test('a second reading uses the reader already there', async () => {
  const { read } = await load()
  const made = stand('Haus  house')

  expect(await read(shot())).toBe('Haus  house')
  expect(await read(shot())).toBe('Haus  house')

  expect(made).toHaveBeenCalledTimes(2)
  expect(document.querySelectorAll('script[src*="tesseract"]')).toHaveLength(0)
})

/* Nothing read and nothing fetched are different facts, and a reader told the wrong one
   goes and fixes the wrong thing. */
test('a reader that cannot be fetched fails as that', async () => {
  const { read, ReadingFailed } = await load()
  scriptsThat('error')

  await expect(read(shot())).rejects.toBeInstanceOf(ReadingFailed)
})

/* Found in review: a script that loaded but defined nothing rejected while the memo
   kept pointing at the rejected promise, so every later photo in that session failed
   instantly off the cache without trying again. */
test('a load that defined nothing is tried again for the next photo', async () => {
  const { read, ReadingFailed } = await load()
  const first = scriptsThat('load')

  await expect(read(shot())).rejects.toBeInstanceOf(ReadingFailed)
  expect(first).toHaveLength(1)

  vi.restoreAllMocks()
  const second = scriptsThat('load')
  await expect(read(shot())).rejects.toBeInstanceOf(ReadingFailed)

  expect(second).toHaveLength(1)
  expect(document.querySelectorAll('script[src*="tesseract"]')).toHaveLength(0)
})
