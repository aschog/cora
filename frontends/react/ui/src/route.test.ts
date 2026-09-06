import { afterEach, expect, test } from 'vitest'
import { showThread, threadInUrl } from './route'

const at = (hash: string) =>
  globalThis.history.replaceState(null, '', globalThis.location.pathname + hash)

afterEach(() => at(''))

test('a conversation in the address is read back out of it', () => {
  at('#/c/ec2f3426-b2b5-4886-9f40-0d1d9c0f2a11')

  expect(threadInUrl()).toBe('ec2f3426-b2b5-4886-9f40-0d1d9c0f2a11')
})

test('an address naming no conversation names none', () => {
  /* Anything else the hash could be: nothing, a fragment somebody linked to, the route
     with nothing after it. A page that read a conversation out of one of those would ask
     the store for a thread that never existed. */
  for (const hash of ['', '#', '#top', '#/c/', '#/c/a/b', '#/other']) {
    at(hash)
    expect(threadInUrl()).toBeNull()
  }
})

test('the conversation on the page is written into the address', () => {
  showThread('old')

  expect(globalThis.location.hash).toBe('#/c/old')
  expect(threadInUrl()).toBe('old')
})

test('starting over takes the conversation out of the address', () => {
  /* A fresh thread is in no store and has nothing to link to. What is left is the page's
     own address with no fragment — not a bare `#`, which is a link to nowhere that the
     reader would see in the bar. */
  showThread('old')

  showThread(null)

  expect(globalThis.location.hash).toBe('')
  expect(threadInUrl()).toBeNull()
})

test('a conversation opened twice is one entry, so back goes back', () => {
  /* Writing the same address again is an entry that goes nowhere: the reader presses
     back, lands on the address they are already at, and nothing happens. */
  at('#/c/old')
  const depth = globalThis.history.length

  showThread('old')

  expect(globalThis.history.length).toBe(depth)
})

test('a name with characters the address would eat survives the round trip', () => {
  showThread('a thread/with?awkward#parts')

  expect(threadInUrl()).toBe('a thread/with?awkward#parts')
})

test('an address that decodes to nothing names no conversation', () => {
  /* Hand-edited, or truncated by something that passed it on. Reading it as a name would
     have the page ask the store for a thread nobody ever opened. */
  at('#/c/%E0%A4%A')

  expect(threadInUrl()).toBeNull()
})
