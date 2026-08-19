import { render } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'
import { cleanup } from '@testing-library/react'
import DocumentBody from './DocumentBody'

afterEach(cleanup)

const TEXT = 'ABCDEFGHIJ'

const shown = (spans: { start: number; end: number }[]) =>
  render(<DocumentBody text={TEXT} spans={spans} />).container

test('the document is rendered exactly once, whatever the passages do', () => {
  /* Chunks overlap by design — `DEFAULT_OVERLAP` — so two adjacent cited chunks share
     their edges. Slicing each span independently emits the shared characters twice and
     a nested one out of order: the reader is shown a corrupted copy of their own
     document, in the panel that exists to be checked against. */
  expect(shown([{ start: 0, end: 6 }, { start: 4, end: 9 }]).textContent).toBe(TEXT)
  expect(shown([{ start: 0, end: 8 }, { start: 2, end: 4 }]).textContent).toBe(TEXT)
  expect(shown([{ start: 4, end: 9 }, { start: 0, end: 6 }]).textContent).toBe(TEXT)
})

test('passages arrive in citation order, not in document order', () => {
  /* Citations are numbered as the model used them, so `[1]` can sit later in the file
     than `[2]`. Merging without ordering first drops every passage that precedes the
     one it happens to see first — the panel then counts two and marks one. */
  const marks = shown([{ start: 6, end: 8 }, { start: 0, end: 2 }]).querySelectorAll(
    '.doc-passage',
  )

  expect([...marks].map((mark) => mark.textContent)).toEqual(['AB', 'GH'])
})

test('overlapping passages read as the one passage they cover', () => {
  const marks = shown([{ start: 0, end: 6 }, { start: 4, end: 9 }]).querySelectorAll(
    '.doc-passage',
  )

  expect(marks).toHaveLength(1)
  expect(marks[0].textContent).toBe('ABCDEFGHI')
})

test('passages that do not touch stay two passages', () => {
  const marks = shown([{ start: 0, end: 2 }, { start: 6, end: 8 }]).querySelectorAll(
    '.doc-passage',
  )

  expect([...marks].map((mark) => mark.textContent)).toEqual(['AB', 'GH'])
})

test('a passage running past the end marks to the end rather than throwing', () => {
  const container = shown([{ start: 8, end: 99 }])

  expect(container.textContent).toBe(TEXT)
  expect(container.querySelector('.doc-passage')?.textContent).toBe('IJ')
})

test('a document with nothing cited in it is still the document', () => {
  const container = shown([])

  expect(container.textContent).toBe(TEXT)
  expect(container.querySelector('.doc-passage')).toBeNull()
})
