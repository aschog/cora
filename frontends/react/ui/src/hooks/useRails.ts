import { useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import * as cora from '../api'
import type { Scopes } from '../api'
import { message } from '../fail'

/** What the page shows around the conversation, keyed by what it was asked for. One
 *  read per listing rather than one `Promise.all`: a listing that arrives under the
 *  field it asked about cannot land under another one's name, which is what the guard
 *  used to do by hand — and a field the reader goes back to is drawn from what is
 *  already held.
 *
 *  The banner is still one, and still every one of them: their errors are read
 *  together below. Each keeps its own, so a load that goes through clears its own news
 *  and not the warning another one raised — which is the failure the single banner used
 *  to hide. */
export const rail = {
  /* Under the field it asked about, so the listing for one is never the listing drawn
     for another. The bare name matches every field's, which is what a refresh wants:
     the reader may go back to a field a turn changed while they were elsewhere. */
  documents: (field: string) => ['documents', field] as const,
  everyDocument: ['documents'] as const,
  /* Not a rail, but it is a document's text and a document can go: an effect a turn ran
     may have deleted the one the panel is reading, and nothing else would ever ask
     again. */
  everyPassage: ['passage'] as const,
  memory: ['memory'] as const,
  sessions: ['sessions'] as const,
  scopes: ['scopes'] as const,
  /* What loaded, which is what says whether a field has a plugin behind it and whether
     that plugin is one this deployment can delete. */
  plugins: ['plugins'] as const,
}

export function useRails({
  pin,
  answered,
}: {
  pin: string | null
  answered: string | null
}) {
  const held = useQueryClient()

  /* The fields this deployment offers, and the field a question belonging to none is
     answered in — where an upload naming none lands too. The server's answer rather than
     a constant here: it is one fact, and the page is not where it is decided. */
  const scopes = useQuery({
    queryKey: rail.scopes,
    queryFn: ({ signal }) => cora.scopes(signal),
  })
  const memory = useQuery({
    queryKey: rail.memory,
    queryFn: ({ signal }) => cora.memory(signal),
  })
  const sessions = useQuery({
    queryKey: rail.sessions,
    queryFn: ({ signal }) => cora.sessions(signal),
  })
  const plugins = useQuery({
    queryKey: rail.plugins,
    queryFn: ({ signal }) => cora.plugins(signal),
  })

  const offered: Scopes = scopes.data ?? { available: [], default: '' }
  const fields = offered.available

  /* Where the rail sits when nothing else has spoken. One field loaded is a field
     routing cannot choose against, so every turn runs in it; with more than one, a turn
     belonging to none is answered in the default field. */
  const home = fields.length === 1 ? fields[0] : offered.default

  /** Which field the rail shows and uploads into, in one expression rather than in the
   *  several places that used to write it — a pin outranks the conversation's own turns
   *  because a pinned conversation has one field for good, and a conversation that has
   *  said nothing sits at home. Derived, so nothing can race it: every writer settles one
   *  of the inputs and none settles the answer. */
  const field = pin ?? answered ?? home

  /* Keyed on the field, which is what makes an older listing harmless rather than
     dangerous: it is held under the field it asked about, and the rail reads the entry
     for the field it is drawing. */
  const documents = useQuery({
    queryKey: rail.documents(field),
    queryFn: ({ signal }) => cora.documents(field, signal),
  })

  /** Whether the strip over the conversation is already naming the field, which is the
   *  one case the rail leaves it unsaid. Both halves here rather than one in each
   *  component: a rule split across two is a rule that can say no twice, and a field
   *  named nowhere still takes the uploads. Fewer than two fields draws no strip, so a
   *  pin under one of them is the rail's to say. */
  const namedAbove = pin !== null && fields.length > 1

  /** The first thing that could not be read, in one sentence for all four. A reader is
   *  told the page is incomplete once; which listing it was is the console's. */
  const failed = [documents, memory, sessions, scopes, plugins].find(
    (read) => read.error,
  )
  const trouble = failed?.error ? message(failed.error) : null

  /** Everything the rails hold, read again. Every write goes through this: what a turn,
   *  an upload or a delete changed is on the page because the listing that names it was
   *  asked for again, rather than because the page guessed at what changed. */
  const refresh = useCallback(async () => {
    await Promise.all(
      [
        rail.everyDocument,
        rail.everyPassage,
        rail.memory,
        rail.sessions,
        rail.scopes,
        rail.plugins,
      ].map((queryKey) =>
        held.invalidateQueries({ queryKey }),
      ),
    )
  }, [held])

  return {
    documents: documents.data ?? [],
    facts: memory.data ?? [],
    sessions: sessions.data ?? [],
    plugins: plugins.data ?? [],
    fields,
    field,
    namedAbove,
    trouble,
    refresh,
  }
}
