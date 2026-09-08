import { render } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'
import { cleanup } from '@testing-library/react'
import DocumentBody from './DocumentBody'
import bodyCss from '../components/DocumentBody.module.css'

afterEach(cleanup)

const TEXT = 'ABCDEFGHIJ'

const shown = (spans: { start: number; end: number }[]) =>
  render(<DocumentBody text={TEXT} spans={spans} />).container

test('passages arrive in citation order, not in document order', () => {
  /* Citations are numbered as the model used them, so `[1]` can sit later in the file
     than `[2]`. Merging without ordering first drops every passage that precedes the
     one it happens to see first — the panel then counts two and marks one. */
  const marks = shown([{ start: 6, end: 8 }, { start: 0, end: 2 }]).querySelectorAll(
    `.${bodyCss.docPassage}`,
  )

  expect([...marks].map((mark) => mark.textContent)).toEqual(['AB', 'GH'])
})

test('overlapping passages read as the one passage they cover', () => {
  const marks = shown([{ start: 0, end: 6 }, { start: 4, end: 9 }]).querySelectorAll(
    `.${bodyCss.docPassage}`,
  )

  expect(marks).toHaveLength(1)
  expect(marks[0].textContent).toBe('ABCDEFGHI')
})

test('a passage running past the end marks to the end rather than throwing', () => {
  const container = shown([{ start: 8, end: 99 }])

  expect(container.textContent).toBe(TEXT)
  expect(container.querySelector(`.${bodyCss.docPassage}`)?.textContent).toBe('IJ')
})

