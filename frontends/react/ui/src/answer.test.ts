import { expect, test } from 'vitest'
import { answerHtml } from './answer'
import type { Citation } from './api'

const cite = (number: number): Citation => ({
  number,
  document: 'notes.md',
  start: 0,
  end: 4,
  upload: 'u1',
  scope: 'cora',
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
  /* `rows[1]` would be left alone by the citation rule anyway — the bracket continues a
     word — so what this has to show is a run the rule *would* take: one standing on its
     own inside a fence, and inline code that is nothing else. */
  const fenced = answerHtml('Sample:\n\n```\n[1] the first entry\n```', [cite(1)])
  const inline = answerHtml('Write `[1]` to mean the first.', [cite(1)])

  expect(fenced).not.toContain('data-cite')
  expect(fenced).toContain('[1] the first entry')
  expect(inline).not.toContain('data-cite')
})

test('a citation outside code is still a button when code is nearby', () => {
  const html = answerHtml('As [1] says:\n\n```\n[1] not this one\n```', [cite(1)])

  expect(html.match(/data-cite=/g)).toHaveLength(1)
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

test('a link in an answer opens away from the page and carries nothing back', () => {
  const html = answerHtml('See [the log](https://elsewhere.test/x).', [])

  expect(html).toContain('target="_blank"')
  expect(html).toContain('rel="noopener noreferrer"')
})
