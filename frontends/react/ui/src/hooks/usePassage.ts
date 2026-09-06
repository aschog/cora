import { useEffect, useState } from 'react'
import * as cora from '../api'

/** One sentence for every way a passage's document cannot be read: deleted, indexed
 *  before cora kept any text, or cited by an index that names no field to look in. All
 *  three arrive as nothing, so guessing between them would sometimes be a lie — and a
 *  reader who clicked `[1]` is owed the same sentence as one who opened the rail. */
export const UNKEPT = 'cora cannot open this document.'

/** The text in hand and which upload it is of, kept as one value. Two states could
 *  disagree — the old document's words under the new one's name — and clearing them at
 *  the top of the effect costs a render, and shows that disagreement in it. */
type Kept = { of: string; text: string | null; trouble: string | null }

const names = (scope: string, upload: string) => `${scope}/${upload}`

/**
 * The kept text of an upload, or why it cannot be read. Both answers live here so that
 * every way of opening a passage gives the same one: a citation from an index written
 * before cora kept any text names no upload, and a reader who clicked `[1]` deserves
 * that sentence as much as a reader who opened the document in the rail.
 */
export function usePassage(source: { scope: string; upload: string } | null) {
  /* Read off the source rather than held, so the effect's dependencies are the two
     values it actually reads and the rule that checks them can say so. */
  const scope = source?.scope
  const upload = source?.upload
  const [kept, setKept] = useState<Kept | null>(null)

  /* Text belonging to another upload is text this source has not loaded yet. Derived, so
     a changed source is blank in the same render it changed in. */
  const current =
    scope !== undefined && upload !== undefined && kept?.of === names(scope, upload)
      ? kept
      : null

  useEffect(() => {
    if (scope === undefined || upload === undefined) return
    let live = true
    cora
      .passage(scope, upload)
      .then(
        (text) => live && setKept({ of: names(scope, upload), text, trouble: null }),
      )
      .catch(
        (failed) =>
          live &&
          setKept({
            of: names(scope, upload),
            text: null,
            trouble: String(failed.message ?? failed),
          }),
      )
    return () => {
      live = false
    }
  }, [scope, upload])

  return {
    text: current?.text ?? null,
    trouble: source ? (current?.trouble ?? null) : UNKEPT,
  }
}
