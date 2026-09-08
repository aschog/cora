import { cleanup, render as draw, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import CitationModal from './CitationModal'
import type { Citation } from '../api'
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

