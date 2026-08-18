import { expect, test } from 'vitest'
import { answerHtml } from './answer'
import type { Citation } from './api'

const cite = (number: number): Citation => ({
  number,
  document: 'notes.md',
  start: 0,
  end: 4,
  upload: 'u1',
})

test('markdown is markdown: a list stays a list and bold stays bold', () => {
  const html = answerHtml('Do this:\n\n- one\n- two\n\n**Then** rest.', [])

  expect(html).toContain('<ul>')
  expect(html).toContain('<li>one</li>')
  expect(html).toContain('<strong>Then</strong>')
})

test('a citation becomes a button the reader can click', () => {
  const html = answerHtml('Sleep, not volume [1].', [cite(1)])

  expect(html).toContain('data-cite="1"')
  expect(html).toContain('aria-label="Open cited source 1"')
})

test('every number in a run becomes its own button', () => {
  const html = answerHtml('Both [1][2] say so.', [cite(1), cite(2)])

  expect(html.match(/data-cite=/g)).toHaveLength(2)
})

test('a number citing nothing stays the text it was written as', () => {
  const html = answerHtml('Section [9] of the plan.', [cite(1)])

  expect(html).not.toContain('data-cite')
  expect(html).toContain('[9]')
})

test('a bracketed number inside code is left alone', () => {
  const html = answerHtml('Read `rows[1]` and:\n\n```\nrows[1]\n```', [cite(1)])

  expect(html).not.toContain('data-cite')
})

test('a document cannot smuggle markup into the page', () => {
  const html = answerHtml('<script>alert(1)</script> and <b>raw</b>', [])

  expect(html).not.toContain('<script>')
  expect(html).not.toContain('<b>raw</b>')
})

test('an answer fetches nothing: an image is text, not a request', () => {
  const html = answerHtml('![tracker](https://example.test/pixel.png)', [])

  expect(html).not.toContain('<img')
})

test('a bracketed number inside an attribute is not a citation', () => {
  /* Substitution runs over the text between tags, never over what is inside one. */
  const html = answerHtml('[A link [1]](https://example.test/a)', [cite(1)])

  expect(html.match(/data-cite=/g)).toHaveLength(1)
  expect(html).toContain('href="https://example.test/a"')
})
