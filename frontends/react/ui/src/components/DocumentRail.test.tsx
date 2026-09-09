import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import DocumentRail from './DocumentRail'

afterEach(cleanup)

const rail = (documents: string[], cited: string[], onDelete = vi.fn()) => {
  const drawn = render(
    <DocumentRail
      documents={documents}
      cited={new Set(cited)}
      field="cora"
      indexing={[]}
      indexed={null}
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

/* A live region has to be in the DOM before its content changes for a screen reader to
   announce the change. The colour and the `!` mark carry the outcome for a reader who can
   see it; this region is the only channel that carries it for one who cannot. */
test('what an upload did is announced in that same region', () => {
  render(
    <DocumentRail
      documents={['notes.md']}
      cited={new Set<string>()}
      field="cora"
      indexing={[]}
      indexed={null}
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


/* An upload takes seconds, and until it is over the file is in neither place the reader
   looks: the list has nothing under that name yet, and no sentence is coming for the one
   outcome that needs none. The row is what says the wait is cora's rather than theirs. */
test('a file being indexed is listed as indexing, and the control says how many', () => {
  render(
    <DocumentRail
      documents={['notes.md']}
      cited={new Set<string>()}
      field="cora"
      indexing={['deadlift-form-guide.pdf']}
      indexed={null}
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      onDelete={vi.fn()}
      upload={null}
      onDismissUpload={vi.fn()}
    />,
  )

  expect(screen.getByText('Indexing 1 file…')).toBeTruthy()
  const indexing = screen.getByRole('status', { name: 'Indexing' })
  expect(indexing.textContent).toContain('deadlift-form-guide.pdf')
  expect(indexing.textContent).toContain('INDEXING')
  /* Nothing to open and nothing to delete: it is not a document of the field yet. */
  expect(screen.queryByRole('button', { name: 'deadlift-form-guide.pdf' })).toBeNull()
  expect(screen.queryByLabelText('Delete deadlift-form-guide.pdf')).toBeNull()
})

test('two files at once are counted, and one at a time is not pluralised', () => {
  render(
    <DocumentRail
      documents={[]}
      cited={new Set<string>()}
      field="cora"
      indexing={['one.md', 'two.md']}
      indexed={null}
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      onDelete={vi.fn()}
      upload={null}
      onDismissUpload={vi.fn()}
    />,
  )

  expect(screen.getByText('Indexing 2 files…')).toBeTruthy()
})

/* The label wraps the file input, so the label's text is the input's accessible name.
   The count belongs to the list below it, not to the control. */
test('the control still says what it does while a file is indexing', () => {
  render(
    <DocumentRail
      documents={[]}
      cited={new Set<string>()}
      field="cora"
      indexing={['deadlift-form-guide.pdf']}
      indexed={null}
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      onDelete={vi.fn()}
      upload={null}
      onDismissUpload={vi.fn()}
    />,
  )

  expect(screen.getByLabelText('Add a document')).toBeTruthy()
})

/* The list says an upload arrived to anyone who can see it. A reader who cannot is
   owed the same news, and a row leaving a live region is not announced. */
test('a document just indexed is said where a screen reader hears it', () => {
  render(
    <DocumentRail
      documents={['deadlift-form-guide.pdf']}
      cited={new Set<string>()}
      field="cora"
      indexing={[]}
      indexed="deadlift-form-guide.pdf"
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      onDelete={vi.fn()}
      upload={null}
      onDismissUpload={vi.fn()}
    />,
  )

  const said = screen.getByRole('status', { name: 'Last upload' })
  expect(said.textContent).toContain('deadlift-form-guide.pdf')
  expect(said.textContent).toContain('indexed')
})
