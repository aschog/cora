import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
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
  const { indexing, indexed, notice, upload } = useDocuments({
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
      <p>{indexed ? `indexed ${indexed}` : 'nothing indexed'}</p>
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

/** The click through `fireEvent`, so React has flushed by the time an assertion runs.
 *  A raw `.click()` leaves the first synchronous `waitFor` check reading the render
 *  before the upload started — where "nothing indexing" is already true, and a test
 *  that only ever asserted that cannot fail. */
const start = () => fireEvent.click(screen.getByText('upload'))

test('a file is listed as indexing while its upload runs, and not after', async () => {
  const upload = held()
  render(<Uploading />)

  start()
  await waitFor(() => expect(screen.getByText('deadlift.pdf')).toBeTruthy())

  upload.done({ document: 'deadlift.pdf', chunks: 12 })

  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
})

test('an upload that indexed something says nothing: the list says it', async () => {
  const upload = held()
  render(<Uploading />)

  start()
  await waitFor(() => expect(screen.getByText('deadlift.pdf')).toBeTruthy())
  upload.done({ document: 'deadlift.pdf', chunks: 12 })

  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
  expect(screen.getByText('nothing said')).toBeTruthy()
})

test('bytes the field already had are said, because the list will not change', async () => {
  const upload = held()
  render(<Uploading />)

  start()
  await waitFor(() => expect(screen.getByText('deadlift.pdf')).toBeTruthy())
  upload.done({ document: 'deadlift.pdf', chunks: 0 })

  await waitFor(() =>
    expect(
      screen.getByText('“deadlift.pdf” is already in your documents.'),
    ).toBeTruthy(),
  )
})

test('an upload that failed leaves nothing indexing', async () => {
  /* Held open first, so the row is on screen before the request answers: a row that
     never arrived cannot be seen to go, and cleanup on the success path only would
     leave the rail saying `Indexing 1 file…` until a reload. */
  let refuse = () => {}
  const answer = new Promise((_, broken) => {
    refuse = () => broken(new Error('ingest failed'))
  })
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: () => answer }) as unknown as Response),
  )
  render(<Uploading />)

  start()
  await waitFor(() => expect(screen.getByText('deadlift.pdf')).toBeTruthy())

  refuse()

  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
})

test('a row is drawn in the field it was uploaded into, and in no other', async () => {
  const upload = held()
  const { rerender } = render(<Uploading field="fitness" />)

  start()
  await waitFor(() => expect(screen.getByText('deadlift.pdf')).toBeTruthy())

  rerender(<Uploading field="travel" />)
  expect(screen.getByText('nothing indexing')).toBeTruthy()

  rerender(<Uploading field="fitness" />)
  expect(screen.getByText('deadlift.pdf')).toBeTruthy()

  upload.done({ document: 'deadlift.pdf', chunks: 3 })
  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
})

test('an upload that indexed something is named for the region that reads it out', async () => {
  const upload = held()
  render(<Uploading />)

  start()
  upload.done({ document: 'deadlift.pdf', chunks: 12 })

  await waitFor(() =>
    expect(screen.getByText('indexed deadlift.pdf')).toBeTruthy(),
  )
})

test('the same file indexed twice is named again, not held from the first time', async () => {
  /* A live region announces what changes in it. Holding the same sentence across a
     second upload is a region that does not change, and a reader who hears nothing —
     so what is running clears it, and the answer sets it again. */
  const first = held()
  render(<Uploading />)

  start()
  first.done({ document: 'deadlift.pdf', chunks: 12 })
  await waitFor(() => expect(screen.getByText('indexed deadlift.pdf')).toBeTruthy())

  const again = held()
  start()
  await waitFor(() => expect(screen.getByText('nothing indexed')).toBeTruthy())

  again.done({ document: 'deadlift.pdf', chunks: 12 })
  await waitFor(() => expect(screen.getByText('indexed deadlift.pdf')).toBeTruthy())
})

test('bytes the field already had are not announced as indexed', async () => {
  const upload = held()
  render(<Uploading />)

  start()
  upload.done({ document: 'deadlift.pdf', chunks: 0 })

  await waitFor(() =>
    expect(
      screen.getByText('“deadlift.pdf” is already in your documents.'),
    ).toBeTruthy(),
  )
  expect(screen.getByText('nothing indexed')).toBeTruthy()
})

test('an upload that failed announces nothing', async () => {
  let refuse = () => {}
  const answer = new Promise((_, broken) => {
    refuse = () => broken(new Error('ingest failed'))
  })
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: () => answer }) as unknown as Response),
  )
  render(<Uploading />)

  start()
  refuse()

  await waitFor(() => expect(screen.getByText('nothing indexing')).toBeTruthy())
  expect(screen.getByText('nothing indexed')).toBeTruthy()
})

test('what was indexed in another field is not announced over this one', async () => {
  const upload = held()
  const { rerender } = render(<Uploading field="fitness" />)

  start()
  upload.done({ document: 'deadlift.pdf', chunks: 12 })
  await waitFor(() => expect(screen.getByText('indexed deadlift.pdf')).toBeTruthy())

  rerender(<Uploading field="travel" />)

  expect(screen.getByText('nothing indexed')).toBeTruthy()
})
