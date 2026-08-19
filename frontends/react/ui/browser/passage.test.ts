import { expect, test } from 'vitest'
import '../src/styles.css'

/** What the browser resolved a token to, in the form a computed style reports it — so the
 *  test names the token it means rather than the hex behind it. */
const resolved = (token: string) => {
  const probe = document.createElement('div')
  probe.style.color = `var(${token})`
  document.body.appendChild(probe)
  const seen = getComputedStyle(probe).color
  probe.remove()
  return seen
}

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
