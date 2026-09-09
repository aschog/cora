import { expect, test } from '@playwright/test'
import { confirm, fresh } from './helpers'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))

const NOTE = resolve(HERE, '../../../../tests/e2e/documents/second.md')

test('a document is uploaded, listed, and deleted only once i have said so', async ({
  page,
}) => {
  await fresh(page)

  await page.locator('input[type=file]').setInputFiles(NOTE)

  /* The list is what says the upload worked — the page says nothing else about one that
     did, and the row it was indexing under goes when the document arrives. */
  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toBeVisible()
  await expect(page.getByRole('status', { name: 'Indexing' })).toHaveText('')

  await page.getByLabel('Delete second.md').click()
  const asked = page.getByRole('dialog', { name: 'DELETE DOCUMENT' })
  await expect(asked).toContainText('second.md')
  await asked.getByRole('button', { name: 'Keep it' }).click()
  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toBeVisible()

  await page.getByLabel('Delete second.md').click()
  await confirm(page, 'DELETE DOCUMENT', 'Delete document')

  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toHaveCount(0)
})
