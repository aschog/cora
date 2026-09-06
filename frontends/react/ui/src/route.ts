/* Where a conversation is written in the address, so the one on the page is the one the
   address names. The hash rather than the path: the built page is served as static files
   with no fallback, so `/c/<id>` asks the server for a file it does not have and gets a
   404 — and a route that only works when the page was already open is not a route. */

const AT = '#/c/'

/** What a thread may be made of. Checked rather than assumed: the address is the one
 *  input to this page that anybody can write, and what it holds goes into the path of a
 *  request — `..%2Fmemory` decodes to `../memory`, which the browser resolves to another
 *  endpoint whose answer would then be drawn as this conversation's turns.
 *
 *  Letters, digits and dashes: what `crypto.randomUUID` produces, and what the fallback
 *  for a browser without it produces too. Not the UUID shape itself, because the page
 *  mints one of those and cora is what decides the other. Nothing here can be a `.`, a
 *  `/` or an escape, so nothing read out of the address can mean a different path. */
const THREAD = /^[A-Za-z0-9-]+$/

/** Which conversation the address names, or nothing. */
export function threadInUrl(
  hash: string = globalThis.location?.hash ?? '',
): string | null {
  if (!hash.startsWith(AT)) return null
  let named: string
  try {
    named = decodeURIComponent(hash.slice(AT.length))
  } catch {
    /* A hand-edited address can hold a `%` that decodes to nothing. It names no
       conversation, which is what an address the page did not write usually is. */
    return null
  }
  return THREAD.test(named) ? named : null
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
