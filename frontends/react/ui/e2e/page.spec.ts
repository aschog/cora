import { expect, test } from '@playwright/test'
import { answered, ask, confirm, fresh, PROSE, rightRail, SEARCH } from './helpers'

/* The one tier that proves a plugin's page is really served and really drawn: the page,
   the API and the plugins folder are all the real ones, and the frame is a document the
   browser fetched from cora rather than a element the shell drew. */
test('a field with a page is worked in it, and answers beside it', async ({
  page,
}) => {
  await fresh(page)
  const strip = page.getByRole('group', { name: 'Answer in' })

  await strip.getByRole('button', { name: 'Plugin' }).click()
  await page.getByRole('button', { name: 'atlas', exact: true }).click()

  const shown = page.locator('iframe[title="atlas"]')
  await expect(shown).toBeVisible()
  await expect(shown.contentFrame().locator('#here')).toHaveText(
    'The atlas is open.',
  )

  /* The conversation is beside it, in the rail, and it is the whole conversation: a
     question goes in and the answer lands where it was asked. */
  const rail = page
    .getByRole('complementary')
    .filter({ has: page.getByRole('tablist') })
  await expect(rail.getByRole('region', { name: 'New conversation' })).toBeVisible()

  await ask(page, PROSE)
  await answered(page)

  await expect(rail.getByText(PROSE)).toHaveCount(2)
  await expect(shown).toBeVisible()
})

test('a field with no page leaves the conversation in the middle', async ({
  page,
}) => {
  await fresh(page)

  await page
    .getByRole('group', { name: 'Answer in' })
    .getByRole('button', { name: 'Plugin' })
    .click()
  await page.getByRole('button', { name: 'kit', exact: true }).click()

  await expect(page.locator('iframe')).toHaveCount(0)
  await expect(
    page.getByRole('main').getByRole('region', { name: 'Conversation' }),
  ).toBeVisible()
})

test('the composer stays in the rail however tall the panel above it grows', async ({
  page,
}) => {
  /* The rail holds two things now, and it has stopped scrolling itself, so the share
     between them is the whole of whether either is usable. A document opened in SOURCE
     is the tallest thing that lands in the panel: left to settle it on its own the
     conversation takes every spare pixel and the panel is a sliver nobody can read,
     while the composer has to stay inside the rail whatever the panel does. */
  /* Narrow enough that the rails are at their minimums, which is where the composer
     has least room of its own. */
  await page.setViewportSize({ width: 800, height: 700 })
  await fresh(page)
  await page
    .getByRole('group', { name: 'Answer in' })
    .getByRole('button', { name: 'Plugin' })
    .click()
  await page.getByRole('button', { name: 'atlas', exact: true }).click()

  /* This field is this spec's own, so what it holds is this spec's to say: the seeded
     note goes, and the long one is then the only thing a search can come back with. */
  await page.getByLabel('Delete note.md').click()
  await confirm(page, 'DELETE DOCUMENT', 'Delete document')
  await expect(page.getByRole('button', { name: 'note.md', exact: true })).toHaveCount(0)

  /* Long, and about what the stub searches for, so it is this that comes back cited. */
  await page.locator('input[type=file]').setInputFiles({
    name: 'long.md',
    mimeType: 'text/markdown',
    buffer: Buffer.from(
      Array.from(
        { length: 80 },
        (_, n) => `Protein, note ${n}. Protein builds muscle, and this note says so again.`,
      ).join('\n\n'),
    ),
  })
  await expect(page.getByRole('status', { name: 'Indexing' })).toHaveText('')

  await ask(page, SEARCH)
  await answered(page)
  await page.getByLabel('Open cited source 1').click()
  await page.keyboard.press('Escape')
  await rightRail(page, 'SOURCE')
  await expect(page.getByRole('heading', { name: 'long.md' })).toBeVisible()

  const rail = page.getByRole('complementary').filter({ has: page.getByRole('tablist') })
  const composer = page.getByRole('button', { name: 'Ask', exact: true })
  const [asked, held] = [await composer.boundingBox(), await rail.boundingBox()]
  expect(asked, 'the composer is drawn').not.toBeNull()
  expect(held, 'the rail is drawn').not.toBeNull()
  expect(
    Math.round(asked!.y + asked!.height),
    'the composer is inside the rail rather than clipped below it',
  ).toBeLessThanOrEqual(Math.round(held!.y + held!.height))
  /* Drawn inside it is not the same as reachable: what is under that point has to be
     the button, and not a panel that grew over it. */
  await composer.click({ trial: true, timeout: 2000 })

  /* And both halves stay usable: a document far taller than the rail is scrolled inside
     the panel rather than taking the rail and leaving the conversation a sliver. */
  const room = await page.evaluate(() => {
    const aside = Array.from(document.querySelectorAll('aside')).find((each) =>
      each.querySelector('[role=tablist]'),
    )!
    const held = (each: Element) => each.getBoundingClientRect().height
    const [, , panel, talk] = Array.from(aside.children)
    return { rail: held(aside), panel: held(panel), talk: held(talk) }
  })
  expect(room.talk / room.rail, 'the conversation keeps a usable share').toBeGreaterThan(0.3)
  expect(room.panel / room.rail, 'the panel keeps a readable share').toBeGreaterThan(0.25)
})
