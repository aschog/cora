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

/** The turn is over when the button that sends one is usable again. */
export async function answered(page: Page) {
  await expect(page.getByRole('button', { name: 'Ask', exact: true })).toBeEnabled({
    timeout: 20_000,
  })
}

/** The conversation has a name in the address once it has answered, which is what a
 *  reload reopens it by. */
export async function named(page: Page) {
  await expect(page).toHaveURL(/#\/c\//, { timeout: 20_000 })
}

export const rightRail = (page: Page, tab: 'STEPS' | 'SOURCE' | 'SESSIONS' | 'MEMORY') =>
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

/** WCAG's ratio between two resolved colours, so a spec can say "visible" as a number. */
export function contrast(one: string, other: string) {
  const luminance = (colour: string) => {
    const [r, g, b] = colour.match(/\d+/g)!.map((each) => {
      const part = Number(each) / 255
      return part <= 0.04045 ? part / 12.92 : ((part + 0.055) / 1.055) ** 2.4
    })
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  }
  const [light, dark] = [luminance(one), luminance(other)].sort((a, b) => b - a)
  return (light + 0.05) / (dark + 0.05)
}
