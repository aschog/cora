import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import CitationModal from './CitationModal'
import type { Citation } from '../api'

const KEPT = 'Sleep matters. The rest of the document follows.'

const cited = (upload: string): Citation => ({
  number: 1,
  document: 'notes.md',
  start: 0,
  end: 6,
  upload,
})

beforeEach(() =>
  vi.stubGlobal(
    'fetch',
    vi.fn(
      async () =>
        ({ ok: true, json: async () => ({ text: KEPT }) }) as unknown as Response,
    ),
  ),
)

afterEach(cleanup)

test('the cited passage opens over the conversation, marked', async () => {
  render(<CitationModal citation={cited('u1')} onClose={() => {}} />)

  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(document.querySelector('.doc-passage')?.textContent).toBe('Sleep ')
})

test('a passage whose text was never kept says so rather than opening onto nothing', () => {
  /* `[1]` in the answer is the way a citation is opened. An index written before cora
     kept any text names no upload, and a dialog with a filename and no body tells the
     reader nothing about why. */
  render(<CitationModal citation={cited('')} onClose={() => {}} />)

  expect(screen.getByText(/indexed before cora kept its text/)).toBeTruthy()
})
