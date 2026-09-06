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
