import { expect, test } from '@playwright/test'
import { fresh } from './helpers'

/* The fitness trainer, in the only tier that can run it: it is the plugin's own
   JavaScript, served by cora at its field's path, and nothing in the Python or the
   shell tiers executes a line of it. Its pure functions are called in the page itself
   rather than lifted out of the file, so what is asserted is what the browser loaded. */

const TRAINER = '/pages/fitness/'

test('the trainer writes a workout in the session grammar', async ({ page }) => {
  await page.goto(TRAINER)

  const written = await page.evaluate(() => {
    type Logged = { n: string; w: number; done: number; r: number; reps: number[] }
    const draw = (window as unknown as { sessionText: (ex: Logged[]) => string })
      .sessionText
    return {
      equal: draw([{ n: 'Snatch', w: 24, done: 3, r: 10, reps: [10, 10, 10] }]),
      uneven: draw([{ n: 'Snatch', w: 24, done: 3, r: 10, reps: [10, 10, 8] }]),
      bodyweight: draw([{ n: 'Push-up', w: 0, done: 2, r: 12, reps: [12, 12] }]),
      /* Two exercises are two headings, separated by a blank line. */
      both: draw([
        { n: 'Snatch', w: 24, done: 1, r: 10, reps: [10] },
        { n: 'Halo', w: 12, done: 2, r: 8, reps: [8, 8] },
      ]),
    }
  })

  expect(written.equal).toBe('# Snatch 24 kg\n3 sets of 10\n')
  expect(written.uneven).toBe('# Snatch 24 kg\nsets of 10 / 10 / 8\n')
  expect(written.bodyweight).toBe('# Push-up bw\n2 sets of 12\n')
  expect(written.both).toBe('# Snatch 24 kg\n1 sets of 10\n\n# Halo 12 kg\n2 sets of 8\n')
})

test('a workout finished in the trainer becomes a document of the fitness field', async ({
  page,
}) => {
  const named = new Date()
  const two = (n: number) => String(n).padStart(2, '0')
  const today = `${named.getFullYear()}-${two(named.getMonth() + 1)}-${two(named.getDate())}.md`

  await page.goto(TRAINER)
  /* One set of the first exercise: the control carries the rep count, and pressing it
     is how a set is logged. Which field it is saved into is the path it was opened
     under — the plugin never writes its own name into the page — and the strip below
     says which one took it. */
  await page.locator('.set').first().click()
  await expect(page.locator('.row.complete, .row .st')).not.toHaveCount(0)

  page.once('dialog', (asked) => asked.accept())
  await page.getByRole('button', { name: /SAVE & FINISH/i }).click()

  await expect(page.locator('#warn')).toContainText('Saved to fitness', {
    timeout: 15_000,
  })

  /* And it is a document of that field, which is the whole point of writing it: the
     shell lists it, and cora can be asked about it. */
  await fresh(page)
  await page
    .getByRole('group', { name: 'Answer in' })
    .getByRole('button', { name: 'Plugin' })
    .click()
  await page.getByRole('button', { name: 'fitness', exact: true }).click()
  await expect(page.getByRole('button', { name: today, exact: true })).toBeVisible()
})

test('a workout cora would not take is said to be lost and kept all the same', async ({
  page,
}) => {
  await page.goto(TRAINER)
  /* cora refusing the upload, which is the one failure the reader cannot act on
     themselves: the workout is theirs and the page is the only thing holding it. */
  await page.route('**/api/documents', (asked) =>
    asked.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'that field takes no documents' }),
    }),
  )
  await page.locator('.set').first().click()

  page.once('dialog', (asked) => asked.accept())
  await page.getByRole('button', { name: /SAVE & FINISH/i }).click()

  await expect(page.locator('#warn')).toContainText('Not saved to cora')
  /* And it is still the reader's: with no clipboard to put it on, the page opens the
     workout where it can be read and copied out by hand. */
  /* The whole value, ended: one exercise was worked, so one heading is written and
     nothing follows it — a workout that handed over the untouched plan fails here. */
  await expect(page.locator('#box')).toHaveValue(/^# [^\n]+\n1 sets of \d+\n$/)
  /* And the page's own history has it, which is what a fresh workout starts beside. */
  const kept = await page.evaluate(() =>
    JSON.parse(globalThis.localStorage.getItem('kb.hist') ?? '[]'),
  )
  expect(kept.length, 'the workout is in the history whatever cora said').toBeGreaterThan(0)
})

test('a workout with nothing logged is not saved, and says so', async ({ page }) => {
  await page.goto(TRAINER)
  let asked = 0
  await page.route('**/api/documents', (call) => {
    asked += 1
    return call.continue()
  })

  /* No set logged: there is nothing to hand over, and the reader has to be told that
     rather than left with a button that did nothing. */
  page.once('dialog', (shown) => shown.accept())
  await page.getByRole('button', { name: /SAVE & FINISH/i }).click()

  await expect(page.locator('#warn')).toContainText(/[Nn]othing logged/)
  expect(asked, 'nothing was uploaded').toBe(0)
})
