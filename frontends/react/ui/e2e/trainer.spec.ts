import { expect, test } from '@playwright/test'
import { fresh } from './helpers'

/* The fitness trainer, in the only tier that can run it: it is the plugin's own
   JavaScript, served by cora at its field's path, and nothing in the Python or the
   shell tiers executes a line of it. Its pure functions are called in the page itself
   rather than lifted out of the file, so what is asserted is what the browser loaded. */

const TRAINER = '/pages/fitness/'

/* The page asks its sheet for the plan on load. No spec here wants that answer — one
   asserts what happens without it, and the rest are about what the trainer does with
   whatever plan it has — so the suite never reaches Google, on a train or otherwise. */
test.beforeEach(async ({ page }) => {
  await page.route('**/docs.google.com/**', (asked) => asked.abort())
})

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
  const today = `${named.getFullYear()}-${two(named.getMonth() + 1)}-${two(named.getDate())}`
  // named for its moment: the day, then the time it was saved at
  const saved = new RegExp(`^${today}-\\d{2}-\\d{2}-\\d{2}\\.md$`)

  await page.goto(TRAINER)
  /* One set of the first exercise: the control carries the rep count, and pressing it
     is how a set is logged. Which field it is saved into is the path it was opened
     under — the plugin never writes its own name into the page — and the strip below
     says which one took it. */
  await page.locator('.set').first().click()
  await expect(page.locator('.set.on')).toHaveCount(1)

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
  await expect(page.getByRole('button', { name: saved })).toBeVisible()
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

test("the workout's name is read off the sheet export's filename", async ({ page }) => {
  await page.goto(TRAINER)

  /* The header as Google really sends it: a plain filename that says nothing, and the
     encoded one that names the document and the tab. The tab is what the save is titled
     with. */
  const named = await page.evaluate(() => {
    const read = (window as unknown as { workoutName: (header: string | null) => string })
      .workoutName
    const header =
      'attachment; filename="-.csv"; filename*=UTF-8\'\'' +
      '%D0%9F%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B0%20%D0%9E%D0%B1%D1%83%D1%87' +
      '%D0%B5%D0%BD%D0%B8%D0%B5%20%D1%80%D1%8B%D0%B2%D0%BA%D1%83%20%20-%20' +
      '%D0%A0%D1%8B%D0%B2%D0%BE%D0%BA%20%D0%B3%D0%B8%D1%80%D0%B8.csv'
    return [read(header), read('attachment; filename="-.csv"'), read(null)]
  })

  expect(named).toEqual(['Рывок гири', '', ''])
})

test('the plan is read from the sheet the page is pointed at', async ({ page }) => {
  await page.goto(TRAINER)

  /* The parsing, against the columns the sheet really has — headers in the owner's own
     language, a name column spelled two ways, and a row with no exercise on it. The
     fetch itself is not exercised here: a suite that reached Google would fail on a
     train. */
  const read = await page.evaluate(() => {
    const draw = (
      window as unknown as {
        planFromCSV: (csv: string) => { n: string; s: number; r: number; w: number }[]
      }
    ).planFromCSV
    return draw(
      [
        'Подходы,Повторы,Вес снаряда,Упрожнение,Длинное видео,Короткое видео',
        '4,12,16,Рывок,https://youtu.be/kEBDdhJNhZc,https://youtu.be/7FJh9pIZirs',
        ',,,,,',
        '3,10,24,Толчок,https://youtu.be/XdQ_DaAYI2k,',
      ].join('\n'),
    )
  })

  expect(read.map((each) => [each.n, each.s, each.r, each.w])).toEqual([
    ['Рывок', 4, 12, 16],
    ['Толчок', 3, 10, 24],
  ])
})

test('a sheet that cannot be read leaves the plan the page ships with', async ({
  page,
}) => {
  /* The one failure a lifter in a gym actually has: no signal — which is how every
     spec here runs. The plan already in the page is what they train from, and the strip
     says why it is that one. */
  await page.goto(TRAINER)

  await expect(page.locator('#warn')).toContainText('Sheet unavailable')
  /* And the exercises are the shipped ones, named as the coach speaks. */
  await expect(page.locator('.row .nm').first()).toHaveText(
    'Kettlebell around-the-body pass',
  )
})

test('a sheet that changes under a running workout leaves what was logged', async ({
  page,
}) => {
  await page.goto(TRAINER)
  const clip = [{ l: 'Full', v: 'kEBDdhJNhZc' }]
  const plan = (ids: string[]) =>
    ids.map((id) => ({ id, s: 3, r: 10, w: 16, n: `Exercise ${id}`, vids: clip }))

  /* A plan of this spec's own, so what is asserted is what a changed sheet does to
     progress rather than what the shipped plan happens to be. */
  await page.evaluate(
    (given) => (window as unknown as { adoptPlan: (p: unknown[]) => void }).adoptPlan(given),
    plan(['a', 'b']),
  )
  await page.locator('.set').first().click()
  await expect(page.locator('.set.on')).toHaveCount(1)

  /* The sheet gained an exercise while the lifter was working. What they have already
     done is theirs, and an exercise still in the plan keeps it. */
  await page.evaluate(
    (given) => (window as unknown as { adoptPlan: (p: unknown[]) => void }).adoptPlan(given),
    plan(['c', 'a', 'b']),
  )

  await expect(page.locator('.row', { hasText: 'Exercise c' })).toBeVisible()
  await expect(page.locator('.set.on')).toHaveCount(1)
})

test('a clip plays in the frame rather than sending the lifter to another tab', async ({
  page,
}) => {
  await page.goto(TRAINER)
  const clip = [{ l: 'Full', v: 'kEBDdhJNhZc', t: 42 }]
  await page.evaluate(
    (given) => (window as unknown as { adoptPlan: (p: unknown[]) => void }).adoptPlan(given),
    [{ id: 'a', s: 3, r: 10, w: 16, n: 'Exercise a', vids: clip }],
  )

  await page.locator('.thumb').first().click()

  /* In the frame, not a link out of it: a lifter mid-set is not going to come back from
     another tab, and the clip is the thing they opened the trainer to see. */
  const player = page.locator('.stage iframe')
  await expect(player).toBeVisible()
  const src = await player.getAttribute('src')
  expect(src).toContain('kEBDdhJNhZc')
  expect(src, 'it starts where the plan says it does').toContain('start=42')
  expect(src, 'and asks the host that sets no cookie').toContain('youtube-nocookie.com')
  await expect(page.locator('.stage a[href*="youtube.com/watch"]')).toHaveCount(0)
})
