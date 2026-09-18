import { expect, test } from '@playwright/test'
import { fresh } from './helpers'

/* Folded, a rail is gone and the control that brings it back is the only thing left of
   it — so that control has to read as a control rather than as the last grey thing on
   an empty edge. It carries the accent either way; which state it is in is the fill of
   the pane inside its outline, not its colour. */

const folded = async (page: import('@playwright/test').Page, named: RegExp) => {
  await fresh(page)
  const control = page.getByRole('button', { name: named })
  await control.click()
  await expect(control).toHaveAttribute('aria-pressed', 'false')
  return control
}

test('the control left behind by a folded rail is drawn in the accent', async ({
  page,
}) => {
  for (const named of [/Documents/, /Plan & memory/]) {
    const control = await folded(page, named)

    /* The token as it resolves on the control itself, so what is asserted is that the
       control reads the accent rather than that somebody typed the same blue twice. */
    const drawn = await control.evaluate((each) => {
      const shown = getComputedStyle(each)
      const probe = document.createElement('span')
      probe.style.color = shown.getPropertyValue('--accent')
      each.appendChild(probe)
      const accent = getComputedStyle(probe).color
      probe.remove()
      return { colour: shown.color, accent }
    })

    expect(drawn.colour, `the ${named} control while its rail is folded`).toBe(drawn.accent)
  }
})

test('the folded left rail keeps the name of the page beside its control', async ({
  page,
}) => {
  const control = await folded(page, /Documents/)
  const rail = page.getByRole('complementary').filter({ has: control })

  await expect(rail.getByText('cora')).toBeVisible()
  /* And nothing else of it: a folded rail is gone, not narrower. */
  await expect(rail.getByText('YOUR DOCUMENTS')).toHaveCount(0)
})
