import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import DocumentRail from './DocumentRail'

afterEach(cleanup)

const rail = (documents: string[], cited: string[], onDelete = vi.fn()) => {
  const drawn = render(
    <DocumentRail
      documents={documents}
      cited={new Set(cited)}
      field="cora"
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      onDelete={onDelete}
      upload={null}
      onDismissUpload={vi.fn()}
    />,
  )
  return { ...drawn, onDelete }
}

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

/* A live region has to be in the DOM before its content changes for a screen reader to
   announce the change. The colour and the `!` mark carry the outcome for a reader who can
   see it; this region is the only channel that carries it for one who cannot. */
test('the rail holds the region an upload’s outcome is announced in before there is one', () => {
  rail(['notes.md'], [])

  expect(screen.getByRole('status', { name: 'Last upload' }).textContent).toBe('')
})

test('what an upload did is announced in that same region', () => {
  render(
    <DocumentRail
      documents={['notes.md']}
      cited={new Set<string>()}
      field="cora"
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      onDelete={vi.fn()}
      upload={{ said: '“notes.md” is already in your documents.', wrong: true }}
      onDismissUpload={vi.fn()}
    />,
  )

  expect(
    screen.getByRole('status', { name: 'Last upload' }).textContent,
  ).toContain('already in your documents')
})


test('each document carries the control the other rails carry, named for it', () => {
  /* One shape across the three rails: a document, a conversation and a fact are each a
     row with a control at the end of it. The name is the document, not the verb — a
     column of identical icons would otherwise say nothing about which is which. */
  const { onDelete } = rail(['notes.md', 'plan.md'], ['notes.md'])

  const control = screen.getByRole('button', { name: 'Delete notes.md' })
  expect(control.querySelector('svg')).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Delete plan.md' })).toBeTruthy()

  fireEvent.click(control)

  expect(onDelete).toHaveBeenCalledWith('notes.md')
})

test('an uncited document can still be deleted, though it cannot be opened', () => {
  /* The row is disabled unless this answer cited it, so the control sits beside that
     button rather than inside it — otherwise the only deletable documents would be the
     ones the last answer happened to quote. */
  const { onDelete } = rail(['notes.md', 'plan.md'], ['notes.md'])

  fireEvent.click(screen.getByRole('button', { name: 'Delete plan.md' }))

  expect(onDelete).toHaveBeenCalledWith('plan.md')
})
