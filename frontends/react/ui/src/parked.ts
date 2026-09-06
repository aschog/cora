const PARKED = 'cora.parked'

const keep = (name: string, value: string | null) => {
  try {
    if (value === null) globalThis.sessionStorage?.removeItem(name)
    else globalThis.sessionStorage?.setItem(name, value)
  } catch {
    /* A browser that keeps nothing for this page. The card is then a reload away from
       gone, which is what it was before it could be kept at all. */
  }
}

export const stowed = () => {
  try {
    return globalThis.sessionStorage?.getItem(PARKED) ?? null
  } catch {
    return null
  }
}

/** Which conversation a card was left open in. A reload mints a new thread, and a paused
 *  turn is in no store — so without this the question would be unreachable: SESSIONS
 *  lists only conversations that have answered something. */
export const stow = (thread_id: string) => keep(PARKED, thread_id)

export const forget = () => keep(PARKED, null)

/** Only this conversation's own card is forgotten. A thread parked on its *first*
 *  question is recorded nowhere and listed under no session, so clearing the stow while
 *  reading a different conversation would leave that card reachable by no route at all. */
export const forgetIf = (thread_id: string) => {
  if (stowed() === thread_id) forget()
}
