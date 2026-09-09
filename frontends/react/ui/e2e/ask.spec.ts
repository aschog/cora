import { expect, test } from '@playwright/test'
import { answered, ask, contrast, over, fresh, PROSE, resolved, rightRail, SEARCH } from './helpers'

test('a question is answered, and the answer lands on the page', async ({ page }) => {
  await fresh(page)

  await ask(page, PROSE)

  await expect(page.getByText('Ask me about your documents')).toBeVisible()
  await answered(page)
})

test('an answer from a document cites it, and the citation opens the passage', async ({
  page,
}) => {
  await fresh(page)

  await ask(page, SEARCH)
  await answered(page)

  const cite = page.getByLabel('Open cited source 1')
  await expect(cite).toBeVisible()
  await cite.click()

  /* The modal is the passage over the conversation; the panel is the whole document
     with the passage marked in it. Both are the same citation followed back. */
  await expect(page.getByRole('dialog')).toContainText('Protein builds muscle')
  await page.keyboard.press('Escape')
  await rightRail(page, 'SOURCE')
  await expect(page.getByRole('heading', { name: 'note.md' })).toBeVisible()
  const passage = page.locator('mark').first()
  await expect(passage).toContainText('Protein builds muscle')

  /* A real cascade, which is the only place these two are true or false. The passage an
     answer quotes is warm rather than the colour the page uses for its controls — and
     what the reader selects has to read against the page: the tint that shipped once
     managed 1.23 against it, which is a highlight that is there and not visible. */
  const drawn = await passage.evaluate((mark) => {
    const shown = getComputedStyle(mark)
    const picked = getComputedStyle(mark, '::selection')
    return {
      background: shown.backgroundColor,
      selection: picked.backgroundColor,
      selected: picked.color,
    }
  })
  const [amber, accent, page_bg] = await Promise.all([
    resolved(page, '--amber-tint'),
    resolved(page, '--accent-tint'),
    resolved(page, '--bg'),
  ])

  expect(drawn.background).toBe(amber)
  expect(drawn.background).not.toBe(accent)
  /* The selection is a veil, so what the reader sees is it laid over what it covers:
     the quotation where it falls on one, and the page where it does not. Rated as the
     opaque blue it is mixed from, both numbers would describe a colour nobody sees. */
  const veiling_a_quote = over(drawn.selection, drawn.background)
  expect(contrast(over(drawn.selection, page_bg), page_bg)).toBeGreaterThan(1.5)
  expect(contrast(veiling_a_quote, drawn.background)).toBeGreaterThan(1.2)
  expect(contrast(drawn.selected, veiling_a_quote)).toBeGreaterThan(4.5)
})

test('the steps of the turn are on the trace', async ({ page }) => {
  await fresh(page)

  await ask(page, SEARCH)
  await answered(page)
  await rightRail(page, 'STEPS')

  await expect(page.getByRole('button', { name: /search_documents\(query/ })).toBeVisible()
})
