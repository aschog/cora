import { expect, test } from 'vitest'
import { answerHtml } from '../src/answer'
import { patch } from '../src/patch'

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
