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

test('a conversation opened is an entry, so back leaves it', () => {
  /* The other half of the test below, and the one that actually pins `pushState`: without
     it, `showThread` could be a `replaceState` and both would still pass — a router the
     back button walks past is not one. */
  at('#/c/one')
  const depth = globalThis.history.length

  showThread('two')

  expect(globalThis.history.length).toBe(depth + 1)
})

test('a conversation acquiring a name replaces the entry it is standing on', () => {
  /* The reader did not go anywhere: the page they are on became linkable. Pushing would
     leave a back button that returns to the same page under no name — a press that looks
     broken. */
  at('')
  const depth = globalThis.history.length

  showThread('one', { replacing: true })

  expect(globalThis.history.length).toBe(depth)
  expect(threadInUrl()).toBe('one')
})

test('a conversation opened twice is one entry, so back goes back', () => {
  /* Writing the same address again is an entry that goes nowhere: the reader presses
     back, lands on the address they are already at, and nothing happens. */
  at('#/c/old')
  const depth = globalThis.history.length

  showThread('old')

  expect(globalThis.history.length).toBe(depth)
})

test('an address that could mean another path names no conversation', () => {
  /* Whatever is in that slot goes into the path of a request. `..%2Fmemory` decodes to
     `../memory`, which the browser resolves to a different endpoint entirely — and its
     answer would then be drawn as this conversation's turns. The address is the one input
     to this page anybody can write, so it is checked here, once, rather than trusted by
     every reader of it. */
  for (const named of ['..%2Fmemory', '..%2F..%2Fetc', '.', '..', 'a%2Fb', 'a b', 'a.b']) {
    at(`#/c/${named}`)
    expect(threadInUrl()).toBeNull()
  }
})

test('a thread the page minted is read back as one, however it was minted', () => {
  /* `crypto.randomUUID` where the browser has it, and a run of digits where it does not.
     Both are threads this page made, and refusing either would leave a conversation
     unnameable on the browsers that mint it that way. */
  for (const named of [
    'ec2f3426-b2b5-4886-9f40-0d1d9c0f2a11',
    'EC2F3426-B2B5-4886-9F40-0D1D9C0F2A11',
    '84019273640192',
  ]) {
    at(`#/c/${named}`)
    expect(threadInUrl()).toBe(named)
  }
})

test('an address that decodes to nothing names no conversation', () => {
  /* Hand-edited, or truncated by something that passed it on. Reading it as a name would
     have the page ask the store for a thread nobody ever opened. */
  at('#/c/%E0%A4%A')

  expect(threadInUrl()).toBeNull()
})
