import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { useRef, useState } from 'react'
import { useDocuments } from './useDocuments'
import type { Read } from './useSource'

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, status: 204 }) as Response),
  )
})

afterEach(cleanup)

/** The panel's state held for real, so what `erase` does to it is what is asserted —
 *  not which calls were made on a spy. */
function Deleting({ reading, from }: { reading: Read; from: Read }) {
  const [read, setRead] = useState<Read | null>(reading)
  const here = useRef('thread')
  const { erase } = useDocuments({
    field: from.scope,
    here,
    refresh: async () => {},
    setTrouble: () => {},
    setRead,
  })
  return (
    <>
      <button onClick={() => void erase(from.scope, from.document)}>delete</button>
      <p>{read ? `${read.document} in ${read.scope}` : 'nothing open'}</p>
    </>
  )
}

test('deleting the document the panel is reading closes it', async () => {
  render(
    <Deleting
      reading={{ document: 'kyoto.md', scope: 'travel' }}
      from={{ document: 'kyoto.md', scope: 'travel' }}
    />,
  )

  screen.getByText('delete').click()

  await waitFor(() => expect(screen.getByText('nothing open')).toBeTruthy())
})

test('deleting the same name in another field leaves the panel reading', async () => {
  /* One name covers a document in each field, and what was deleted is the other field's.
     The panel is reading a file that is still there, so it stays open on it. */
  render(
    <Deleting
      reading={{ document: 'kyoto.md', scope: 'fitness' }}
      from={{ document: 'kyoto.md', scope: 'travel' }}
    />,
  )

  screen.getByText('delete').click()
  await waitFor(() =>
    expect(vi.mocked(globalThis.fetch)).toHaveBeenCalledTimes(1),
  )

  expect(screen.getByText('kyoto.md in fitness')).toBeTruthy()
})

/** An upload held open, so what the rail draws *during* one is what is asserted. */
function Uploading({ field = 'cora' }: { field?: string }) {
  const here = useRef('thread')
  const { indexing, notice, upload } = useDocuments({
    field,
    here,
    refresh: async () => {},
    setTrouble: () => {},
    setRead: () => {},
  })
  return (
    <>
      <button onClick={() => void upload(new File(['x'], 'deadlift.pdf'))}>
        upload
      </button>
      <p>{indexing.join(', ') || 'nothing indexing'}</p>
      <p>{notice ? notice.said : 'nothing said'}</p>
    </>
  )
}

const held = () => {
  let done = (added: { document: string; chunks: number }) => {
    void added
  }
  const answer = new Promise<{ document: string; chunks: number }>((settle) => {
    done = settle
  })
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: () => answer }) as unknown as Response),
  )
  return { done: (added: { document: string; chunks: number }) => done(added) }
}

test('a file is listed as indexing while its upload runs, and not after', async () => {
  const upload = held()
  render(<Uploading />)

  screen.getByText('upload').click()
  await waitFor(() => expect(screen.getByText('deadlift.pdf')).toBeTruthy())

  upload.done({ document: 'deadlift.pdf', chunks: 12 })

  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
})

test('an upload that indexed something says nothing: the list says it', async () => {
  const upload = held()
  render(<Uploading />)

  screen.getByText('upload').click()
  upload.done({ document: 'deadlift.pdf', chunks: 12 })

  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
  expect(screen.getByText('nothing said')).toBeTruthy()
})

test('bytes the field already had are said, because the list will not change', async () => {
  const upload = held()
  render(<Uploading />)

  screen.getByText('upload').click()
  upload.done({ document: 'deadlift.pdf', chunks: 0 })

  await waitFor(() =>
    expect(
      screen.getByText('“deadlift.pdf” is already in your documents.'),
    ).toBeTruthy(),
  )
})

test('an upload that failed leaves nothing indexing', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) }) as Response),
  )
  render(<Uploading />)

  screen.getByText('upload').click()

  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
})
