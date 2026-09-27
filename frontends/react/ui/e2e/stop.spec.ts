import { expect, test } from '@playwright/test'
import { answered, ask, fresh, PROSE, SLOW } from './helpers'

test('a turn stopped mid-answer gives the conversation back', async ({ page }) => {
  await fresh(page)

  /* Paced prose, so the turn is still running when the control is taken. */
  await ask(page, SLOW)

  /* The same control, now saying what it does. */
  const stopping = page.getByRole('button', { name: 'Stop', exact: true })
  await expect(stopping).toBeVisible()
  await stopping.click()

  /* The question stands under the reader's own sentence, with no answer beside it —
     a stopped turn is recorded nowhere. */
  await expect(page.getByText('You stopped that answer.')).toBeVisible()
  await expect(page.getByText(SLOW)).toBeVisible()

  /* And the conversation takes the next question as it always did. */
  await ask(page, PROSE)
  await answered(page)
  await expect(page.getByText('Ask me about your documents')).toBeVisible()
})
