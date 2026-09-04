import { expect, test } from 'vitest'
import { answerHtml } from '../src/answer'
import { patch } from '../src/patch'
import '../src/styles.css'
import { contrast, resolved } from './tokens'

test('a phrase selected in the paragraph being written survives the next piece', () => {
  const kept = document.createElement('div')
  document.body.appendChild(kept)
  let written = 'Sleep is the lever. Not volume'
  patch(kept, answerHtml(written, []))

  const words = kept.querySelector('p')!.firstChild as Text
  const range = document.createRange()
  range.setStart(words, words.data.indexOf('Not volume'))
  range.setEnd(words, words.data.length)
  const selection = window.getSelection()!
  selection.removeAllRanges()
  selection.addRange(range)
  expect(selection.toString()).toBe('Not volume')

  written += ' and not intensity.'
  patch(kept, answerHtml(written, []))

  expect(selection.toString()).toBe('Not volume')
})

// The ratio the panel tint managed against the page was 1.23, which is why the highlight was
// there and not visible. The floor is set by that, not by taste.
test('text selected on the page is drawn so the highlight reads against it', () => {
  const words = document.createElement('p')
  words.textContent = 'Sleep is the lever.'
  document.body.appendChild(words)

  const drawn = getComputedStyle(words, '::selection')
  expect(drawn.backgroundColor).not.toBe(resolved('--accent-tint'))
  expect(contrast(drawn.backgroundColor, resolved('--bg'))).toBeGreaterThan(1.5)
  expect(contrast(drawn.color, drawn.backgroundColor)).toBeGreaterThan(4.5)
})
