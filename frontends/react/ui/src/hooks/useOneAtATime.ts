import { useCallback, useEffect, useRef } from 'react'

/**
 * One request at a time, where starting another abandons the one before it. Returns the
 * signal for the new one, having called off whatever it replaced.
 *
 * The page already drops what a superseded read answers — every load is a race with a
 * reader who can move on — but dropping an answer is not the same as not asking for it.
 * This is the half that stops the work: a reader opening four conversations leaves one
 * request on the wire rather than four, and a page that has gone leaves none.
 *
 * Whether the answer *lands* is still the caller's rule, because it is about which
 * conversation the reader is in and not about which request finished.
 */
export function useOneAtATime() {
  const running = useRef<AbortController | null>(null)

  useEffect(
    () => () => {
      running.current?.abort()
    },
    [],
  )

  /* Stable, because callers hold it in dependency arrays: a fresh function each render
     would make every `useCallback` that takes it fresh too, and the effect that runs
     one of those would run on every render. */
  return useCallback(() => {
    running.current?.abort()
    running.current = new AbortController()
    return running.current.signal
  }, [])
}
