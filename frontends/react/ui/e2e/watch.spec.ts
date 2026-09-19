import { expect, test } from '@playwright/test'
import { answered, ask, fresh, named, PROSE } from './helpers'

/* The watch, as the page meets it: cora keeps one notice per field, whatever is on the
   wrist writes it, and the trainer follows it. The wrist itself is not here — no tier
   runs a watch — so what is driven is the notice, exactly as the extension writes it. */

const TRAINER = '/pages/fitness/'
const NOTICE = '/api/scopes/fitness/notice'

const RUNNING = { workout: 'running' }
const FINISHED = { workout: 'finished' }

/* The plan comes from a sheet the suite never reaches, as in the trainer's own specs. */
test.beforeEach(async ({ page }) => {
  await page.route('**/docs.google.com/**', (asked) => asked.abort())
})

/** The notice as cora answers it, without going near cora — so a spec says what the
 *  wrist wrote and when, and leaves nothing behind for the next one. */
const wrist = (page: import('@playwright/test').Page, said: unknown, at = Date.now()) =>
  page.route(`**${NOTICE}`, (asked) =>
    asked.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(said === null ? { notice: null } : { notice: said, at }),
    }),
  )

test('a workout finished on the wrist is a document of the fitness field', async ({
  page,
}) => {
  const named = new Date()
  const two = (n: number) => String(n).padStart(2, '0')
  const today = `${named.getFullYear()}-${two(named.getMonth() + 1)}-${two(named.getDate())}.md`

  /* Through cora's own notice and not a stub: this is the one spec that proves the
     whole path, from what the extension writes to what the field holds. */
  await page.request.put(NOTICE, { data: RUNNING })
  await page.goto(TRAINER)
  await page.locator('.set').first().click()
  await expect(page.locator('.set.on')).toHaveCount(1)

  /* The lifter taps the control on the wrist. Nothing on this page is touched after
     this line — no dialog is accepted, no button is pressed. */
  await page.request.put(NOTICE, { data: FINISHED })

  await expect(page.locator('#warn')).toContainText('Watch ended the workout', {
    timeout: 20_000,
  })
  await expect(page.getByRole('button', { name: /^saved$/i })).toBeVisible()

  /* And it is a document of that field, which is what the wrist was for. */
  await page.request.put(NOTICE, { data: {} }) // read by nothing: the next spec's slate
  const held = await page.request.get('/api/documents?scope=fitness')
  expect(await held.json()).toContain(today)
})

test('a notice saying a workout runs becomes the workout the page is timing', async ({
  page,
}) => {
  /* The page first and the wrist after, which is the order a lifter has them in: the
     trainer is open on the bench, and the workout starts when they start it. */
  await page.goto(TRAINER)

  await wrist(page, RUNNING)

  /* The counter is the whole of what the lifter asked for: it says the training has
     started and that cora knows it has. */
  await expect(page.locator('#watch')).toHaveText(/^\d+:\d\d$/)
})

test("last workout's notice leaves this workout's start alone", async ({ page }) => {
  await wrist(page, RUNNING, Date.now() - 6 * 60 * 60 * 1000)

  await page.goto(TRAINER)

  await expect(page.locator('#watch')).toHaveText('')
})

test('a field whose notice nobody wrote leaves the trainer as it is', async ({ page }) => {
  await wrist(page, null)

  await page.goto(TRAINER)
  await page.locator('.set').first().click()

  await expect(page.locator('#watch')).toHaveText('')
  await expect(page.locator('.row .st').first()).toContainText('1/')
})

test('a notice route answering nothing at all leaves the trainer working', async ({
  page,
}) => {
  await page.route(`**${NOTICE}`, (asked) => asked.abort())

  await page.goto(TRAINER)
  await page.locator('.set').first().click()

  await expect(page.locator('.row .st').first()).toContainText('1/')
  await expect(page.locator('#watch')).toHaveText('')
})

test('a tap on the wrist saves the workout and starts a fresh one', async ({ page }) => {
  await wrist(page, RUNNING)
  await page.goto(TRAINER)
  await page.locator('.set').first().click()
  let uploads = 0
  await page.route('**/api/documents', (asked) => {
    uploads += 1
    return asked.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ document: 'today.md', chunks: 1, scope: 'fitness' }),
    })
  })

  await wrist(page, FINISHED)

  /* No dialog: the page asks before saving when the button was pressed, and does not
     when the lifter already said they were done by ending on the wrist. */
  await expect(page.locator('#warn')).toContainText('Watch ended the workout')
  await expect(page.locator('.row .st').first()).toContainText('0/')
  expect(uploads, 'the workout went to cora once').toBe(1)

  /* And it stays once, however many times the same notice is read back. */
  await page.waitForTimeout(12_000)
  expect(uploads, 'the same notice is acted on once').toBe(1)
})

test('a tap on the wrist with nothing logged saves nothing and says so', async ({
  page,
}) => {
  await wrist(page, RUNNING)
  await page.goto(TRAINER)
  let uploads = 0
  await page.route('**/api/documents', (asked) => {
    uploads += 1
    return asked.continue()
  })

  await wrist(page, FINISHED)

  await expect(page.locator('#warn')).toContainText(/[Nn]othing logged/)
  expect(uploads, 'nothing was uploaded').toBe(0)
})

test('a workout the wrist ended that cora would not take is said to be lost', async ({
  page,
}) => {
  await wrist(page, RUNNING)
  await page.goto(TRAINER)
  await page.locator('.set').first().click()
  await page.route('**/api/documents', (asked) =>
    asked.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'that field takes no documents' }),
    }),
  )

  await wrist(page, FINISHED)

  await expect(page.locator('#warn')).toContainText('Watch ended the workout')
  await expect(page.locator('#warn')).toContainText('Not saved to cora')
  const kept = await page.evaluate(() =>
    JSON.parse(globalThis.localStorage.getItem('kb.hist') ?? '[]'),
  )
  expect(kept.length, 'the workout is in the history whatever cora said').toBeGreaterThan(0)
})

/* And what the notice does to the screen: a field that speaks puts its own conversation
   on the page, so the trainer is there when the training starts. The shell reads that a
   notice was written and nothing of what it says — the words below are the trainer's,
   and any others would do as well. */

/** A conversation pinned to the field, left where the shell will find it: the pin is
 *  written by a turn, so one is asked. */
async function pinned(page: import('@playwright/test').Page, field: string) {
  await fresh(page)
  await page
    .getByRole('group', { name: 'Answer in' })
    .getByRole('button', { name: 'Plugin' })
    .click()
  await page.getByRole('button', { name: field, exact: true }).click()
  await ask(page, PROSE)
  await answered(page)
  await named(page)
  return page.url()
}

test('a field that speaks puts its own conversation on the screen', async ({ page }) => {
  const conversation = await pinned(page, 'fitness')

  /* The reader has gone somewhere else entirely — another conversation, no field. */
  await fresh(page)
  await ask(page, PROSE)
  await answered(page)
  await named(page)
  expect(page.url()).not.toBe(conversation)

  /* The wrist says a workout has begun. Nothing on this page is touched. */
  await page.request.put(NOTICE, { data: RUNNING })

  await expect(page).toHaveURL(conversation, { timeout: 20_000 })
  /* And the field's page is what the screen is about, which is the point of going. */
  await expect(page.locator('iframe')).toBeVisible()
  await page.request.put(NOTICE, { data: {} })
})
