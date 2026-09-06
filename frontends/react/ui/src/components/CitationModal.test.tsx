import { cleanup, render as draw, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import CitationModal from './CitationModal'
import type { Citation } from '../api'
import { UNKEPT } from '../hooks/usePassage'
import WithStore from '../test/withStore'
import bodyCss from '../components/DocumentBody.module.css'

/** Every render here goes through the store the passage read is held in — the component
 *  under test asks for it the same way the page does. */
const render = (ui: ReactElement) => draw(<WithStore>{ui}</WithStore>)

const KEPT = 'Sleep matters. The rest of the document follows.'

const cited = (upload: string): Citation => ({
  number: 1,
  document: 'notes.md',
  start: 0,
  end: 6,
  upload,
  scope: 'cora',
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
  expect(document.querySelector(`.${bodyCss.docPassage}`)?.textContent).toBe('Sleep ')
})

test('a passage whose text was never kept says so rather than opening onto nothing', () => {
  /* `[1]` in the answer is the way a citation is opened. An index written before cora
     kept any text names no upload, and a dialog with a filename and no body tells the
     reader nothing about why. */
  render(<CitationModal citation={cited('')} onClose={() => {}} />)

  expect(screen.getByText(UNKEPT)).toBeTruthy()
})

test('a citation that names no field says so rather than asking for a broken address', () => {
  /* A conversation recorded before a passage carried its field restores citations with
     none. Asking for one would miss the route entirely and leave the reader a bare 404
     where a sentence was written for them. */
  render(
    <CitationModal citation={{ ...cited('u1'), scope: '' }} onClose={vi.fn()} />,
  )

  expect(screen.getByText(UNKEPT)).toBeTruthy()
})
