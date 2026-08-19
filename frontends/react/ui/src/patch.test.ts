import { expect, test } from 'vitest'
import { answerHtml } from './answer'
import { patch } from './patch'

const block = (html = '') => {
  const kept = document.createElement('div')
  kept.innerHTML = html
  return kept
}

test('an empty block takes the whole of the HTML it is given', () => {
  const kept = block()

  patch(kept, '<p>Sleep is the lever.</p>')

  expect(kept.innerHTML).toBe('<p>Sleep is the lever.</p>')
})

test('text that grew is the same text node, carrying the longer text', () => {
  const kept = block('<p>Sleep</p>')
  const words = kept.firstElementChild!.firstChild

  patch(kept, '<p>Sleep is the lever.</p>')

  expect(kept.firstElementChild!.firstChild).toBe(words)
  expect(words!.nodeValue).toBe('Sleep is the lever.')
})

test('the block the reader has read is untouched by the one that follows it', () => {
  const kept = block('<p>Sleep is the lever.</p>')
  const read = kept.firstElementChild!
  const words = read.firstChild

  patch(kept, '<p>Sleep is the lever.</p><p>Not volume.</p>')

  expect(kept.firstElementChild).toBe(read)
  expect(read.firstChild).toBe(words)
  expect(kept.innerHTML).toBe('<p>Sleep is the lever.</p><p>Not volume.</p>')
})

test('a paragraph that turns out to be a list is replaced, because the tag is the node', () => {
  const kept = block('<p>1. Sleep</p>')

  patch(kept, '<ol><li>Sleep</li></ol>')

  expect(kept.innerHTML).toBe('<ol><li>Sleep</li></ol>')
})

test('an attribute that appeared is set and one that went is removed', () => {
  const kept = block('<p><button class="cite" data-cite="1">1</button></p>')
  const cite = kept.querySelector('button')!

  patch(kept, '<p><button class="cite" aria-label="Open cited source 2">2</button></p>')

  expect(kept.querySelector('button')).toBe(cite)
  expect(cite.getAttribute('aria-label')).toBe('Open cited source 2')
  expect(cite.hasAttribute('data-cite')).toBe(false)
})

test('blocks the new HTML no longer has are removed', () => {
  const kept = block('<p>Let me check the log.</p><p>Reading…</p>')

  patch(kept, '<p>Sleep is the lever.</p>')

  expect(kept.innerHTML).toBe('<p>Sleep is the lever.</p>')
})

test('an answer arriving in pieces ends as one parse of the whole would have drawn it', () => {
  const citations = [{ number: 1, document: 'notes.md', start: 0, end: 5, upload: 'u1' }]
  const pieces = ['Sleep is ', 'the lever.\n\n- Not volume\n', '- Not intensity [1]\n']
  const kept = block()

  let written = ''
  for (const piece of pieces) {
    written += piece
    patch(kept, answerHtml(written, citations))
  }

  expect(kept.innerHTML).toBe(answerHtml(written, citations))
})

test('a node that is not an element is its text, so nothing goes looking for attributes', () => {
  const kept = block('<p>Sleep</p><!-- 1 -->')

  patch(kept, '<p>Sleep</p><!-- 2 -->')

  expect(kept.innerHTML).toBe('<p>Sleep</p><!-- 2 -->')
})
