import { cleanup, render as draw, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import SourcePanel from './SourcePanel'
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

const kept = (upload: string) => ({ scope: 'cora', upload })

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => ({ text: KEPT }) }) as unknown as Response),
  )
})

afterEach(cleanup)

test('with nothing opened the panel draws nothing', () => {
  const { container } = render(
    <SourcePanel document={null} source={null} citations={[]} />,
  )

  expect(container.textContent).toBe('')
})

test('a passage whose text was never kept says so rather than drawing an empty page', async () => {
  /* `sourceOf` hands the panel a field and an upload, and `null` where the conversation
     names neither — a citation from an index written before cora kept any text, or a
     document it cites nowhere at all. A document that cannot be read is a document that
     cannot be read: the reader is told, and the panel does not sit blank. */
  render(<SourcePanel document="notes.md" source={null} citations={[cited('')]} />)

  expect(screen.getByText(UNKEPT)).toBeTruthy()
  expect(screen.queryByText(/The rest of the document follows/)).toBeNull()
})

test('a document with its text kept is shown under its name, and marked', async () => {
  const { container } = render(
    <SourcePanel document="notes.md" source={kept('u1')} citations={[cited('u1')]} />,
  )

  expect(await screen.findByText(/The rest of the document follows/)).toBeTruthy()
  expect(screen.getByRole('heading', { name: 'notes.md' })).toBeTruthy()
  expect(container.querySelector(`.${bodyCss.docPassage}`)?.textContent).toBe('Sleep ')
  expect(screen.queryByText('not cited in this answer')).toBeNull()
})

test('a document this answer did not rest on still says so', () => {
  render(<SourcePanel document="notes.md" source={kept('u1')} citations={[]} />)

  expect(screen.getByText('not cited in this answer')).toBeTruthy()
})
