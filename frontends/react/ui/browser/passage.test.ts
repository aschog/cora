import { expect, test } from 'vitest'
import '../src/styles.css'
import { resolved } from './tokens'

test('the passage an answer quotes is warm, not the colour the page uses for controls', () => {
  const mark = document.createElement('mark')
  mark.className = 'doc-passage'
  document.body.appendChild(mark)

  const drawn = getComputedStyle(mark)
  expect(drawn.backgroundColor).toBe(resolved('--amber-tint'))
  expect(drawn.boxShadow).toContain(resolved('--amber'))
  expect(drawn.backgroundColor).not.toBe(resolved('--accent-tint'))
  expect(drawn.boxShadow).not.toContain(resolved('--accent'))
})
