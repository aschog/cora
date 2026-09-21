import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { fresh } from './helpers'

/* A reading kept as one of a field's own files rather than as a document: the page, the
 * routes, the directory and the listing, driven through a real browser against a real
 * server. What the drill then does with such a file is the Python tier's — this is the
 * half a browser is needed for.
 *
 * Tesseract is stood in for as it is next door: recognition is Tesseract's, and what is
 * under test is everything the page does with a reading.
 */

const PICKER = 'Upload from computer'
const DIALOG = 'READ FROM THE IMAGE'
const AS_FILE = "One of this field's own files"
const LIST = 'Grundwortschatz.md'
const FIRST = '| Deutsch | English |\n| --- | --- |\n| Apfel | apple |'
const SECOND = '| Buch | book |'

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

test('a reading is kept as a named file, and a second one is added to it', async ({
  page,
}) => {
  await stand(page, FIRST)
  await fresh(page)

  // The ＋ says what it takes before the picker opens.
  await page.getByRole('button', { name: 'Add a file or photo' }).click()
  await expect(page.getByRole('menuitem', { name: /Add photos & files/ })).toBeVisible()
  await page.keyboard.press('Escape')

  await page.getByLabel(PICKER).setInputFiles(SHOT)
  const asked = page.getByRole('dialog', { name: DIALOG })
  await expect(asked.getByRole('textbox', { name: 'What was read' })).toHaveValue(FIRST)

  // A document is what it would be by default, so keeping a file is a choice made.
  await expect(asked.getByRole('button', { name: 'Keep it' })).toBeEnabled()
  await asked.getByRole('radio', { name: AS_FILE }).check()
  await expect(asked.getByRole('button', { name: 'Keep it' })).toBeDisabled()

  // A combobox rather than a textbox: the name box carries the datalist of what the
  // field already holds, which is what the role follows.
  await asked.getByLabel('What to call it').fill(LIST)
  await asked.getByRole('button', { name: 'Keep it' }).click()
  await expect(page.getByRole('dialog', { name: DIALOG })).toHaveCount(0)

  const held = await page.request.get('/api/scopes/cora/files')
  expect((await held.json()).names).toContain(LIST)
  const kept = await page.request.get(`/api/scopes/cora/files/${LIST}`)
  expect((await kept.json()).text.trim()).toBe(FIRST)

  // A second photograph of the same list: naming it opens what is there above the new
  // reading, and what is kept is the whole box.
  await stand(page, SECOND)
  await page.reload()
  await page.getByLabel(PICKER).setInputFiles(SHOT)
  const again = page.getByRole('dialog', { name: DIALOG })
  await again.getByRole('radio', { name: AS_FILE }).check()
  const naming = again.getByLabel('What to call it')
  await naming.fill(LIST)
  await naming.press('Enter')

  const box = again.getByRole('textbox', { name: 'What was read' })
  await expect(box).toHaveValue(`${FIRST}\n${SECOND}`)
  await again.getByRole('button', { name: 'Keep it' }).click()

  const merged = await page.request.get(`/api/scopes/cora/files/${LIST}`)
  expect((await merged.json()).text.trim()).toBe(`${FIRST}\n${SECOND}`)

  // A file is not a document: nothing indexed it, and the rail does not list it.
  const documents = await page.request.get('/api/documents?scope=cora')
  expect(await documents.json()).not.toContain(LIST)
  await expect(page.getByRole('button', { name: LIST, exact: true })).toHaveCount(0)

  await page.request.delete(`/api/scopes/cora/files/${LIST}`)
})
