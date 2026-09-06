import { useCallback, useEffect, useRef, useState } from 'react'
import * as cora from '../api'
import type { Fact, Session } from '../api'
import { aborted, reportTo } from '../fail'
import { useOneAtATime } from './useOneAtATime'

/** What the page shows around the conversation. One hook rather than one per rail
 *  because it is one load: the four listings arrive together, under one banner, and a
 *  load that goes through clears the last one's. Loading the badge on its own raced that
 *  banner — a page that could not find out which plugin is loaded would say `bare cora`
 *  and then clear the only warning that it was guessing. */
export function useRails({
  pin,
  answered,
  setTrouble,
}: {
  pin: string | null
  answered: string | null
  setTrouble: (said: string | null) => void
}) {
  const [documents, setDocuments] = useState<string[]>([])
  const [facts, setFacts] = useState<Fact[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  /* The fields this deployment offers, and the field a question belonging to none is
     answered in — where an upload naming none lands too. The server's answer rather than
     a constant here: it is one fact, and the page is not where it is decided. */
  const [fields, setFields] = useState<string[]>([])
  const [anyField, setAnyField] = useState('')
  /* Which field the newest documents load asked about, so an older one cannot land. */
  const shown = useRef('')
  const only = useOneAtATime()

  /* Where the rail sits when nothing else has spoken. One field loaded is a field
     routing cannot choose against, so every turn runs in it; with more than one, a turn
     belonging to none is answered in the default field. */
  const home = fields.length === 1 ? fields[0] : anyField

  /** Which field the rail shows and uploads into, in one expression rather than in the
   *  several places that used to write it — a pin outranks the conversation's own turns
   *  because a pinned conversation has one field for good, and a conversation that has
   *  said nothing sits at home. Derived, so nothing can race it: every writer settles one
   *  of the inputs and none settles the answer. */
  const field = pin ?? answered ?? home

  /** Whether the strip over the conversation is already naming the field, which is the
   *  one case the rail leaves it unsaid. Both halves here rather than one in each
   *  component: a rule split across two is a rule that can say no twice, and a field
   *  named nowhere still takes the uploads. Fewer than two fields draws no strip, so a
   *  pin under one of them is the rail's to say. */
  const namedAbove = pin !== null && fields.length > 1

  const refresh = useCallback(() => {
    const asked = field
    shown.current = asked
    const signal = only()
    return Promise.all([
      cora.documents(field, signal),
      cora.memory(signal),
      cora.sessions(signal),
      cora.scopes(signal),
    ])
      .then(([indexed, kept, before, offered]) => {
        /* The listing is per field and this load asked for the field the page was in
             when it started. A load the reader has moved past answers about a field the
             rail is no longer showing: its list must not land under the new one's name,
             and neither must its news — clearing the banner would hide a failure the
             field on the page is still in, and raising one would report a field that is
             no longer drawn. The same race every other read here guards against. */
        if (shown.current !== asked) return
        setDocuments(indexed)
        setFacts(kept)
        setSessions(before)
        setFields(offered.available)
        setAnyField(offered.default)
        setTrouble(null)
      })
      .catch((failed) => {
        /* A refresh the page called off is not trouble, and the guard alone would not
           say so: a second refresh for the *same* field abandons the first without
           moving `shown`, so the abort would land here reading as a failed load. */
        if (aborted(failed)) return
        if (shown.current === asked) reportTo(setTrouble)(failed)
      })
  }, [field, setTrouble, only])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { documents, facts, sessions, fields, field, namedAbove, refresh }
}
