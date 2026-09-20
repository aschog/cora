import { afterEach, expect, test, vi } from 'vitest'
import { read, ReadingFailed } from './reading'

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

afterEach(() => {
  delete (window as unknown as { Tesseract?: unknown }).Tesseract
  vi.restoreAllMocks()
})

test('an image is read into the text recognised in it', async () => {
  stand('Hilfe  help')

  expect(await read(shot())).toBe('Hilfe  help')
})

/* The reader is megabytes of WebAssembly and trained data. A second photo in the same
   session uses the one already there rather than fetching it again. */
test('a second reading uses the reader already there', async () => {
  const made = stand('Haus  house')

  expect(await read(shot())).toBe('Haus  house')
  expect(await read(shot())).toBe('Haus  house')

  expect(made).toHaveBeenCalledTimes(2)
  expect(document.querySelectorAll('script[src*="tesseract"]')).toHaveLength(0)
})

/* Nothing read and nothing fetched are different facts, and a reader told the wrong one
   goes and fixes the wrong thing. */
test('a reader that cannot be fetched fails as that', async () => {
  await expect(read(shot())).rejects.toBeInstanceOf(ReadingFailed)
})
