import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import DocumentRail from './DocumentRail'

afterEach(cleanup)

const rail = (documents: string[], cited: string[], fields: string[] = []) =>
  render(
    <DocumentRail
      documents={documents}
      cited={new Set(cited)}
      fields={fields}
      field={fields[0] ?? 'cora'}
      anyField="cora"
      fixedField={false}
      onField={vi.fn()}
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
      fields={[]}
      field="cora"
      anyField="cora"
      fixedField={false}
      onField={vi.fn()}
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      upload={{ said: '“notes.md” is already in your documents.', wrong: true }}
      onDismissUpload={vi.fn()}
    />,
  )

  expect(
    screen.getByRole('status', { name: 'Last upload' }).textContent,
  ).toContain('already in your documents')
})

test('a rail with fields loaded offers the one an upload goes into', () => {
  rail([], [], ['fitness', 'travel'])

  const picker = screen.getByRole('combobox', {
    name: /upload into/i,
  }) as HTMLSelectElement
  expect(Array.from(picker.options).map((option) => option.value)).toEqual([
    'fitness',
    'travel',
    'cora',
  ])
})

test('a rail with no field loaded offers nothing to choose', () => {
  rail([], [], [])

  expect(screen.queryByRole('combobox', { name: /upload into/i })).toBeNull()
})

test('a pinned conversation shows its field and cannot change it', () => {
  render(
    <DocumentRail
      documents={[]}
      cited={new Set()}
      fields={['fitness', 'travel']}
      field="travel"
      anyField="cora"
      fixedField
      onField={vi.fn()}
      onOpen={vi.fn()}
      onUpload={vi.fn()}
      upload={null}
      onDismissUpload={vi.fn()}
    />,
  )

  expect(screen.queryByRole('combobox', { name: /upload into/i })).toBeNull()
  expect(screen.getByLabelText('Upload into').textContent).toBe('travel')
})
