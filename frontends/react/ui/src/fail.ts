export const message = (failed: unknown) =>
  failed instanceof Error ? failed.message : String(failed)

/** A request the page itself called off, which is not news. The reader moved past it —
 *  telling them "the operation was aborted" would report their own navigation as a
 *  failure, and a request that lost its race says nothing either way. */
export const aborted = (failed: unknown) =>
  failed instanceof DOMException && failed.name === 'AbortError'
