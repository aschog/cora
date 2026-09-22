import { expect, type Page } from '@playwright/test'

/** The words the stub model answers to. Typing one is how a spec says which way the
 *  turn should go — the model's judgement is not what a browser run is testing. */
export const SEARCH = 'search my notes'
export const CHOOSE = 'choose between them'
export const WRITE = 'write it down'
export const REMEMBER = 'remember this about me'
export const PROSE = 'hello there'

/** A fresh page on a conversation of its own. Every spec starts from one: the store is
 *  shared across the run, and a spec landing in the conversation another left behind
 *  would read its turns as its own. */
export async function fresh(page: Page) {
  await page.goto('/')
  await expect(page.getByLabel('Ask a question')).toBeVisible()
}

export async function ask(page: Page, question: string) {
  await page.getByLabel('Ask a question').fill(question)
  await page.getByRole('button', { name: 'Ask', exact: true }).click()
}

/** The turn is over when the button that sends one is usable again. How long that takes
 *  is the run's to say — `playwright.config.ts` sets it, because a stubbed turn and a
 *  live one are not the same order of wait. */
export async function answered(page: Page) {
  await expect(page.getByRole('button', { name: 'Ask', exact: true })).toBeEnabled()
}

/** The conversation has a name in the address once it has answered, which is what a
 *  reload reopens it by. */
export async function named(page: Page) {
  await expect(page).toHaveURL(/#\/c\//, { timeout: 20_000 })
}

export const TRAINER = '/pages/fitness/'

/** The trainer asks its sheet for the plan on load, and no spec wants that answer: each
 *  is about what the trainer does with whatever plan it has, so the suite never reaches
 *  Google, on a train or otherwise. */
export const noSheet = (page: Page) =>
  page.route('**/docs.google.com/**', (asked) => asked.abort())

/** The strip's picker taken to a field: what fixes a fresh conversation to it. */
export async function pin(page: Page, field: string) {
  await page
    .getByRole('group', { name: 'Answer in' })
    .getByRole('button', { name: 'Plugin' })
    .click()
  await page.getByRole('button', { name: field, exact: true }).click()
}

/** A rail folded by its control, which then says so: it is all that is left of the rail. */
export async function folded(page: Page, named: RegExp) {
  const control = page.getByRole('button', { name: named })
  await control.click()
  await expect(control).toHaveAttribute('aria-pressed', 'false')
  return control
}

/** A fresh page fixed to a field with a page of its own, that page drawn in the middle. */
export async function fixed(page: Page, field: string) {
  await fresh(page)
  await pin(page, field)
  const shown = page.locator(`iframe[title="${field}"]`)
  await expect(shown).toBeVisible()
  return shown
}

export const rightRail = (page: Page, tab: 'STEPS' | 'SOURCE' | 'CONVERSATIONS' | 'MEMORY') =>
  page.getByRole('tab', { name: tab }).click()

export const waiting = (page: Page) =>
  page.getByRole('group', { name: 'Paused · needs your input' })
export const settled = (page: Page) => page.getByRole('group', { name: 'Settled · your answer' })

/** The one confirm dialog all three rails and the picker share. */
export async function confirm(page: Page, head: string, button: string) {
  const asked = page.getByRole('dialog', { name: head })
  await expect(asked).toBeVisible()
  await asked.getByRole('button', { name: button }).click()
}

/** What the browser resolved a custom property to, in the form a computed style reports
 *  it — so a spec names the token it means rather than the hex behind it. */
export const resolved = (page: Page, token: string) =>
  page.evaluate((name) => {
    const probe = document.createElement('div')
    probe.style.color = `var(${name})`
    document.body.appendChild(probe)
    const seen = getComputedStyle(probe).color
    probe.remove()
    return seen
  }, token)

/** A resolved colour as three 0-255 channels and an alpha.
 *
 *  The alpha is kept: a translucent colour reported as `rgba(47, 129, 247, 0.32)` rated
 *  as the opaque blue behind it is a number about a colour nobody sees. Which scale the
 *  channels are on follows the function that reported them rather than their size —
 *  `color(srgb …)` states fractions, `rgb()` states 0-255, and a dark legacy colour
 *  like `rgb(1, 1, 1)` would read as white on a guess about magnitude. Everything that
 *  is not a number is dropped, so a colour space named `display-p3` does not lend its
 *  digit to the red channel.
 */
function channels(colour: string) {
  const [named = '', body = ''] = colour.trim().replace(/\)\s*$/, '').split('(')
  const parts = body.split(/[\s,/]+/).filter((each) => /^\d*\.?\d+%?$/.test(each))
  const scale = named.trim().startsWith('color') ? 255 : 1
  const value = (part: string, full: number) =>
    part.endsWith('%') ? (Number(part.slice(0, -1)) / 100) * full : Number(part) * scale
  const [r = '0', g = '0', b = '0', a = '1'] = parts
  return {
    r: value(r, 255),
    g: value(g, 255),
    b: value(b, 255),
    a: a.endsWith('%') ? Number(a.slice(0, -1)) / 100 : Number(a),
  }
}

const OPAQUE = (colour: string) =>
  `${colour} is translucent, and a colour is only comparable once it has been laid over what it covers`

/** One colour laid over another, as the browser composites it.
 *
 *  Source-over in gamma-encoded sRGB, which is what a browser does for an opaque
 *  backdrop — so the backdrop has to be one.
 */
export function over(front: string, back: string) {
  const [top, ground] = [channels(front), channels(back)]
  if (ground.a !== 1) throw new Error(OPAQUE(back))
  const mixed = (one: number, other: number) =>
    Math.round(one * top.a + other * (1 - top.a))
  return `rgb(${mixed(top.r, ground.r)}, ${mixed(top.g, ground.g)}, ${mixed(top.b, ground.b)})`
}

/** WCAG's ratio between two resolved colours, so a spec can say "visible" as a number.
 *
 *  Both have to be opaque, and one that is not is refused rather than rated: `over` is
 *  what lays a veil on its ground, and a ratio against a ground a colour was never
 *  composited with is a number that means nothing. The palette holds translucent
 *  tokens, so this is reachable by a spec that resolves one.
 *
 *  @throws if either colour carries an alpha.
 */
export function contrast(one: string, other: string) {
  for (const colour of [one, other]) {
    if (channels(colour).a !== 1) throw new Error(OPAQUE(colour))
  }
  const luminance = (colour: string) => {
    const { r: red, g: green, b: blue } = channels(colour)
    const [r, g, b] = [red, green, blue].map((each) => {
      const part = each / 255
      return part <= 0.04045 ? part / 12.92 : ((part + 0.055) / 1.055) ** 2.4
    })
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  }
  const [light, dark] = [luminance(one), luminance(other)].sort((a, b) => b - a)
  return (light + 0.05) / (dark + 0.05)
}
