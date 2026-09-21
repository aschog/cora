import { expect, test } from '@playwright/test'
import { existsSync, readFileSync, rmSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
/* Where an approved effect writes. Read from the suite rather than from the page: what
   the gate is for is the file, and the page can only say that it was told about one. */
const WROTE = resolve(HERE, '../../../../.cora/e2e/out/note.md')
import { WRITE, answered, ask, fresh, pin, settled, waiting } from './helpers'

/* The tool that acts belongs to the `kit` field, so the conversation is pinned there
   before it is asked for — the gate is what this covers, not the routing. */
const inKit = (page: import('@playwright/test').Page) => pin(page, 'kit')

test.beforeEach(() => rmSync(WROTE, { force: true }))

test('a turn that would change something outside cora stops for the reader', async ({
  page,
}) => {
  await fresh(page)
  await inKit(page)

  await ask(page, WRITE)

  const card = waiting(page)
  await expect(card).toContainText('Write one note to a file.')
  await expect(card).toContainText('write_note')
  await expect(card.getByRole('button', { name: 'Approve' })).toBeVisible()
  await expect(card.getByRole('button', { name: 'Decline' })).toBeVisible()
})

test('approving runs it, and the turn answers', async ({ page }) => {
  await fresh(page)
  await inKit(page)
  await ask(page, WRITE)
  await expect(waiting(page)).toBeVisible()

  await waiting(page).getByRole('button', { name: 'Approve' }).click()

  await expect(settled(page)).toContainText('You approved it.')
  await expect(page.getByText('it is written')).toBeVisible()
  await answered(page)
  expect(readFileSync(WROTE, 'utf8')).toContain('what the turn worked out')
})

test('declining changes nothing outside cora, and the turn still answers', async ({
  page,
}) => {
  await fresh(page)
  await inKit(page)
  await ask(page, WRITE)
  await expect(waiting(page)).toBeVisible()

  await waiting(page).getByRole('button', { name: 'Decline' }).click()

  await expect(settled(page)).toContainText('Nothing outside cora was changed.')
  await answered(page)
  expect(existsSync(WROTE)).toBe(false)
})
