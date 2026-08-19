import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import DocumentRail from './DocumentRail'

afterEach(cleanup)

const rail = (documents: string[], cited: string[]) =>
  render(
    <DocumentRail
      documents={documents}
      cited={new Set(cited)}
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      upload={null}
      onDismissUpload={vi.fn()}
    />,
  )

/* The state the App-level tests cannot reach: their fixture serves one document, and citing
   it is what makes the rail openable — so a rail holding both a cited and an uncited
   document is only observable here, and it is the only state the deleted note appeared in. */
test('a rail holding a cited and an uncited document draws the list and no prose', () => {
  rail(['notes.md', 'plan.md'], ['notes.md'])

  expect(screen.getByRole('button', { name: 'notes.md' })).toBeTruthy()
  expect(screen.getByRole('button', { name: 'plan.md' })).toBeTruthy()
  expect(screen.queryByText(/Greyed documents are indexed/)).toBeNull()
  expect(screen.queryByText(/ask something they can answer/)).toBeNull()
})

test('an uncited document cannot be opened, and a cited one can', () => {
  rail(['notes.md', 'plan.md'], ['notes.md'])

  expect(screen.getByRole('button', { name: 'notes.md' }).hasAttribute('disabled')).toBe(
    false,
  )
  expect(screen.getByRole('button', { name: 'plan.md' }).hasAttribute('disabled')).toBe(
    true,
  )
})

test('a rail with nothing indexed draws the upload control alone', () => {
  const { container } = rail([], [])

  expect(screen.getByText('Add a document')).toBeTruthy()
  expect(screen.queryByText(/Nothing indexed yet/)).toBeNull()
  expect(container.querySelectorAll('.doc-row')).toHaveLength(0)
})
