import { expect, test } from '@playwright/test'
import { answered, ask, confirm, fresh, named, REMEMBER, rightRail } from './helpers'

/* Named for this spec alone: the sessions rail lists every conversation the run has
   had, and two rows under one name are two rows the delete control cannot tell apart. */
const LEFT = 'a conversation to leave behind'

test('a conversation is deleted from the list only once i have said so', async ({
  page,
}) => {
  await fresh(page)
  await ask(page, LEFT)
  await answered(page)
  await named(page)

  /* The conversation being read offers no delete, so the one to delete is the one left
     behind by starting another. */
  await page.getByRole('button', { name: /new session/i }).click()
  await rightRail(page, 'SESSIONS')
  const row = page.getByLabel(`Delete ${LEFT}`)
  await expect(row).toBeVisible()

  await row.click()
  await confirm(page, 'DELETE SESSION', 'Delete session')

  await expect(page.getByLabel(`Delete ${LEFT}`)).toHaveCount(0)
})

test('a fact is forgotten only once i have said so', async ({ page }) => {
  await fresh(page)
  await ask(page, REMEMBER)
  await answered(page)
  await rightRail(page, 'MEMORY')

  const fact = 'The user trains on Tuesdays.'
  await expect(page.getByText(fact)).toBeVisible()

  await page.getByLabel(`Delete ${fact}`).click()
  await confirm(page, 'FORGET THIS', 'Forget it')

  await expect(page.getByText(fact)).toHaveCount(0)
})
