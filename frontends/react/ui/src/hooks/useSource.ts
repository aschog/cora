import { useState } from 'react'
import type { Entry } from '../entry'
import { answering, citedDocuments } from '../entry'

/** A document and the field it was read in. A filename names nothing on its own — one
 *  name can cover a document in each field — so both travel together. */
export type Read = { document: string; scope: string }

/** What the SOURCE panel reads, and which of this conversation's citations point into
 *  it. Kept beside the conversation's turns rather than beside the documents rail: a
 *  passage is only meaningful against the upload an answer actually cited. */
export function useSource(entries: Entry[], field: string) {
  const [read, setRead] = useState<Read | null>(null)

  /** The documents this conversation has actually rested on, in the field the rail
   *  shows. */
  const cited = citedDocuments(entries, field)

  /** The document as this conversation last had it, in the field the rail is showing.
   *  A filename names nothing on its own — one name can cover a document in each field,
   *  and two uploads within one — so the newest citation for the name *here* is what
   *  says which text to read. A field the conversation has cited nothing in names
   *  nothing, which is the honest answer: this field's copy has not been read. */
  const latestFor = (opened: Read) =>
    entries
      .slice()
      .reverse()
      .flatMap((entry) => entry.citations)
      .find(
        (citation) =>
          citation.document === opened.document && citation.scope === opened.scope,
      )

  /** Where a document's text is kept: the field it was ingested into and the upload it
   *  arrived as. Both, because a span is only meaningful against one field's file. */
  const sourceOf = (opened: Read) => {
    const found = latestFor(opened)
    return found?.upload ? { scope: found.scope, upload: found.upload } : null
  }

  /** Two different questions about one document. What is *marked* is what this answer
   *  rested on, or a document cited three turns ago accumulates marks until most of it
   *  is highlighted; what is *openable* is any upload the conversation still names. Both
   *  come from one citation set, because a span measured in one upload's text points at
   *  arbitrary words in another's. */
  const passagesIn = (opened: Read) => {
    const found = latestFor(opened)
    if (!found) return []
    return (answering(entries)?.citations ?? []).filter(
      (citation) =>
        citation.document === opened.document &&
        citation.upload === found.upload &&
        citation.scope === found.scope,
    )
  }

  return { read, setRead, cited, sourceOf, passagesIn }
}
