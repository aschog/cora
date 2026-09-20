import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { confirm, fresh } from './helpers'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))

const NOTE = resolve(HERE, '../../../../tests/e2e/documents/second.md')

/* Two controls add a document now — the rail's, over the list it changes, and the
   composer's, beside the question being typed. Each spec says which one it used. */
const RAIL = 'Add a document'
const BESIDE = 'Add a file or photo'

test('a document is uploaded, listed, and deleted only once i have said so', async ({
  page,
}) => {
  await fresh(page)

  await page.getByLabel(RAIL).setInputFiles(NOTE)

  /* Indexing is seconds of real work — the embeddings are written before the request
     answers — so the row stands under the control while it runs, and goes when the
     document arrives in the list. The list is what says it worked; the page says
     nothing else about an upload that did. */
  await expect(page.getByRole('status', { name: 'Indexing' })).toContainText('second.md')
  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toBeVisible()
  await expect(page.getByRole('status', { name: 'Indexing' })).toHaveText('')
  /* Read out, not drawn: the list says it to anyone who can see the list, and this is
     the same news for a reader who cannot. */
  await expect(page.getByRole('status', { name: 'Last upload' })).toContainText(
    'second.md',
  )

  await page.getByLabel('Delete second.md').click()
  const asked = page.getByRole('dialog', { name: 'DELETE DOCUMENT' })
  await expect(asked).toContainText('second.md')
  await asked.getByRole('button', { name: 'Keep it' }).click()
  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toBeVisible()

  await page.getByLabel('Delete second.md').click()
  await confirm(page, 'DELETE DOCUMENT', 'Delete document')

  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toHaveCount(0)
})

test('a file added beside the question is a document of the same field', async ({
  page,
}) => {
  await fresh(page)

  await page.getByLabel(BESIDE).setInputFiles(NOTE)

  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toBeVisible()
  await expect(page.getByRole('status', { name: 'Last upload' })).toContainText(
    'second.md',
  )

  await page.getByLabel('Delete second.md').click()
  await confirm(page, 'DELETE DOCUMENT', 'Delete document')
  await expect(page.getByRole('button', { name: 'second.md', exact: true })).toHaveCount(0)
})

test('a file cora refuses is refused the same way from either control', async ({
  page,
}) => {
  await fresh(page)

  /* The refusal is cora's, and where the reader is told is the rail's own notice: the
     control beside the question adds through the path the rail's control uses. */
  await page.route('**/api/documents', (asked) =>
    asked.request().method() === 'POST'
      ? asked.fulfill({
          status: 400,
          json: { error: 'That upload is not one cora reads.' },
        })
      : asked.continue(),
  )

  await page.getByLabel(BESIDE).setInputFiles(NOTE)

  await expect(page.getByText('That upload is not one cora reads.')).toBeVisible()
  await expect(page.getByLabel(BESIDE)).toBeEnabled()
})

/* The smallest thing a browser takes as an image: one transparent pixel. Nothing reads
   words out of it, and nothing here asks the real reader to try — recognition is
   Tesseract's rather than cora's, so it is stood in for, and what is under test is
   everything the page does with a reading. */
const SHOT = {
  name: 'words.png',
  mimeType: 'image/png',
  buffer: Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk' +
      'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
    'base64',
  ),
}

const stand = (page: Page, text: string) =>
  page.addInitScript((said) => {
    ;(window as unknown as { Tesseract: unknown }).Tesseract = {
      createWorker: async () => ({
        recognize: async () => ({ data: { text: said } }),
        terminate: async () => undefined,
      }),
    }
  }, text)

test('a photo added beside the question is read, corrected and kept', async ({ page }) => {
  await stand(page, 'Hilfe  heIp')
  await fresh(page)

  await page.getByLabel(BESIDE).setInputFiles(SHOT)

  const asked = page.getByRole('dialog', { name: 'READ FROM THE IMAGE' })
  await expect(asked).toContainText('words.png')
  const read = asked.getByRole('textbox', { name: 'What was read' })
  await expect(read).toHaveValue('Hilfe  heIp')

  await read.fill('Hilfe  help')
  await asked.getByRole('button', { name: 'Keep it' }).click()

  await expect(page.getByRole('button', { name: 'words.md', exact: true })).toBeVisible()
  const held = await page.request.get('/api/documents/cora/words.md')
  const [upload] = await held.json()
  expect(upload.text).toBe('Hilfe  help')

  /* The store is the run's, and the spec below asks whether a discarded reading left
     a document of this name behind. */
  await page.getByLabel('Delete words.md').click()
  await confirm(page, 'DELETE DOCUMENT', 'Delete document')
  await expect(page.getByRole('button', { name: 'words.md', exact: true })).toHaveCount(0)
})

test('a photo whose reading is discarded leaves the field as it was', async ({ page }) => {
  await stand(page, 'Haus  house')
  await fresh(page)

  await page.getByLabel(BESIDE).setInputFiles(SHOT)
  await page
    .getByRole('dialog', { name: 'READ FROM THE IMAGE' })
    .getByRole('button', { name: 'Discard' })
    .click()

  await expect(page.getByRole('dialog', { name: 'READ FROM THE IMAGE' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'words.md', exact: true })).toHaveCount(0)
})

test('a photo with no words in it says so rather than offering a document', async ({
  page,
}) => {
  await stand(page, '')
  await fresh(page)

  await page.getByLabel(BESIDE).setInputFiles(SHOT)

  const asked = page.getByRole('dialog', { name: 'READ FROM THE IMAGE' })
  await expect(asked).toContainText('Nothing was read')
  await expect(asked.getByRole('button', { name: 'Keep it' })).toBeDisabled()
})

test('while a photo is being read the control says so and takes no second one', async ({
  page,
}) => {
  /* A reading that takes its time, so the state between picking a photo and seeing
     what it said is a state a spec can stand in. */
  await page.addInitScript(() => {
    ;(window as unknown as { Tesseract: unknown }).Tesseract = {
      createWorker: async () => ({
        recognize: () =>
          new Promise((said) =>
            setTimeout(() => said({ data: { text: 'Hilfe — help' } }), 1500),
          ),
        terminate: async () => undefined,
      }),
    }
  })
  await fresh(page)

  await page.getByLabel(BESIDE).setInputFiles(SHOT)

  await expect(page.getByLabel('Adding a file…')).toBeDisabled()

  const asked = page.getByRole('dialog', { name: 'READ FROM THE IMAGE' })
  await expect(asked).toBeVisible()
  /* And still no second photo while its reading is on screen to be corrected. */
  await expect(page.getByLabel('Adding a file…')).toBeDisabled()

  await asked.getByRole('button', { name: 'Discard' }).click()
  await expect(page.getByLabel(BESIDE)).toBeEnabled()
})
