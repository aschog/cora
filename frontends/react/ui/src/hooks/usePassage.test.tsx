import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { usePassage } from './usePassage'
import WithStore from '../test/withStore'

const KEPT = 'Sleep matters. The rest of the document follows.'

function Reads({ upload }: { upload: string }) {
  const { text, trouble } = usePassage({ scope: 'cora', upload })
  return <p>{trouble ?? text ?? 'reading'}</p>
}

const asked = () => vi.mocked(globalThis.fetch).mock.calls.map(([path]) => String(path))

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.stubGlobal(
    'fetch',
    vi.fn(
      async () =>
        ({ ok: true, status: 200, json: async () => ({ text: KEPT }) }) as Response,
    ),
  )
})

afterEach(cleanup)

test('two readers of one passage make one request between them', async () => {
  /* The panel and the citation modal can be open on the same upload at once. Two
     requests for one document is work nobody asked for, and two answers that could
     disagree. */
  render(
    <WithStore>
      <Reads upload="u1" />
      <Reads upload="u1" />
    </WithStore>,
  )

  await waitFor(() => expect(screen.getAllByText(KEPT)).toHaveLength(2))
  expect(asked()).toHaveLength(1)
})

test('a passage already read is drawn out of what is held rather than fetched again first', async () => {
  const { rerender } = render(
    <WithStore>
      <Reads upload="u1" />
    </WithStore>,
  )
  await waitFor(() => expect(screen.getByText(KEPT)).toBeTruthy())

  /* Away to another upload and back. */
  rerender(
    <WithStore>
      <Reads upload="u2" />
    </WithStore>,
  )
  await waitFor(() => expect(asked()).toHaveLength(2))
  rerender(
    <WithStore>
      <Reads upload="u1" />
    </WithStore>,
  )

  /* Drawn in the same tick it came back, out of what was held — the reader is not shown
     an empty panel for a document they were just reading. */
  expect(screen.getByText(KEPT)).toBeTruthy()
  expect(screen.queryByText('reading')).toBeNull()

  /* And asked for again behind that, which is the half worth keeping: an upload's text
     never changes, but the document it belongs to can be deleted while the page is open,
     and a panel drawing held text for a file that is gone would say so to nobody. */
  await waitFor(() => expect(asked()).toHaveLength(3))
})

test('each upload is asked for under its own name, so one cannot be drawn as another', async () => {
  render(
    <WithStore>
      <Reads upload="u1" />
      <Reads upload="u2" />
    </WithStore>,
  )

  await waitFor(() => expect(asked()).toHaveLength(2))
  expect(asked()).toEqual([
    '/api/uploads/cora/u1',
    '/api/uploads/cora/u2',
  ])
})
