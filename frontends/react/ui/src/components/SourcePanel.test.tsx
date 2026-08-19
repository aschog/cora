import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import SourcePanel from './SourcePanel'
import type { Citation } from '../api'

const KEPT = 'Sleep matters. The rest of the document follows.'

const cited = (upload: string): Citation => ({
  number: 1,
  document: 'notes.md',
  start: 0,
  end: 6,
  upload,
})

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => ({ text: KEPT }) }) as unknown as Response),
  )
})

afterEach(cleanup)

test('with nothing opened the panel draws nothing', () => {
  const { container } = render(
    <SourcePanel document={null} upload={null} citations={[]} />,
  )

  expect(container.textContent).toBe('')
})

test('a passage whose text was never kept says so rather than drawing an empty page', async () => {
  /* A citation carries the upload its span was measured in, and an index written before
     cora kept any text hands out citations that name none. The reader is told; the
     panel does not sit blank. */
  /* `uploadOf` hands the panel what the citation names — the empty string for such an
     index — and `null` when the conversation cites the document nowhere at all. A
     document that cannot be read is a document that cannot be read. */
  render(<SourcePanel document="notes.md" upload="" citations={[cited('')]} />)

  expect(screen.getByText(/indexed before cora kept its text/)).toBeTruthy()
  cleanup()
  render(<SourcePanel document="notes.md" upload={null} citations={[]} />)

  expect(screen.getByText(/indexed before cora kept its text/)).toBeTruthy()
  expect(screen.queryByText(/The rest of the document follows/)).toBeNull()
})

test('a document with its text kept is shown, counted and marked', async () => {
  render(
    <SourcePanel document="notes.md" upload="u1" citations={[cited('u1')]} />,
  )

  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(screen.getByText('1 cited passage · highlighted')).toBeTruthy()
})
