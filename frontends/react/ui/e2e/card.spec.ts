import { expect, test } from '@playwright/test'
import { answered, ask, CHOOSE, fresh, settled, waiting } from './helpers'

test('a turn that stops to ask draws the question and every way out of it', async ({
  page,
}) => {
  await fresh(page)

  await ask(page, CHOOSE)

  const card = waiting(page)
  await expect(card).toContainText('Which weight did you mean?')
  await expect(card.getByRole('button', { name: '75 kg' })).toBeVisible()
  await expect(card.getByRole('button', { name: '77 kg' })).toBeVisible()
  await expect(card.getByRole('button', { name: 'Neither, thanks.' })).toBeVisible()
  /* Nothing can be sent while a card waits: the turn is not over, and a second
     question would be asked of a thread that is still answering the first. */
  await expect(page.getByRole('button', { name: 'Ask', exact: true })).toBeDisabled()
  await expect(page.getByText('cora is waiting on your answer above.')).toBeVisible()
})

test('picking an option finishes the turn, and the card says what was chosen', async ({
  page,
}) => {
  await fresh(page)
  await ask(page, CHOOSE)
  await expect(waiting(page)).toBeVisible()

  await waiting(page).getByRole('button', { name: '75 kg' }).click()

  await expect(settled(page)).toContainText('You chose 75 kg.')
  await answered(page)
})

test('a card left open comes back when the page does', async ({ page }) => {
  await fresh(page)
  await ask(page, CHOOSE)
  await expect(waiting(page)).toBeVisible()

  await page.reload()

  await expect(waiting(page)).toContainText('Which weight did you mean?')
})
