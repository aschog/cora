import { useMutation, useQueryClient } from '@tanstack/react-query'
import { message } from '../fail'

/** One thing leaving one listing: the request that takes it away, the listing it is
 *  drawn from, and that listing without it. The last is what lets the row go at the
 *  moment the reader says so rather than a round trip later — and what puts it back if
 *  the store refuses. */
export type Removal = {
  send: () => Promise<void>
  from: readonly unknown[]
  /* `never` as the argument so that every listing's own updater is assignable — a
     function is assignable to one taking a narrower argument, and nothing is narrower
     than this. It buys the four call sites their real types and costs this one: nothing
     ties `without` to what `from` actually holds, so pairing a sessions key with a
     `string[]` updater type-checks and throws when it runs. The four are written side by
     side in `App.tsx`, which is the only thing keeping them honest. */
  without: (held: never) => unknown
}

/**
 * A row taken out of the rail that lists it, before the store has been asked. Deleting is
 * the one thing on this page a reader has already confirmed in a card of its own, so
 * waiting for the round trip to redraw the list reads as the click having missed.
 *
 * What was there is kept, and put back where the delete is refused — with the sentence
 * saying why, so a row reappearing is never the only account of what happened.
 *
 * One mutation over all four deletes rather than four: everything but the request and
 * the listing is the same work, and four would be four places for the rollback to be
 * written differently.
 */
export function useRemoving({
  reread,
  setTrouble,
}: {
  /* The rails' own re-read, not the page's — the page's lets go of what it could not do,
     and what it could not do is the sentence this just wrote. A row coming back with no
     account of why is the one outcome worse than the row never going. */
  reread: () => Promise<void>
  setTrouble: (said: string | null) => void
}) {
  const held = useQueryClient()

  return useMutation({
    mutationFn: (going: Removal) => going.send(),
    onMutate: async (going) => {
      /* A read already on the wire would land on top of the row just taken away and put
         it back, for as long as it takes the delete to answer. */
      await held.cancelQueries({ queryKey: going.from })
      const before = held.getQueryData(going.from)
      held.setQueryData(going.from, going.without)
      return { before }
    },
    /* Same as an upload and a turn: what went through clears what the page last could
       not do. Written here rather than left to the re-read, which must not touch it —
       the failure below is the one thing the re-read runs after. */
    onSuccess: () => setTrouble(null),
    onError: (failed, going, was) => {
      held.setQueryData(going.from, was?.before)
      setTrouble(message(failed))
    },
    /* Either way the listing is read again: what went through is confirmed by the store
       rather than by the page's own guess, and what did not is redrawn from it. */
    onSettled: () => reread(),
  })
}
