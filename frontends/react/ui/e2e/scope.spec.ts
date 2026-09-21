import { expect, test } from '@playwright/test'
import { answered, ask, fresh, named, pin, PROSE } from './helpers'

test('a conversation is pinned to a field, and keeps it', async ({ page }) => {
  await fresh(page)
  await pin(page, 'notes')
  const strip = page.getByRole('group', { name: 'Answer in' })

  await expect(strip).toContainText('notes')
  /* The rail follows the pin: an upload lands in the field the conversation is in. */
  await expect(page.getByText('YOUR DOCUMENTS')).toBeVisible()

  await ask(page, PROSE)
  await answered(page)
  await named(page)

  /* Settled by a turn, the pin is the thread's own state — a reload does not undo it,
     and the strip is a name rather than a control. */
  await page.reload()
  await expect(strip).toContainText('notes')
  await expect(strip.getByRole('button', { name: 'Chat' })).toHaveCount(0)
})
