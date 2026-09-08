import { expect, test } from '@playwright/test'
import { answered, ask, fresh, rightRail } from './helpers'

/* The one thing the stub cannot cover: the provider. Run by hand before submission —
   `make e2e-live` — against a real key and a real model, so what is asserted is loose.
   A real model phrases an answer differently every time; what it may not do is fail to
   search, fail to cite, or fail to answer. */

test('a real model searches the documents and cites what it used', async ({ page }) => {
  await fresh(page)

  await ask(page, 'What do my notes say about protein? Search them first.')
  await answered(page)

  await expect(page.getByLabel('Open cited source 1')).toBeVisible()

  await page.getByLabel('Open cited source 1').click()
  await expect(page.getByRole('dialog')).toContainText('rotein')
  await page.keyboard.press('Escape')

  await rightRail(page, 'STEPS')
  await expect(page.getByRole('button', { name: /search_documents\(query/ })).toBeVisible()
})
