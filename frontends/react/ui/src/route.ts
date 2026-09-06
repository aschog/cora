/* Where a conversation is written in the address, so the one on the page is the one the
   address names. The hash rather than the path: the built page is served as static files
   with no fallback, so `/c/<id>` asks the server for a file it does not have and gets a
   404 — and a route that only works when the page was already open is not a route. */

const AT = '#/c/'

/** Which conversation the address names, or nothing. A thread id is a UUID the page
 *  minted, so anything that could not be one is a hash meaning something else. */
export function threadInUrl(
  hash: string = globalThis.location?.hash ?? '',
): string | null {
  if (!hash.startsWith(AT)) return null
  /* Read as written, before decoding: a `/` in the address is a second segment and this
     route has one, while a `/` in the *name* arrived as `%2F` and is part of it. Decoding
     first cannot tell those apart, and would refuse the name for the address's syntax. */
  const named = hash.slice(AT.length)
  if (named.length === 0 || named.includes('/')) return null
  try {
    return decodeURIComponent(named)
  } catch {
    /* A hand-edited address can hold a `%` that decodes to nothing. It names no
       conversation, which is what an address the page did not write usually is. */
    return null
  }
}

/**
 * The conversation on the page, written into the address — or taken out of it, where the
 * reader has started one that is in no store and has nothing to link to yet.
 *
 * A new entry rather than a replacement, so the back button walks the conversations the
 * reader opened. Written only when it changes: assigning the same hash again is a second
 * entry that goes nowhere, and back would then do nothing the first time it is pressed.
 */
export function showThread(thread_id: string | null) {
  const wanted = thread_id === null ? '' : AT + encodeURIComponent(thread_id)
  if ((globalThis.location?.hash ?? '') === wanted) return
  if (wanted === '') {
    /* Clearing the hash by assignment leaves a bare `#` in the address and fires no
       change. The path is written back without one instead. */
    const { pathname, search } = globalThis.location
    globalThis.history?.pushState(null, '', pathname + search)
    globalThis.dispatchEvent(new HashChangeEvent('hashchange'))
    return
  }
  globalThis.location.hash = wanted
}
