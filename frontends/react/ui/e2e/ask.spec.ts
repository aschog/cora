import { expect, test } from '@playwright/test'
import { answered, ask, fresh, PROSE, rightRail, SEARCH } from './helpers'

test('a question is answered, and the answer is written as it arrives', async ({ page }) => {
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
  await expect(page.locator('mark').first()).toContainText('Protein builds muscle')
})

test('the steps of the turn are on the trace', async ({ page }) => {
  await fresh(page)

  await ask(page, SEARCH)
  await answered(page)
  await rightRail(page, 'STEPS')

  await expect(page.getByRole('button', { name: /search_documents\(query/ })).toBeVisible()
})
