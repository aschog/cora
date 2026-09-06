import { cleanup, render } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'
import { useOneAtATime } from './useOneAtATime'
import { aborted } from '../fail'

afterEach(cleanup)

/** The hook out of a component, since that is the only place a hook runs. `only` is the
 *  function it hands back, taken out so the test can call it the way a load would. */
function held() {
  const taken: { only: ReturnType<typeof useOneAtATime> | null } = { only: null }
  function Holder({ n }: { n: number }) {
    taken.only = useOneAtATime()
    return <p>{n}</p>
  }
  const drawn = render(<Holder n={1} />)
  return {
    /* Read through the holder rather than captured, so a re-render is read back as the
       function that render produced. */
    now: () => taken.only!,
    again: (n: number) => drawn.rerender(<Holder n={n} />),
    drawn,
  }
}

test('starting another calls off the one before it, and leaves the new one running', () => {
  const { now } = held()

  const first = now()()
  const second = now()()

  expect(first.aborted).toBe(true)
  expect(second.aborted).toBe(false)
})

test('a page that has gone leaves nothing on the wire', () => {
  const { now, drawn } = held()

  const running = now()()
  drawn.unmount()

  expect(running.aborted).toBe(true)
})

test('the function is the same one across renders, so a dependency array can hold it', () => {
  /* A fresh function each render would make every `useCallback` that takes it fresh too,
     and an effect running one of those would run on every render — a loop, not a
     re-fetch. */
  const { now, again } = held()
  const first = now()

  again(2)
  again(3)

  expect(now()).toBe(first)
})

test('what a called-off request throws is read as the page moving on, not as a failure', () => {
  /* The one thing the rails must never do with this: report the reader's own navigation
     to them as a load that failed. */
  const called = new DOMException('The operation was aborted.', 'AbortError')

  expect(aborted(called)).toBe(true)
  expect(aborted(new Error('cora could not be reached.'))).toBe(false)
})
