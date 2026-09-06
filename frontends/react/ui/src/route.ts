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
 *
 * @param replacing Whether this is the page it is already on acquiring a name rather
 *   than the reader going somewhere. A conversation's first answer records it, and it
 *   becomes linkable where it stands — pushing an entry for that would leave a back
 *   button that goes to the same page under no name, which is a press that does nothing.
 */
export function showThread(thread_id: string | null, { replacing = false } = {}) {
  const wanted = thread_id === null ? '' : AT + encodeURIComponent(thread_id)
  if ((globalThis.location?.hash ?? '') === wanted) return
  /* Assignment is the only one of the three that fires `hashchange` by itself, and
     clearing the hash that way leaves a bare `#` in the address. So the other two write
     the whole address and say so — what reads it is a subscription, and a change it is
     not told about is one it goes on contradicting. */
  if (wanted === '' || replacing) {
    const { pathname, search } = globalThis.location
    const address = pathname + search + wanted
    /* Leaving a conversation is the reader going somewhere and keeps its entry, so back
       returns to the one they left. A conversation acquiring a name is not, and replaces
       the entry it is already standing on. */
    if (replacing) globalThis.history?.replaceState(null, '', address)
    else globalThis.history?.pushState(null, '', address)
    globalThis.dispatchEvent(new HashChangeEvent('hashchange'))
    return
  }
  globalThis.location.hash = wanted
}
