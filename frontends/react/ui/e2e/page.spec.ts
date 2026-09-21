import { expect, test } from '@playwright/test'
import { answered, ask, fixed, fresh, pin, PROSE } from './helpers'

/* The one tier that proves a plugin's page is really served and really drawn: the page,
   the API and the plugins folder are all the real ones, and the frame is a document the
   browser fetched from cora rather than a element the shell drew. */
test('a field with a page is worked in it, and answers beside it', async ({
  page,
}) => {
  const shown = await fixed(page, 'atlas')
  await expect(shown.contentFrame().locator('#here')).toHaveText(
    'The atlas is open.',
  )

  /* The conversation is beside it, in the rail, and it is the whole conversation: a
     question goes in and the answer lands where it was asked. */
  const rail = page
    .getByRole('complementary')
    .filter({ has: page.getByRole('tablist') })
  await expect(rail.getByRole('heading', { name: /New conversation/ })).toBeVisible()

  await ask(page, PROSE)
  await answered(page)

  /* Named by the question that opened it, and holding that turn. */
  await expect(rail.getByRole('heading', { name: PROSE })).toBeVisible()
  await expect(rail.getByText(PROSE).first()).toBeVisible()
  await expect(shown).toBeVisible()
})

test('a field with no page leaves the conversation in the middle', async ({
  page,
}) => {
  await fresh(page)
  await pin(page, 'kit')

  await expect(page.locator('iframe')).toHaveCount(0)
  await expect(
    page.getByRole('main').getByRole('region', { name: 'Conversation' }),
  ).toBeVisible()
  /* And the rail is the list alone, as it is for every conversation without a page. */
  await page.getByRole('tab', { name: 'SESSIONS' }).click()
  await expect(page.getByRole('button', { name: 'Back to other sessions' })).toHaveCount(0)
})
