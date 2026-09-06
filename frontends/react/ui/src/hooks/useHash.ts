import { useSyncExternalStore } from 'react'
import { threadInUrl } from '../route'

const listen = (changed: () => void) => {
  globalThis.addEventListener('hashchange', changed)
  return () => globalThis.removeEventListener('hashchange', changed)
}

const now = () => globalThis.location?.hash ?? ''

/** Which conversation the address names, kept in step with it. The address is not the
 *  page's state — the reader can edit it, and the back button changes it under us — so it
 *  is subscribed to rather than mirrored: a copy in `useState` is a second answer to the
 *  question of which conversation is open, and the two can disagree.
 *
 *  A server rendering this page has no address, which is what the third reader is for. */
export function useRoutedThread(): string | null {
  return threadInUrl(useSyncExternalStore(listen, now, () => ''))
}
